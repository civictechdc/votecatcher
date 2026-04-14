"""Background worker for processing OCR and matching jobs.

Simple async worker that polls for NOT_STARTED jobs and processes them
through the OCR → Matching pipeline.

When FEATURE_ENABLE_SIMULATION is enabled (default), uses simulated OCR.
When disabled, uses real LLM API calls via LangChain.
"""

import asyncio
import base64
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from sqlmodel import Session, func, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign
from app.data.database.session import engine
from app.events import JobProgressEvent, JobStatusEvent, MetricsUpdatedEvent, event_bus
from app.matching.match_repository import MatchingStatus, is_terminal_matching_status
from app.ocr.clients.open_ai import OpenAiOcrClient
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_client_factory import resolve_provider_config
from app.ocr.ocr_manager import OcrRequest
from app.services.metrics import MetricsService
from app.settings import get_settings

if TYPE_CHECKING:
    from app.settings import Settings

logger = structlog.get_logger(__name__)

POLL_INTERVAL_SECONDS = 2.0
OCR_SIMULATION_DELAY_SECONDS = 1.0
OCR_REAL_DELAY_SECONDS = 2.0
OCR_RETRY_DELAY_SECONDS = 5.0
OCR_MAX_RETRIES = 3
MATCHING_DELAY_SECONDS = 0.5
BATCH_THRESHOLD = 5


class JobWorker:
    """Background worker for processing MatcherJobs.

    Polls for jobs in NOT_STARTED state and processes them through:
    1. OCR phase (simulated or real)
    2. Matching phase (fuzzy matching against voter DB)

    Attributes:
            settings: Application settings
            running: Flag to control worker loop
    """

    def __init__(self, settings: "Settings | None" = None) -> None:
        self.settings = settings or get_settings()
        self.running = False

    async def start(self) -> None:
        """Start the worker loop."""
        self.running = True
        await self._detect_orphaned_jobs()
        logger.info(
            "Job worker started", simulation_mode=self.settings.feature_simulation
        )

        while self.running:
            try:
                await self._process_pending_jobs()
            except Exception as e:
                logger.error("Worker error", error=str(e))

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def stop(self) -> None:
        """Stop the worker loop."""
        self.running = False
        logger.info("Job worker stopped")

    def _orphan_state_map(self) -> dict[JobStatus, JobStatus]:
        """Map orphan states to their terminal error states."""
        return {
            JobStatus.OCR_STARTED: JobStatus.OCR_FAILED,
            JobStatus.OCR_PENDING: JobStatus.OCR_FAILED,
            JobStatus.OCR_COMPLETED: JobStatus.MATCHING_ERROR,
            JobStatus.MATCHING_PENDING: JobStatus.MATCHING_ERROR,
            JobStatus.MATCHING: JobStatus.MATCHING_ERROR,
        }

    def _terminate_orphans_with_session(self, session: Session) -> list[MatcherJob]:
        """Terminate orphaned jobs by moving them to terminal error states.

        Args:
                session: Database session to use for queries and updates.

        Returns:
                List of terminated orphaned jobs.
        """
        state_map = self._orphan_state_map()
        orphans: list[MatcherJob] = []

        for orphan_state, terminal_state in state_map.items():
            jobs = session.exec(
                select(MatcherJob).where(MatcherJob.current_status == orphan_state)
            ).all()
            for job in jobs:
                orphans.append(job)
                previous_status = job.current_status.value
                job.current_status = terminal_state
                job.ended_on = datetime.now(UTC)
                job.error_data = {
                    "message": f"Orphaned job terminated on restart (was {previous_status})",
                    "previous_status": previous_status,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                child_ocr_jobs = session.exec(
                    select(OcrJob).where(
                        OcrJob.matcher_job_id == job.id,
                        OcrJob.status.not_in(
                            [
                                JobStatus.OCR_COMPLETED,
                                JobStatus.OCR_FAILED,
                                JobStatus.CANCELLED,
                                JobStatus.MATCHING_COMPLETED,
                                JobStatus.MATCHING_ERROR,
                            ]
                        ),
                    )
                ).all()
                for ocr_job in child_ocr_jobs:
                    ocr_job.status = JobStatus.OCR_FAILED

                logger.warning(
                    "Orphaned job terminated",
                    job_id=job.id,
                    previous_status=previous_status,
                    new_status=terminal_state.value,
                    campaign_id=str(job.campaign_id),
                )

        if orphans:
            session.commit()
            logger.info(
                "Orphaned jobs terminated",
                count=len(orphans),
            )

        return orphans

    async def _detect_orphaned_jobs(self) -> list[MatcherJob]:
        """Detect and terminate orphaned jobs stuck in non-terminal states.

        Orphaned jobs are those left in OCR_STARTED, OCR_COMPLETED,
        MATCHING_PENDING, or MATCHING states after a backend restart.

        Returns:
                List of orphaned jobs found
        """
        with Session(engine) as session:
            return self._terminate_orphans_with_session(session)

    async def _process_pending_jobs(self) -> None:
        """Process all pending jobs in NOT_STARTED state."""
        with Session(engine) as session:
            statement = select(MatcherJob).where(
                MatcherJob.current_status == JobStatus.NOT_STARTED
            )
            jobs = session.exec(statement).all()

            for job in jobs:
                try:
                    await self._process_job(session, job)
                except Exception as e:
                    logger.error(
                        "Failed to process job",
                        job_id=job.id,
                        error=str(e),
                    )
                    job.current_status = JobStatus.MATCHING_ERROR
                    job.error_data = {
                        "message": str(e),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    session.commit()

    async def _process_job(self, session: Session, job: MatcherJob) -> None:
        """Process a single job through OCR and matching phases.

        Args:
                session: Database session
                job: MatcherJob to process
        """
        logger.info("Processing job", job_id=job.id)

        previous_status = job.current_status.value if job.current_status else None
        job.current_status = JobStatus.OCR_STARTED
        job.started_on = datetime.now(UTC)
        session.commit()

        await event_bus.publish(
            JobStatusEvent(
                trace_id=str(job.id),
                job_id=job.id,
                campaign_id=str(job.campaign_id),
                status=JobStatus.OCR_STARTED.value,
                previous_status=previous_status,
            )
        )

        job_campaign_normalized = str(job.campaign_id).replace("-", "")

        crops = list(
            session.exec(
                select(PetitionCrop)
                .join(PetitionScan, PetitionCrop.scan_id == PetitionScan.id)
                .where(
                    func.replace(PetitionScan.campaign_id, "-", "")
                    == job_campaign_normalized
                )
            ).all()
        )

        if not crops:
            logger.warning("No crops found for job", job_id=job.id)
            previous_status = job.current_status.value if job.current_status else None
            job.current_status = JobStatus.MATCHING_ERROR
            job.error_data = {
                "message": "No petition crops found for campaign",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            session.commit()

            await event_bus.publish(
                JobStatusEvent(
                    trace_id=str(job.id),
                    job_id=job.id,
                    campaign_id=str(job.campaign_id),
                    status=JobStatus.MATCHING_ERROR.value,
                    previous_status=previous_status,
                )
            )
            return

        ocr_job = OcrJob(
            matcher_job_id=job.id,
            status=JobStatus.OCR_STARTED,
        )
        session.add(ocr_job)
        session.commit()
        session.refresh(ocr_job)

        await self._run_ocr_phase(session, job, ocr_job, crops)
        await self._run_matching_phase(session, job, ocr_job)

        previous_status = job.current_status.value if job.current_status else None
        job.current_status = JobStatus.MATCHING_COMPLETED
        job.ended_on = datetime.now(UTC)
        session.commit()

        await event_bus.publish(
            JobStatusEvent(
                trace_id=str(job.id),
                job_id=job.id,
                campaign_id=str(job.campaign_id),
                status=JobStatus.MATCHING_COMPLETED.value,
                previous_status=previous_status,
            )
        )

        metrics = self._compute_job_metrics(session, job)
        await event_bus.publish(
            MetricsUpdatedEvent(
                trace_id=str(job.id),
                job_id=job.id,
                campaign_id=str(job.campaign_id),
                total_signatures=metrics["total_signatures"],
                processed=metrics["processed"],
                high_confidence=metrics["high_confidence"],
            )
        )

        logger.info(
            "Job completed",
            job_id=job.id,
            status=job.current_status,
        )

    def _compute_job_metrics(self, session: Session, job: MatcherJob) -> dict:
        """Compute metrics for a completed job.

        Args:
                session: Database session
                job: Completed MatcherJob

        Returns:
                Dictionary with total_signatures, processed, high_confidence
        """
        metrics_service = MetricsService(session)
        campaign_metrics = metrics_service.compute_campaign_metrics(job.campaign_id)

        return {
            "total_signatures": campaign_metrics.get("total_signatures", 0),
            "processed": campaign_metrics.get("processed", 0),
            "high_confidence": campaign_metrics.get("high_confidence", 0),
        }

    async def _run_ocr_phase(
        self,
        session: Session,
        job: MatcherJob,
        ocr_job: OcrJob,
        crops: list[PetitionCrop],
    ) -> None:
        """Run OCR phase.

        Uses real LLM API calls when simulation mode is disabled,
        otherwise uses simulated OCR results.

        Args:
                session: Database session
                job: MatcherJob being processed
                ocr_job: OcrJob for this phase
                crops: List of PetitionCrop records to process
        """
        ocr_start_time = time.time()

        logger.info(
            "Starting OCR phase",
            job_id=job.id,
            crop_count=len(crops),
            simulation_mode=self.settings.feature_simulation,
            force_reprocess=job.force_reprocess,
        )

        crop_ids = [c.id for c in crops]
        cached_count = 0
        new_count = 0

        if job.force_reprocess:
            existing_results = session.exec(
                select(OcrResult).where(OcrResult.crop_id.in_(crop_ids))
            ).all()
            if existing_results:
                logger.info(
                    "Force reprocess: deleting existing OCR results",
                    job_id=job.id,
                    deleting_count=len(existing_results),
                )
                for result in existing_results:
                    session.delete(result)
                session.commit()
            crops_to_process = crops
            new_count = len(crops_to_process)
            existing_crop_ids = set()
        else:
            existing_results = session.exec(
                select(OcrResult).where(OcrResult.crop_id.in_(crop_ids))
            ).all()
            existing_crop_ids = {r.crop_id for r in existing_results}

            crops_to_process = [c for c in crops if c.id not in existing_crop_ids]
            cached_count = len(existing_crop_ids)
            new_count = len(crops_to_process)

        if not crops_to_process:
            ocr_duration = time.time() - ocr_start_time
            logger.info(
                "All crops already have OCR results, skipping OCR phase",
                job_id=job.id,
                total_crops=len(crops),
            )
            job.cached_ocr_count = cached_count
            job.new_ocr_count = new_count
            job.ocr_duration_seconds = ocr_duration
            ocr_job.status = JobStatus.OCR_COMPLETED
            job.current_status = JobStatus.OCR_COMPLETED
            session.commit()

            await event_bus.publish(
                JobStatusEvent(
                    trace_id=str(job.id),
                    job_id=job.id,
                    campaign_id=str(job.campaign_id),
                    status=JobStatus.OCR_COMPLETED.value,
                    previous_status=JobStatus.OCR_STARTED.value,
                )
            )
            return

        if existing_crop_ids:
            logger.info(
                "Skipping crops with existing OCR results",
                job_id=job.id,
                skipped_count=len(existing_crop_ids),
                processing_count=len(crops_to_process),
            )

        if self.settings.feature_simulation:
            await self._run_simulated_ocr(session, job, ocr_job, crops_to_process)
        else:
            if (
                len(crops_to_process) >= BATCH_THRESHOLD
                or self.settings.always_batch_ocr
            ):
                logger.info(
                    "Using batch OCR mode",
                    job_id=job.id,
                    crop_count=len(crops_to_process),
                    threshold=BATCH_THRESHOLD,
                    always_batch=self.settings.always_batch_ocr,
                )
                await self._run_batch_ocr(session, job, ocr_job, crops_to_process)
            else:
                await self._run_real_ocr(session, job, ocr_job, crops_to_process)

        ocr_duration = time.time() - ocr_start_time
        job.cached_ocr_count = cached_count
        job.new_ocr_count = new_count
        job.ocr_duration_seconds = ocr_duration
        ocr_job.status = JobStatus.OCR_COMPLETED
        job.current_status = JobStatus.OCR_COMPLETED
        session.commit()

        await event_bus.publish(
            JobStatusEvent(
                trace_id=str(job.id),
                job_id=job.id,
                campaign_id=str(job.campaign_id),
                status=JobStatus.OCR_COMPLETED.value,
                previous_status=JobStatus.OCR_STARTED.value,
            )
        )

        logger.info(
            "OCR phase completed",
            job_id=job.id,
            cached_count=cached_count,
            new_count=new_count,
            ocr_duration_seconds=round(ocr_duration, 2),
        )

    async def _run_simulated_ocr(
        self,
        session: Session,
        job: MatcherJob,
        ocr_job: OcrJob,
        crops: list[PetitionCrop],
    ) -> None:
        """Run simulated OCR (for demo/testing).

        Args:
                session: Database session
                job: MatcherJob being processed
                ocr_job: OcrJob for this phase
                crops: List of PetitionCrop records to process
        """
        for i, crop in enumerate(crops):
            await asyncio.sleep(OCR_SIMULATION_DELAY_SECONDS)

            extracted_text = self._simulate_ocr_result(i)

            ocr_result = OcrResult(
                crop_id=crop.id,
                ocr_job_id=ocr_job.id,
                extracted_text=extracted_text,
                confidence_score=random.uniform(0.75, 0.95),  # nosec B311
            )
            session.add(ocr_result)

            progress = (i + 1) / len(crops) * 100
            logger.info(
                "OCR progress (simulated)",
                job_id=job.id,
                crop_index=i + 1,
                total=len(crops),
                progress=f"{progress:.0f}%",
            )

    async def _run_real_ocr(
        self,
        session: Session,
        job: MatcherJob,
        ocr_job: OcrJob,
        crops: list[PetitionCrop],
    ) -> None:
        """Run real OCR using LLM API with retry logic for rate limiting.

        Commits after each crop to maintain clean session state.

        Args:
                session: Database session
                job: MatcherJob being processed
                ocr_job: OcrJob for this phase
                crops: List of PetitionCrop records to process
        """
        from app.ocr.ocr_client_factory import extract_from_encoding_async

        config = resolve_provider_config(session=session)

        for i, crop in enumerate(crops):
            existing_result = session.exec(
                select(OcrResult).where(OcrResult.crop_id == crop.id)
            ).first()
            if existing_result:
                logger.debug(
                    "OcrResult already exists for crop, skipping",
                    crop_id=crop.id,
                    result_id=existing_result.id,
                )
                continue

            try:
                crop_path = Path(crop.stored_path)
                if not crop_path.exists():
                    logger.warning(
                        "Crop file not found, skipping",
                        crop_id=crop.id,
                        path=crop.stored_path,
                    )
                    continue

                img_bytes = crop_path.read_bytes()
                base64_image = base64.b64encode(img_bytes).decode("utf-8")

                ocr_entries = None
                last_error = None
                for attempt in range(OCR_MAX_RETRIES):
                    try:
                        await asyncio.sleep(OCR_REAL_DELAY_SECONDS * (attempt + 1))
                        ocr_entries = await extract_from_encoding_async(
                            base64_image, config=config
                        )
                        break
                    except Exception as retry_error:
                        last_error = retry_error
                        if (
                            "429" in str(retry_error)
                            or "rate_limit" in str(retry_error).lower()
                        ):
                            wait_time = OCR_RETRY_DELAY_SECONDS * (2**attempt)
                            logger.warning(
                                "Rate limited, waiting before retry",
                                crop_id=crop.id,
                                attempt=attempt + 1,
                                wait_seconds=wait_time,
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            raise

                if ocr_entries is None:
                    raise last_error

                for entry_idx, entry in enumerate(ocr_entries):
                    extracted_text = {
                        "name": entry.get("Name", ""),
                        "address": entry.get("Address", ""),
                    }

                    ocr_result = OcrResult(
                        crop_id=crop.id,
                        ocr_job_id=ocr_job.id,
                        ocr_index=entry_idx,
                        extracted_text=extracted_text,
                        confidence_score=0.85,
                    )
                    session.add(ocr_result)

                session.commit()
                logger.info(
                    "OCR progress (real)",
                    job_id=job.id,
                    crop_index=i + 1,
                    total=len(crops),
                    entries_found=len(ocr_entries),
                )

            except Exception as e:
                session.rollback()
                logger.error(
                    "OCR failed for crop, rolled back session",
                    crop_id=crop.id,
                    error=str(e),
                )
                existing = session.exec(
                    select(OcrResult).where(OcrResult.crop_id == crop.id)
                ).first()
                if not existing:
                    session.add(
                        OcrResult(
                            crop_id=crop.id,
                            ocr_job_id=ocr_job.id,
                            extracted_text={"error": str(e)},
                            confidence_score=0.0,
                        )
                    )
                    session.commit()

    async def _run_batch_ocr(
        self,
        session: Session,
        job: MatcherJob,
        ocr_job: OcrJob,
        crops: list[PetitionCrop],
    ) -> None:
        """Run batch OCR using OpenAI Batch API for large payloads.

        Batch jobs take 5-15 minutes but avoid rate limits.
        Falls back to sequential processing if batch fails.

        Args:
                session: Database session
                job: MatcherJob being processed
                ocr_job: OcrJob for this phase
                crops: List of PetitionCrop records to process
        """
        logger.info(
            "Starting batch OCR",
            job_id=job.id,
            crop_count=len(crops),
        )

        try:
            config = resolve_provider_config(session=session)

            encoded_pages: list[EncodedPetitionPage] = []
            for idx, crop in enumerate(crops):
                crop_path = Path(crop.stored_path)
                if not crop_path.exists():
                    logger.warning(
                        "Crop file not found, skipping",
                        crop_id=crop.id,
                        path=crop.stored_path,
                    )
                    continue

                img_bytes = crop_path.read_bytes()
                base64_image = base64.b64encode(img_bytes).decode("utf-8")

                encoded_pages.append(
                    EncodedPetitionPage(
                        page_num=idx,
                        encoded_page=base64_image,
                        image_path=crop.stored_path,
                        petition_file_name=crop.stored_path,
                        petition_file_page_total=len(crops),
                        scan_id=str(crop.scan_id),
                    )
                )

            if not encoded_pages:
                logger.warning("No valid crops to process in batch", job_id=job.id)
                return

            batch_dir = Path("batch_temp") / f"job_{job.id}"
            batch_dir.mkdir(parents=True, exist_ok=True)

            client = OpenAiOcrClient(config, batch_dir)

            request_data = OcrRequest(
                campaign_id=str(job.campaign_id),
                provider_id=config.provider,
                task_id=str(ocr_job.id),
                encoded_pages=encoded_pages,
            )

            batch_status = await client.create_batch_job(request_data)
            logger.info(
                "Batch job created",
                job_id=job.id,
                batch_job_id=batch_status.ocr_job_id,
                status=batch_status.task_status,
            )

            poll_interval = 60
            max_wait_minutes = 30
            elapsed = 0

            ocr_status = batch_status
            while elapsed < max_wait_minutes * 60:
                if is_terminal_matching_status(ocr_status.task_status):
                    break

                logger.info(
                    "Batch job in progress",
                    job_id=job.id,
                    batch_job_id=ocr_status.ocr_job_id,
                    status=ocr_status.task_status,
                    elapsed_seconds=elapsed,
                )

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                ocr_status = await client.fetch_job_status(ocr_status.ocr_job_id)

            if ocr_status.task_status != MatchingStatus.OCR_COMPLETED:
                raise RuntimeError(
                    f"Batch job did not complete: {ocr_status.task_status}, "
                    f"error: {ocr_status.failure_message}"
                )

            crop_entry_counts: dict[int, int] = {}
            async for result in client.get_ocr_results(batch_status.ocr_job_id):
                crop_idx = result.page_num
                crop_id = crops[crop_idx].id

                entry_idx = crop_entry_counts.get(crop_id, 0)
                crop_entry_counts[crop_id] = entry_idx + 1

                field_map = {
                    part["field_name"]: part["value"] for part in result.result_parts
                }

                ocr_result = OcrResult(
                    crop_id=crop_id,
                    ocr_job_id=ocr_job.id,
                    ocr_index=entry_idx,
                    extracted_text={
                        "name": field_map.get("Name", ""),
                        "address": field_map.get("Address", ""),
                    },
                    confidence_score=0.85,
                )
                session.add(ocr_result)

            session.commit()
            logger.info(
                "Batch OCR completed",
                job_id=job.id,
                batch_job_id=batch_status.ocr_job_id,
            )

        except Exception as e:
            logger.error(
                "Batch OCR failed, falling back to sequential",
                job_id=job.id,
                error=str(e),
            )
            session.rollback()
            await self._run_real_ocr(session, job, ocr_job, crops)

    def _get_provider_api_key(self, provider: str) -> str | None:
        """Get API key for provider from config or environment.

        Args:
                provider: Provider name (e.g., 'openai')

        Returns:
                API key if configured, None otherwise
        """
        from app.data.database.session import engine

        with Session(engine) as config_session:
            from app.data.database.model.llm_provider_config import LlmProviderConfig

            config = config_session.exec(
                select(LlmProviderConfig).where(LlmProviderConfig.provider == provider)
            ).first()

            if config and config.api_key:
                return config.api_key

        import os

        env_key = os.environ.get(f"{provider.upper()}_API_KEY")
        if env_key:
            return env_key

        return None

    async def _run_matching_phase(
        self,
        session: Session,
        job: MatcherJob,
        ocr_job: OcrJob,
    ) -> None:
        """Run matching phase against voter database.

        For each OCR result, finds top 5 matching voters using fuzzy matching.

        Args:
                session: Database session
                job: MatcherJob being processed
                ocr_job: OcrJob with completed OCR results
        """
        matching_start_time = time.time()

        logger.info("Starting matching phase", job_id=job.id)

        previous_status = job.current_status.value if job.current_status else None
        job.current_status = JobStatus.MATCHING
        session.commit()

        await event_bus.publish(
            JobStatusEvent(
                trace_id=str(job.id),
                job_id=job.id,
                campaign_id=str(job.campaign_id),
                status=JobStatus.MATCHING.value,
                previous_status=previous_status,
            )
        )

        ocr_results = session.exec(
            select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id)
        ).all()

        campaign = session.get(Campaign, job.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {job.campaign_id}")

        from app.dependencies import get_field_spec_service
        from app.matching.matching_service import MatchingService

        matching_service = MatchingService(session=session)

        spec_service = next(get_field_spec_service())
        region_key = "DC"
        if hasattr(campaign, "region") and campaign.region:
            region_key = campaign.region.region_key
        spec = spec_service.get_spec_by_key(region_key)

        total_ocr_results = len(ocr_results)
        for idx, ocr_result in enumerate(ocr_results, start=1):
            await asyncio.sleep(MATCHING_DELAY_SECONDS)

            matches = matching_service.match_ocr_result_with_spec(
                spec=spec,
                ocr_text=ocr_result.extracted_text,
                region_id=campaign.region_id,
                top_n=5,
            )

            for rank, match in enumerate(matches, start=1):
                match_result = MatchResult(
                    ocr_result_id=ocr_result.id,
                    matcher_job_id=job.id,
                    rank=rank,
                    voter_id=match["voter_id"],
                    similarity_score=match["similarity_score"],
                    confidence_level=match["confidence_level"],
                    field_scores=match["field_scores"],
                )
                session.add(match_result)

            if idx % max(1, total_ocr_results // 10) == 0:
                await event_bus.publish(
                    JobProgressEvent(
                        trace_id=str(job.id),
                        job_id=job.id,
                        campaign_id=str(job.campaign_id),
                        processed=idx,
                        total=total_ocr_results,
                        percentage=(idx / total_ocr_results) * 100,
                    )
                )

        matching_duration = time.time() - matching_start_time
        job.matching_duration_seconds = matching_duration
        session.commit()

        logger.info(
            "Matching phase completed",
            job_id=job.id,
            ocr_results_processed=len(ocr_results),
            matching_duration_seconds=round(matching_duration, 2),
        )

    def _simulate_ocr_result(self, index: int) -> dict[str, str]:
        """Generate simulated OCR result.

        Args:
                index: Crop index for generating varied results

        Returns:
                Dictionary with simulated extracted text
        """
        sample_names = [
            "John Smith",
            "Maria Garcia",
            "Robert Johnson",
            "Sarah Williams",
            "David Brown",
            "Jennifer Davis",
            "Michael Miller",
            "Lisa Wilson",
            "James Taylor",
            "Emily Anderson",
        ]
        sample_addresses = [
            "123 Main St NW",
            "456 Oak Ave NE",
            "789 Pine St SW",
            "321 Elm Blvd SE",
            "654 Cedar Ln NW",
            "987 Maple Dr NE",
            "147 Birch Ave NW",
            "258 Walnut Way SE",
            "369 Cherry Ct NW",
            "741 Spruce Pl NE",
        ]

        name_idx = index % len(sample_names)
        address_idx = index % len(sample_addresses)

        return {
            "name": sample_names[name_idx],
            "address": sample_addresses[address_idx],
        }


_worker: JobWorker | None = None


async def start_worker() -> None:
    """Start the global job worker."""
    global _worker
    if _worker is None:
        _worker = JobWorker()
        await _worker.start()


async def stop_worker() -> None:
    """Stop the global job worker."""
    global _worker
    if _worker:
        await _worker.stop()
        _worker = None
