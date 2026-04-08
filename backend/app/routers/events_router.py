from fastapi import APIRouter

from app.events import sse_transport

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/campaigns/{campaign_id}/stream")
async def campaign_event_stream(
    campaign_id: str,
):  # nosemgrep: fastapi-unauthenticated-route
    """SSE stream for all events in a campaign."""
    return await sse_transport.subscribe_to_campaign(campaign_id)


@router.get("/jobs/{job_id}/stream")
async def job_event_stream(job_id: str):  # nosemgrep: fastapi-unauthenticated-route
    """SSE stream for job status updates."""
    return await sse_transport.subscribe_to_job(job_id)
