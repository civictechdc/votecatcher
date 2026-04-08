"""Job management router with SSE endpoint for real-time status updates."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign
from app.dependencies import get_session
from app.events.sse_manager import format_sse_message, sse_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


SessionDep = Annotated[Session, Depends(get_session)]


class CreateJobRequest(BaseModel):
    """Request schema for creating a matcher job."""

    campaign_id: uuid.UUID
    scan_ids: list[int] = []
    provider_name: str | None = None
    provider_model: str | None = None
    force_reprocess: bool = False


class JobResponse(BaseModel):
    """Response schema for job status."""

    job_id: int
    status: str
    campaign_id: uuid.UUID
    campaign_name: str | None = None
    provider_name: str | None = None
    provider_model: str | None = None
    force_reprocess: bool = False
    cached_ocr_count: int | None = None
    new_ocr_count: int | None = None
    ocr_duration_seconds: float | None = None
    matching_duration_seconds: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_message: str | None = None
    is_orphaned: bool = False


class JobListResponse(BaseModel):
    """Response schema for listing jobs."""

    jobs: list[JobResponse]
    total: int


def _build_job_response(job: MatcherJob, session: Session) -> JobResponse:
    campaign = session.get(Campaign, job.campaign_id)
    error_message = None
    if job.error_data and isinstance(job.error_data, dict):
        error_message = job.error_data.get("message") or job.error_data.get("error")

    orphan_states = {
        JobStatus.OCR_STARTED,
        JobStatus.OCR_COMPLETED,
        JobStatus.MATCHING_PENDING,
        JobStatus.MATCHING,
    }
    is_orphaned = job.current_status in orphan_states

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


@router.get("", response_model=JobListResponse)
def list_jobs(session: SessionDep) -> JobListResponse:
    jobs = session.exec(select(MatcherJob)).all()
    return JobListResponse(
        jobs=[_build_job_response(job, session) for job in jobs],
        total=len(jobs),
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    request: CreateJobRequest,
    session: SessionDep,
) -> JobResponse:
    """Create a new matcher job.

    Args:
            request: Job creation request
            session: Database session

    Returns:
            Created job details

    Raises:
            HTTPException: 404 if campaign not found
    """
    campaign = session.get(Campaign, request.campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {request.campaign_id} not found",
        )

    petition_scans = session.exec(
        select(PetitionScan).where(PetitionScan.campaign_id == request.campaign_id)
    ).all()
    if not petition_scans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot create job: No petition scans uploaded for this campaign. "
                "Please upload a petition PDF first."
            ),
        )

    job = MatcherJob(
        campaign_id=request.campaign_id,
        current_status=JobStatus.NOT_STARTED,
        provider_name=request.provider_name,
        provider_model=request.provider_model,
        force_reprocess=request.force_reprocess,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    logger.info(
        "Created matcher job",
        job_id=job.id,
        campaign_id=request.campaign_id,
        provider_name=request.provider_name,
        provider_model=request.provider_model,
    )

    return _build_job_response(job, session)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Get job status.

    Args:
            job_id: Job ID
            session: Database session

    Returns:
            Job status details

    Raises:
            HTTPException: 404 if job not found
    """
    job = session.get(MatcherJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return _build_job_response(job, session)


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Cancel a running job.

    Args:
            job_id: Job ID
            session: Database session

    Returns:
            Updated job status

    Raises:
            HTTPException: 404 if job not found
            HTTPException: 400 if job cannot be cancelled
    """
    job = session.get(MatcherJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    cancelable_states = [
        JobStatus.NOT_STARTED,
        JobStatus.OCR_PENDING,
        JobStatus.OCR_STARTED,
        JobStatus.OCR_COMPLETED,
        JobStatus.MATCHING_PENDING,
        JobStatus.MATCHING,
    ]
    if job.current_status not in cancelable_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be cancelled in state {job.current_status.value}",
        )

    job.current_status = JobStatus.CANCELLED
    session.add(job)
    session.commit()
    session.refresh(job)

    logger.info("Cancelled job", job_id=job_id)

    return _build_job_response(job, session)


@router.post("/{job_id}/start", response_model=JobResponse)
def start_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Start a NOT_STARTED job.

    Args:
            job_id: Job ID
            session: Database session

    Returns:
            Updated job status

    Raises:
            HTTPException: 404 if job not found
            HTTPException: 400 if job not in NOT_STARTED state or no scans
    """
    job = session.get(MatcherJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job.current_status != JobStatus.NOT_STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be started in state {job.current_status.value}",
        )

    petition_scans = session.exec(
        select(PetitionScan).where(PetitionScan.campaign_id == job.campaign_id)
    ).all()
    if not petition_scans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start job: Campaign has no petition scans",
        )

    job.current_status = JobStatus.OCR_PENDING
    session.add(job)
    session.commit()
    session.refresh(job)

    logger.info("Started job", job_id=job_id)

    return _build_job_response(job, session)


@router.get("/{job_id}/status", response_class=StreamingResponse)
async def get_job_status_stream(
    job_id: int,
    session: SessionDep,
) -> StreamingResponse:
    """SSE endpoint for real-time job status updates.

    Args:
            job_id: Job ID to subscribe to
            session: Database session

    Returns:
            StreamingResponse with SSE events

    Raises:
            HTTPException: 404 if job not found
    """
    job = session.get(MatcherJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return StreamingResponse(
        _generate_events(job_id, job, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _generate_events(
    job_id: int,
    job: MatcherJob,
    session: Session,
) -> AsyncGenerator[str]:
    """Generate SSE events for job status updates."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    await sse_manager.connect(job_id, queue)

    try:
        initial_status = {
            "job_id": job_id,
            "status": job.current_status.value,
            "phase": _get_phase(job.current_status.value),
            "timestamp": job.updated_on.isoformat() if job.updated_on else None,
        }
        yield format_sse_message("status_update", initial_status)

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield message

                session.expire_all()
                job = session.get(MatcherJob, job_id)

                if job and job.current_status.value in [
                    "MATCHING_COMPLETED",
                    "OCR_FAILED",
                    "OCR_TIMEOUT",
                    "MATCHING_ERROR",
                ]:
                    logger.info("Terminal state reached, closing SSE connection")
                    break

            except TimeoutError:
                yield ": heartbeat\n\n"

    except asyncio.CancelledError:
        logger.info("SSE connection cancelled by client", job_id=job_id)

    finally:
        sse_manager.disconnect(job_id, queue)


def _get_phase(status: str) -> str:
    """Determine current phase from status."""
    if "OCR" in status:
        return "ocr"
    elif "MATCHING" in status:
        return "matching"
    elif "COMPLETE" in status:
        return "complete"
    elif "ERROR" in status or "FAILED" in status or "TIMEOUT" in status:
        return "error"
    return "unknown"
