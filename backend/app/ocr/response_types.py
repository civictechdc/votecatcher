from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

from app.matching.match_repository import MatchingStatus, MatchingTask


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
    task_id: str = Field(
        description="The id of the long running taxk to performing OCR and matching"
    )
    started_at: Annotated[datetime, PlainSerializer(date_to_iso_string)] = Field(
        default_factory=datetime.now
    )
    status_message: str | None = Field(default=None)
    last_updated_at: OptionalDateTime = Field(default=None)
    ended_at: OptionalDateTime = Field(default=None)
    failure_reason: str | None = Field(default=None)
    job_status: MatchingStatus


def adapt_ocr_batch_status_to_progress_response(
    task: MatchingTask,
) -> MatchingJobStatusProgress:
    return MatchingJobStatusProgress(
        campaign_id=task.campaign_id,
        task_id=task.id,
        started_at=task.created_at,
        job_status=task.status,
        last_updated_at=(task.updated_at if task.updated_at else datetime.now(UTC)),
        status_message=task.status_message,
        failure_reason=task.failure_message if task.failure_message else None,
        ended_at=task.ended_at if task.ended_at else None,
    )
