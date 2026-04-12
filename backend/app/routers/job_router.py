"""Job management router with SSE endpoint for real-time status updates."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api_models import ApiModel
from app.data.database.model.jobs import MatcherJob
from app.dependencies import get_session
from app.events.sse_manager import format_sse_message, sse_manager
from app.services.job_query_service import JobQueryService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


SessionDep = Annotated[Session, Depends(get_session)]


class CreateJobRequest(ApiModel):
    """Request schema for creating a matcher job."""

    campaign_id: uuid.UUID
    scan_ids: list[int] = []
    provider_name: str | None = None
    provider_model: str | None = None
    force_reprocess: bool = False


class JobResponse(ApiModel):
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


class JobListResponse(ApiModel):
    """Response schema for listing jobs."""

    jobs: list[JobResponse]
    total: int


@router.get("", response_model=JobListResponse)
def list_jobs(
    session: SessionDep,
) -> JobListResponse:
    return JobQueryService(session).list_jobs()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    request: CreateJobRequest,
    session: SessionDep,
) -> JobResponse:
    """Create a new matcher job."""
    try:
        return JobQueryService(session).create_job(
            campaign_id=request.campaign_id,
            provider_name=request.provider_name,
            provider_model=request.provider_model,
            force_reprocess=request.force_reprocess,
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Get job status."""
    try:
        return JobQueryService(session).get_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Cancel a running job."""
    try:
        return JobQueryService(session).cancel_job(job_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)


@router.post("/{job_id}/start", response_model=JobResponse)
def start_job(
    job_id: int,
    session: SessionDep,
) -> JobResponse:
    """Start a NOT_STARTED job."""
    try:
        return JobQueryService(session).start_job(job_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)


@router.get("/{job_id}/status", response_class=StreamingResponse)
async def get_job_status_stream(
    job_id: int,
    session: SessionDep,
) -> StreamingResponse:
    """SSE endpoint for real-time job status updates."""
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
            "phase": JobQueryService.get_phase(job.current_status.value),
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
