"""Job orchestrator for managing OCR → Matching state machine.

Orchestrates the complete job lifecycle following the state machine defined
in SPEC.md §3.3. Handles state transitions, error recovery, and coordination
between OCR and matching services.
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.petition_crop import PetitionCrop

if TYPE_CHECKING:
    from sqlmodel import Session

    from app.ocr.ocr_manager import OcrClient
    from app.ocr.ocr_service import OCRService

logger = structlog.get_logger(__name__)


class JobOrchestrator:
    """Orchestrates OCR and matching job lifecycle with state management.

    State Machine:
        NOT_STARTED → OCR_STARTED → OCR_COMPLETED → MATCHING →
        MATCHING_COMPLETED

    Error States:
        OCR_FAILED, OCR_TIMEOUT, MATCHING_ERROR
    """

    def __init__(
        self,
        session: "Session",
        ocr_service: "OCRService | None" = None,
        matching_service: Any | None = None,
        storage_base: Path | None = None,
    ) -> None:
        """Initialize job orchestrator.

        Args:
            session: Database session for persistence
            ocr_service: OCR service instance (optional, can be set later)
            matching_service: Matching service instance (optional, can be set later)
            storage_base: Base path for file storage (optional)
        """
        self.session = session
        self.ocr_service = ocr_service
        self.matching_service = matching_service
        self.storage_base = storage_base or Path(tempfile.gettempdir())

    def create_matcher_job(self, campaign_id: UUID) -> MatcherJob:
        """Create a new matcher job with NOT_STARTED status.

        Args:
            campaign_id: Campaign UUID this job belongs to

        Returns:
            Created MatcherJob instance
        """
        job = MatcherJob(campaign_id=campaign_id, current_status=JobStatus.NOT_STARTED)

        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)

        logger.info(
            "Created matcher job",
            job_id=job.id,
            campaign_id=str(campaign_id),
            status=job.current_status,
        )

        return job

    def get_job(self, job_id: int) -> MatcherJob | None:
        """Retrieve job by ID.

        Args:
            job_id: MatcherJob database ID

        Returns:
            MatcherJob instance or None if not found
        """
        return self.session.get(MatcherJob, job_id)

    async def start_ocr_phase(
        self,
        job_id: int,
        crops: list[PetitionCrop],
        ocr_client: "OcrClient",
        campaign_id: str,
        task_id: str,
    ) -> MatcherJob:
        """Start OCR processing phase.

        Transitions job from NOT_STARTED → OCR_STARTED.
        Creates child OCR job and submits batch to OCR provider.

        Args:
            job_id: MatcherJob database ID
            crops: List of petition crops to process
            ocr_client: OCR provider client
            campaign_id: Campaign identifier
            task_id: Task identifier for tracking

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found, invalid state, or OCR service
                not configured
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.current_status != JobStatus.NOT_STARTED:
            raise ValueError(
                f"Cannot start OCR from state {job.current_status}. "
                f"Expected {JobStatus.NOT_STARTED}"
            )

        if not self.ocr_service:
            raise ValueError("OCR service not configured")

        logger.info(
            "Starting OCR phase",
            job_id=job_id,
            crop_count=len(crops),
            campaign_id=campaign_id,
        )

        job.current_status = JobStatus.OCR_PENDING
        job.started_on = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(job)

        ocr_job = await self.ocr_service.create_ocr_job(
            matcher_job_id=job_id,
            crops=crops,
            ocr_client=ocr_client,
            campaign_id=campaign_id,
            task_id=task_id,
        )

        job.current_status = JobStatus.OCR_STARTED
        self.session.commit()
        self.session.refresh(job)

        logger.info(
            "OCR phase started",
            job_id=job_id,
            ocr_job_id=ocr_job.id,
            status=job.current_status,
        )

        return job

    async def check_ocr_completion(
        self,
        job_id: int,
        ocr_job_id: int,
        ocr_client: "OcrClient",
        crops: list[PetitionCrop],
    ) -> MatcherJob:
        """Check OCR job completion and retrieve results.

        Polls OCR provider for status, retrieves results if complete,
        and transitions job to OCR_COMPLETED.

        Args:
            job_id: MatcherJob database ID
            ocr_job_id: OcrJob database ID
            ocr_client: OCR provider client
            crops: List of petition crops (for result mapping)

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found or OCR service not configured
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if not self.ocr_service:
            raise ValueError("OCR service not configured")

        logger.debug(
            "Checking OCR completion",
            job_id=job_id,
            ocr_job_id=ocr_job_id,
        )

        ocr_job = await self.ocr_service.poll_job_status(ocr_job_id, ocr_client)

        if ocr_job.status in [JobStatus.OCR_FAILED, JobStatus.OCR_TIMEOUT]:
            return await self.handle_ocr_failure(
                job_id=job_id,
                error_message=ocr_job.error_data.get(
                    "message", "OCR processing failed"
                ),
            )

        if ocr_job.status == JobStatus.OCR_COMPLETED:
            results = await self.ocr_service.retrieve_and_store_results(
                ocr_job_id=ocr_job_id, ocr_client=ocr_client, crops=crops
            )

            job.current_status = JobStatus.OCR_COMPLETED
            self.session.commit()
            self.session.refresh(job)

            logger.info(
                "OCR phase completed",
                job_id=job_id,
                result_count=len(results),
                status=job.current_status,
            )

        return job

    async def start_matching_phase(self, job_id: int) -> MatcherJob:
        """Start matching phase.

        Transitions job from OCR_COMPLETED → MATCHING.
        Invokes matching service to process OCR results.

        Args:
            job_id: MatcherJob database ID

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found, invalid state, or matching service
                not configured
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.current_status != JobStatus.OCR_COMPLETED:
            raise ValueError(
                f"Cannot start matching from state {job.current_status}. "
                f"Expected {JobStatus.OCR_COMPLETED}"
            )

        if not self.matching_service:
            raise ValueError("Matching service not configured")

        logger.info(
            "Starting matching phase",
            job_id=job_id,
        )

        job.current_status = JobStatus.MATCHING
        self.session.commit()
        self.session.refresh(job)

        try:
            results = await self.matching_service.run_matching(job_id=job_id)

            return await self.complete_matching_phase(job_id=job_id, results=results)

        except Exception as e:
            logger.error(
                "Matching phase failed",
                job_id=job_id,
                error=str(e),
            )

            return await self.handle_matching_error(job_id=job_id, error_message=str(e))

    async def complete_matching_phase(
        self, job_id: int, results: dict[str, Any]
    ) -> MatcherJob:
        """Complete matching phase.

        Transitions job to MATCHING_COMPLETED and stores success data.

        Args:
            job_id: MatcherJob database ID
            results: Matching results dictionary

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.current_status = JobStatus.MATCHING_COMPLETED
        job.ended_on = datetime.now(UTC)
        job.success_data = results

        self.session.commit()
        self.session.refresh(job)

        logger.info(
            "Matching phase completed",
            job_id=job_id,
            status=job.current_status,
            results=results,
        )

        return job

    async def handle_ocr_failure(self, job_id: int, error_message: str) -> MatcherJob:
        """Handle OCR failure.

        Transitions job to OCR_FAILED state with error details.

        Args:
            job_id: MatcherJob database ID
            error_message: Error description

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.current_status = JobStatus.OCR_FAILED
        job.ended_on = datetime.now(UTC)
        job.error_data = {
            "message": error_message,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.session.commit()
        self.session.refresh(job)

        logger.error(
            "OCR phase failed",
            job_id=job_id,
            error=error_message,
            status=job.current_status,
        )

        return job

    async def handle_ocr_timeout(self, job_id: int) -> MatcherJob:
        """Handle OCR timeout.

        Transitions job to OCR_TIMEOUT state.

        Args:
            job_id: MatcherJob database ID

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.current_status = JobStatus.OCR_TIMEOUT
        job.ended_on = datetime.now(UTC)
        job.error_data = {
            "message": "OCR processing timeout",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.session.commit()
        self.session.refresh(job)

        logger.error(
            "OCR phase timed out",
            job_id=job_id,
            status=job.current_status,
        )

        return job

    async def handle_matching_error(
        self, job_id: int, error_message: str
    ) -> MatcherJob:
        """Handle matching error.

        Transitions job to MATCHING_ERROR state with error details.

        Args:
            job_id: MatcherJob database ID
            error_message: Error description

        Returns:
            Updated MatcherJob instance

        Raises:
            ValueError: If job not found
        """
        job = self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.current_status = JobStatus.MATCHING_ERROR
        job.ended_on = datetime.now(UTC)
        job.error_data = {
            "message": error_message,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.session.commit()
        self.session.refresh(job)

        logger.error(
            "Matching phase failed",
            job_id=job_id,
            error=error_message,
            status=job.current_status,
        )

        return job
