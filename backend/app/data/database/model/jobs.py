"""Job orchestration models for OCR and matching workflows."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    """Status values for matcher jobs."""

    NOT_STARTED = "NOT_STARTED"
    OCR_PENDING = "OCR_PENDING"
    OCR_STARTED = "OCR_STARTED"
    OCR_COMPLETED = "OCR_COMPLETED"
    OCR_FAILED = "OCR_FAILED"
    OCR_TIMEOUT = "OCR_TIMEOUT"
    MATCHING_PENDING = "MATCHING_PENDING"
    MATCHING = "MATCHING"
    MATCHING_COMPLETED = "MATCHING_COMPLETED"
    MATCHING_ERROR = "MATCHING_ERROR"
    CANCELLED = "CANCELLED"


class MatcherJob(SQLModel, table=True):
    """Orchestrator job tracking OCR → Matching → Results."""

    __tablename__ = "matcher_jobs"

    id: int = Field(primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    current_status: JobStatus = Field(default=JobStatus.NOT_STARTED)
    provider_name: str | None = Field(default=None)
    provider_model: str | None = Field(default=None)
    force_reprocess: bool = Field(default=False)
    cached_ocr_count: int | None = Field(default=None)
    new_ocr_count: int | None = Field(default=None)
    started_on: datetime | None = Field(default=None)
    updated_on: datetime | None = Field(
        default=None, sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
    )
    ended_on: datetime | None = Field(default=None)
    ocr_duration_seconds: float | None = Field(default=None)
    matching_duration_seconds: float | None = Field(default=None)
    error_data: dict = Field(default={}, sa_column=Column(JSON))
    success_data: dict = Field(default={}, sa_column=Column(JSON))
    started_by: int | None = Field(default=None, foreign_key="users.id")
    distinct_ocr_count: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OcrJob(SQLModel, table=True):
    """Child job for batch OCR processing."""

    __tablename__ = "ocr_jobs"

    id: int = Field(primary_key=True)
    matcher_job_id: int = Field(foreign_key="matcher_jobs.id", index=True)
    provider_job_id: str | None = Field(default=None)  # External batch ID from provider
    ocr_model_id: int | None = Field(default=None, foreign_key="ocr_models.id")
    status: JobStatus = Field(default=JobStatus.NOT_STARTED)
    started_on: datetime | None = Field(default=None)
    updated_on: datetime | None = Field(
        default=None, sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
    )
    ended_on: datetime | None = Field(default=None)
    error_data: dict = Field(default={}, sa_column=Column(JSON))
    success_data: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OcrProvider(SQLModel, table=True):
    """OCR provider configuration (OpenAI, Gemini, Mistral)."""

    __tablename__ = "ocr_providers"

    id: int = Field(primary_key=True)
    unique_name: str = Field(unique=True)  # e.g., "openai", "gemini", "mistral"
    display_name: str = Field()  # e.g., "OpenAI GPT-4 Vision"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OcrModel(SQLModel, table=True):
    """OCR model configuration."""

    __tablename__ = "ocr_models"

    id: int = Field(primary_key=True)
    unique_name: str = Field(unique=True)  # e.g., "gpt-4-vision-preview"
    display_name: str = Field()  # e.g., "GPT-4 Vision Preview"
    provider_id: int = Field(foreign_key="ocr_providers.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
