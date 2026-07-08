"""Job query service for handling job CRUD and status operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.routers.job_router import JobListResponse, JobResponse

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload

_ORPHAN_STATES = frozenset(
    {
        JobStatus.OCR_STARTED,
        JobStatus.OCR_COMPLETED,
        JobStatus.MATCHING_PENDING,
        JobStatus.MATCHING,
    }
)

_CANCELABLE_STATES = frozenset(
    [
        JobStatus.NOT_STARTED,
        JobStatus.OCR_PENDING,
        JobStatus.OCR_STARTED,
        JobStatus.OCR_COMPLETED,
        JobStatus.MATCHING_PENDING,
        JobStatus.MATCHING,
    ]
)

_RETRYABLE_STATES = frozenset(
    {
        JobStatus.OCR_FAILED,
        JobStatus.OCR_TIMEOUT,
        JobStatus.MATCHING_ERROR,
        JobStatus.OCR_STARTED,
        JobStatus.OCR_COMPLETED,
        JobStatus.MATCHING_PENDING,
        JobStatus.MATCHING,
    }
)

_TERMINAL_OCR_STATES = frozenset(
    {
        JobStatus.OCR_COMPLETED,
        JobStatus.OCR_FAILED,
        JobStatus.CANCELLED,
        JobStatus.MATCHING_COMPLETED,
        JobStatus.MATCHING_ERROR,
    }
)


class JobQueryService:
    """Service for querying and mutating matcher jobs."""

    def __init__(self, session: Session):
        self._session = session

    def list_jobs(self) -> JobListResponse:
        """List all matcher jobs.

        Returns:
            JobListResponse with all jobs and total count.
        """
        from app.routers.job_router import JobListResponse

        jobs = self._session.exec(select(MatcherJob)).all()
        return JobListResponse(
            jobs=[self._build_job_response(job) for job in jobs],
            total=len(jobs),
        )

    def get_job(self, job_id: int) -> JobResponse:
        """Get a single job by ID.

        Args:
            job_id: Job ID

        Returns:
            JobResponse with job details

        Raises:
            ValueError: If job not found
        """

        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return self._build_job_response(job)

    def create_job(
        self,
        campaign_id: uuid.UUID,
        provider_name: str | None = None,
        provider_model: str | None = None,
        force_reprocess: bool = False,
    ) -> JobResponse:
        """Create a new matcher job.

        Args:
            campaign_id: Campaign UUID
            provider_name: OCR provider name (optional)
            provider_model: OCR provider model (optional)
            force_reprocess: Whether to force reprocessing

        Returns:
            JobResponse for the created job

        Raises:
            ValueError: If campaign not found or has no petition scans
        """
        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        petition_scans = self._session.exec(
            select(PetitionScan).where(PetitionScan.campaign_id == campaign_id)
        ).all()
        if not petition_scans:
            raise ValueError(
                "No petition scans uploaded for this campaign. "
                "Please upload a petition PDF first."
            )

        active_upload = self._session.exec(
            select(VoterListUpload).where(
                VoterListUpload.region_id == campaign.region_id,
                VoterListUpload.status == UploadStatus.ACTIVE,
            )
        ).first()
        if not active_upload:
            raise ValueError(
                "No voter list uploaded for this campaign's region. "
                "Please upload a voter list first."
            )

        self._validate_ocr_provider(self._session)

        job = MatcherJob(
            campaign_id=campaign_id,
            current_status=JobStatus.NOT_STARTED,
            provider_name=provider_name,
            provider_model=provider_model,
            force_reprocess=force_reprocess,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)

        return self._build_job_response(job)

    def cancel_job(self, job_id: int) -> JobResponse:
        """Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            JobResponse with updated status

        Raises:
            ValueError: If job not found or cannot be cancelled
        """
        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.current_status not in _CANCELABLE_STATES:
            raise ValueError(
                f"Job cannot be cancelled in state {job.current_status.value}"
            )

        job.current_status = JobStatus.CANCELLED
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)

        return self._build_job_response(job)

    def start_job(self, job_id: int) -> JobResponse:
        """Start a NOT_STARTED job.

        Args:
            job_id: Job ID

        Returns:
            JobResponse with updated status

        Raises:
            ValueError: If job not found, wrong state, or no scans
        """
        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.current_status != JobStatus.NOT_STARTED:
            raise ValueError(
                f"Job cannot be started in state {job.current_status.value}"
            )

        petition_scans = self._session.exec(
            select(PetitionScan).where(PetitionScan.campaign_id == job.campaign_id)
        ).all()
        if not petition_scans:
            raise ValueError("Cannot start job: Campaign has no petition scans")

        job.current_status = JobStatus.OCR_PENDING
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)

        return self._build_job_response(job)

    def retry_job(self, job_id: int) -> JobResponse:
        """Retry a failed or stuck job by resetting it to NOT_STARTED.

        Args:
            job_id: Job ID to retry

        Returns:
            JobResponse with updated status

        Raises:
            ValueError: If job not found or cannot be retried in current state
        """
        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.current_status not in _RETRYABLE_STATES:
            raise ValueError(
                f"Job cannot be retried in state {job.current_status.value}"
            )

        job.current_status = JobStatus.NOT_STARTED
        job.started_on = None
        job.ended_on = None
        job.error_data = {}

        child_ocr_jobs = self._session.exec(
            select(OcrJob).where(OcrJob.matcher_job_id == job.id)
        ).all()
        for ocr_job in child_ocr_jobs:
            if ocr_job.status not in _TERMINAL_OCR_STATES:
                ocr_job.status = JobStatus.NOT_STARTED

        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)

        return self._build_job_response(job)

    def _build_job_response(self, job: MatcherJob) -> JobResponse:
        """Convert a MatcherJob to a JobResponse.

        Args:
            job: MatcherJob database record

        Returns:
            JobResponse with formatted fields
        """
        from app.routers.job_router import JobResponse

        campaign = self._session.get(Campaign, job.campaign_id)

        error_message = None
        if job.error_data and isinstance(job.error_data, dict):
            error_message = job.error_data.get("message") or job.error_data.get("error")

        is_orphaned = job.current_status in _ORPHAN_STATES

        return JobResponse(
            job_id=job.id,
            status=job.current_status.value,
            campaign_id=job.campaign_id,
            campaign_name=campaign.unique_name if campaign else None,
            provider_name=job.provider_name,
            provider_model=job.provider_model,
            force_reprocess=job.force_reprocess,
            cached_ocr_count=job.cached_ocr_count,
            new_ocr_count=job.new_ocr_count,
            ocr_duration_seconds=job.ocr_duration_seconds,
            matching_duration_seconds=job.matching_duration_seconds,
            created_at=job.created_at,
            updated_at=job.updated_on,
            started_at=job.started_on,
            ended_at=job.ended_on,
            error_message=error_message,
            is_orphaned=is_orphaned,
        )

    @staticmethod
    def get_phase(status: str) -> str:
        """Determine current phase from status string.

        Args:
            status: Job status string

        Returns:
            Phase name: 'ocr', 'matching', 'complete', 'error', or 'unknown'
        """
        terminal_complete = ("MATCHING_COMPLETED",)
        terminal_error = ("OCR_FAILED", "OCR_TIMEOUT", "MATCHING_ERROR")

        if status in terminal_complete:
            return "complete"
        elif status in terminal_error:
            return "error"
        elif "OCR" in status:
            return "ocr"
        elif "MATCHING" in status:
            return "matching"
        return "unknown"

    @staticmethod
    def _validate_ocr_provider(session: Session) -> None:
        """Validate that an OCR provider is configured.

        Checks DB config first, then env vars via resolve_provider_config.

        Raises:
            ValueError: If no OCR provider is configured.
        """
        from app.ocr.ocr_client_factory import resolve_provider_config

        try:
            resolve_provider_config(session=session)
        except ValueError:
            raise ValueError(
                "No OCR provider configured. "
                "Configure via the settings UI or set "
                "OCR_PROVIDER_NAME, OCR_PROVIDER_MODEL, and OCR_PROVIDER_API_KEY "
                "environment variables."
            )
