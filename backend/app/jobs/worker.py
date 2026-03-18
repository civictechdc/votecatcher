"""Background worker for processing OCR and matching jobs.

Simple async worker that polls for NOT_STARTED jobs and processes them
through the OCR → Matching pipeline.

When FEATURE_ENABLE_SIMULATION is enabled (default), uses simulated OCR.
When disabled, uses real LLM API calls via LangChain.
"""

import asyncio
import base64
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from sqlmodel import Session, func, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign
from app.data.database.session import engine
from app.settings.env_settings import get_settings

if TYPE_CHECKING:
	from app.settings.env_settings import AppSettings

logger = structlog.get_logger(__name__)

POLL_INTERVAL_SECONDS = 2.0
OCR_SIMULATION_DELAY_SECONDS = 1.0
OCR_REAL_DELAY_SECONDS = 2.0
OCR_RETRY_DELAY_SECONDS = 5.0
OCR_MAX_RETRIES = 3
MATCHING_DELAY_SECONDS = 0.5
BATCH_THRESHOLD = 10


class JobWorker:
	"""Background worker for processing MatcherJobs.

	Polls for jobs in NOT_STARTED state and processes them through:
	1. OCR phase (simulated or real)
	2. Matching phase (fuzzy matching against voter DB)

	Attributes:
		settings: Application settings
		running: Flag to control worker loop
	"""

	def __init__(self, settings: "AppSettings | None" = None) -> None:
		self.settings = settings or get_settings()
		self.running = False

	async def start(self) -> None:
		"""Start the worker loop."""
		self.running = True
		await self._detect_orphaned_jobs()
		logger.info(
			"Job worker started", simulation_mode=self.settings.enable_simulation
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

	async def _detect_orphaned_jobs(self) -> list[MatcherJob]:
		"""Detect jobs stuck in non-terminal states (orphaned by restart).

		Orphaned jobs are those left in OCR_STARTED, OCR_COMPLETED,
		MATCHING_PENDING, or MATCHING states after a backend restart.

		Returns:
			List of orphaned jobs found
		"""
		orphan_states = [
			JobStatus.OCR_STARTED,
			JobStatus.OCR_COMPLETED,
			JobStatus.MATCHING_PENDING,
			JobStatus.MATCHING,
		]
		orphans = []

		with Session(engine) as session:
			for status in orphan_states:
				jobs = session.exec(
					select(MatcherJob).where(MatcherJob.current_status == status)
				).all()
				for job in jobs:
					orphans.append(job)
					logger.warning(
						"Orphaned job detected",
						job_id=job.id,
						status=status.value,
						campaign_id=str(job.campaign_id),
						updated_on=job.updated_on.isoformat()
						if job.updated_on
						else None,
					)

		if orphans:
			logger.info(
				"Orphaned jobs summary",
				count=len(orphans),
				note="These jobs can be cancelled or resumed from the UI",
			)

		return orphans

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

		job.current_status = JobStatus.OCR_STARTED
		job.started_on = datetime.now(UTC)
		session.commit()

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
			job.current_status = JobStatus.MATCHING_ERROR
			job.error_data = {
				"message": "No petition crops found for campaign",
				"timestamp": datetime.now(UTC).isoformat(),
			}
			session.commit()
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

		job.current_status = JobStatus.MATCHING_COMPLETED
		job.ended_on = datetime.now(UTC)
		session.commit()

		logger.info(
			"Job completed",
			job_id=job.id,
			status=job.current_status,
		)

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
		logger.info(
			"Starting OCR phase",
			job_id=job.id,
			crop_count=len(crops),
			simulation_mode=self.settings.enable_simulation,
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
		else:
			existing_results = session.exec(
				select(OcrResult).where(OcrResult.crop_id.in_(crop_ids))
			).all()
			existing_crop_ids = {r.crop_id for r in existing_results}

			crops_to_process = [c for c in crops if c.id not in existing_crop_ids]
			cached_count = len(existing_crop_ids)
			new_count = len(crops_to_process)

			if not crops_to_process:
				logger.info(
					"All crops already have OCR results, skipping OCR phase",
					job_id=job.id,
					total_crops=len(crops),
				)
				job.cached_ocr_count = cached_count
				job.new_ocr_count = new_count
				ocr_job.status = JobStatus.OCR_COMPLETED
				job.current_status = JobStatus.OCR_COMPLETED
				session.commit()
				return

			if existing_crop_ids:
				logger.info(
					"Skipping crops with existing OCR results",
					job_id=job.id,
					skipped_count=len(existing_crop_ids),
					processing_count=len(crops_to_process),
				)

		if self.settings.enable_simulation:
			await self._run_simulated_ocr(session, job, ocr_job, crops_to_process)
		else:
			if len(crops_to_process) >= BATCH_THRESHOLD:
				logger.info(
					"Using batch OCR mode",
					job_id=job.id,
					crop_count=len(crops_to_process),
					threshold=BATCH_THRESHOLD,
				)
				await self._run_batch_ocr(session, job, ocr_job, crops_to_process)
			else:
				await self._run_real_ocr(session, job, ocr_job, crops_to_process)

		job.cached_ocr_count = cached_count
		job.new_ocr_count = new_count
		ocr_job.status = JobStatus.OCR_COMPLETED
		job.current_status = JobStatus.OCR_COMPLETED
		session.commit()

		logger.info(
			"OCR phase completed",
			job_id=job.id,
			cached_count=cached_count,
			new_count=new_count,
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
						ocr_entries = await extract_from_encoding_async(base64_image)
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
		from app.ocr.batching.batch_ocr_client import JobStatus
		from app.ocr.batching.openai_ocr_batch import OpenAiBatchClient
		from app.ocr.batching.request_types import BatchRequestPayload, Payload
		from app.settings.settings_repo import OpenAiConfig

		logger.info(
			"Starting batch OCR",
			job_id=job.id,
			crop_count=len(crops),
		)

		try:
			api_key = self._get_provider_api_key("openai")
			if not api_key:
				raise ValueError("OpenAI API key not configured")

			config = OpenAiConfig(
				api_key=api_key,
				model=job.provider_model or "gpt-4o",
			)

			batch_payloads = []
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

				batch_payloads.append(
					Payload(
						role="user",
						messages=[
							{
								"type": "image_url",
								"image_url": {
									"url": f"data:image/jpeg;base64,{base64_image}"
								},
							}
						],
						page=idx,
						file_name=crop.stored_path,
					)
				)

			if not batch_payloads:
				logger.warning("No valid crops to process in batch", job_id=job.id)
				return

			class NoOpResultRepository:
				async def save_results(self, campaign_id, results):
					return results

				async def fetch_results(self, campaign_id):
					return []

			result_store = NoOpResultRepository()
			client = OpenAiBatchClient(config, result_store)

			request_data = BatchRequestPayload(
				campaign_id=str(job.campaign_id),
				batch_payloads=batch_payloads,
			)

			batch_dir = Path("batch_temp") / f"job_{job.id}"
			batch_dir.mkdir(parents=True, exist_ok=True)

			batch_status = await client.create_batch_job(request_data, batch_dir)
			logger.info(
				"Batch job created",
				job_id=job.id,
				batch_job_id=batch_status.job_id,
				status=batch_status.status,
			)

			poll_interval = 60
			max_wait_minutes = 30
			elapsed = 0

			while elapsed < max_wait_minutes * 60:
				batch_status = await client.get_job_status(batch_status.job_id)

				if batch_status.status in [
					JobStatus.COMPLETED,
					JobStatus.FAILED,
					JobStatus.CANCELLED,
					JobStatus.EXPIRED,
				]:
					break

				logger.info(
					"Batch job in progress",
					job_id=job.id,
					batch_job_id=batch_status.job_id,
					status=batch_status.status,
					elapsed_seconds=elapsed,
				)

				await asyncio.sleep(poll_interval)
				elapsed += poll_interval

			if batch_status.status != JobStatus.COMPLETED:
				raise RuntimeError(
					f"Batch job did not complete: {batch_status.status}, "
					f"error: {batch_status.error}"
				)

			crop_entry_counts: dict[int, int] = {}
			async for result_item in client.get_ocr_results(batch_status.job_id):
				entry = result_item.ocr_entry
				crop_idx = result_item.row_num
				crop_id = crops[crop_idx].id

				entry_idx = crop_entry_counts.get(crop_id, 0)
				crop_entry_counts[crop_id] = entry_idx + 1

				ocr_result = OcrResult(
					crop_id=crop_id,
					ocr_job_id=ocr_job.id,
					ocr_index=entry_idx,
					extracted_text={
						"name": entry.Name,
						"address": entry.Address,
					},
					confidence_score=0.85,
				)
				session.add(ocr_result)

			session.commit()
			logger.info(
				"Batch OCR completed",
				job_id=job.id,
				batch_job_id=batch_status.job_id,
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
		logger.info("Starting matching phase", job_id=job.id)

		job.current_status = JobStatus.MATCHING
		session.commit()

		ocr_results = session.exec(
			select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id)
		).all()

		campaign = session.get(Campaign, job.campaign_id)
		if not campaign:
			raise ValueError(f"Campaign not found: {job.campaign_id}")

		voters = session.exec(
			select(RegisteredVoter).where(
				RegisteredVoter.region_id == campaign.region_id
			)
		).all()

		if not voters:
			logger.warning(
				"No voters found for region",
				job_id=job.id,
				region_id=str(campaign.region_id),
			)
			return

		for ocr_result in ocr_results:
			await asyncio.sleep(MATCHING_DELAY_SECONDS)

			matches = self._find_top_matches(ocr_result, voters, top_n=5)

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

		session.commit()

		logger.info(
			"Matching phase completed",
			job_id=job.id,
			ocr_results_processed=len(ocr_results),
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

	def _find_top_matches(
		self,
		ocr_result: OcrResult,
		voters: list[RegisteredVoter],
		top_n: int = 5,
	) -> list[dict]:
		"""Find top matching voters for an OCR result.

		Uses simple string similarity for MVP. Can be enhanced with
		RapidFuzz for production.

		Args:
			ocr_result: OCR result to match
			voters: List of registered voters to match against
			top_n: Number of top matches to return

		Returns:
			List of match dictionaries with voter_id, similarity_score,
			confidence_level, and field_scores
		"""
		from rapidfuzz import fuzz

		ocr_name = str(ocr_result.extracted_text.get("name", ""))
		ocr_address = str(ocr_result.extracted_text.get("address", ""))

		matches = []
		for voter in voters:
			name_data = voter.name_data or {}
			address_data = voter.address_data or {}

			voter_name = " ".join(
				[
					name_data.get("first_name") or "",
					name_data.get("last_name") or "",
				]
			).strip()

			voter_address = " ".join(
				[
					address_data.get("street") or "",
					address_data.get("city") or "",
					address_data.get("state") or "",
					address_data.get("zip") or "",
				]
			).strip()

			name_score = fuzz.ratio(ocr_name, voter_name) / 100.0
			address_score = fuzz.ratio(ocr_address, voter_address) / 100.0

			if name_score + address_score > 0:
				similarity = (2 * name_score * address_score) / (
					name_score + address_score
				)
			else:
				similarity = 0.0

			if similarity >= 0.85:
				confidence = ConfidenceLevel.HIGH
			elif similarity >= 0.60:
				confidence = ConfidenceLevel.MEDIUM
			else:
				confidence = ConfidenceLevel.LOW

			matches.append(
				{
					"voter_id": voter.id,
					"similarity_score": similarity,
					"confidence_level": confidence,
					"field_scores": {
						"name": name_score,
						"address": address_score,
					},
				}
			)

		matches.sort(key=lambda x: x["similarity_score"], reverse=True)
		return matches[:top_n]


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
