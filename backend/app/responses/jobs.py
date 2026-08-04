"""Job API response models."""

import uuid
from datetime import datetime

from app.api_models import ApiModel


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
