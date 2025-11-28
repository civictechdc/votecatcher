from datetime import datetime, timezone
from typing import Annotated

from app.ocr.batching.batch_ocr_client import BatchJobStatus, JobStatus
from pydantic import BaseModel, Field, PlainSerializer


def date_to_iso_string(datetime: datetime | None) -> str:
    if datetime is None:
        return ""
    return datetime.isoformat()


OptionalDateTime = Annotated[
    datetime | None,
    PlainSerializer(date_to_iso_string),
]


class MatchingJobStatusProgress(BaseModel):
    campaign_id: str
    ocr_job_id: str = Field(
        description="The id of the long running job to performing OCR"
    )
    ocr_provider: str
    started_at: Annotated[datetime, PlainSerializer(date_to_iso_string)] = Field(
        default_factory=datetime.now
    )
    last_updated_at: OptionalDateTime = Field(default=None)
    ended_at: OptionalDateTime = Field(default=None)
    failure_reason: str | None = Field(default=None)
    job_status: JobStatus


def adapt_ocr_batch_status_to_progress_response(
    batch_status: BatchJobStatus,
) -> MatchingJobStatusProgress:
    return MatchingJobStatusProgress(
        campaign_id=batch_status.campaign_id,
        ocr_job_id=batch_status.job_id,
        ocr_provider=batch_status.provider_id,
        started_at=batch_status.started_at,
        job_status=batch_status.status,
        last_updated_at=(
            batch_status.last_updated_at
            if batch_status.last_updated_at
            else datetime.now(timezone.utc)
        ),
        failure_reason=batch_status.error if batch_status.error else None,
        ended_at=batch_status.completed_at if batch_status.completed_at else None,
    )
