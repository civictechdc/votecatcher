import uuid
from datetime import datetime, timezone
from typing import Protocol

import sqlalchemy as sa
from app.matching.match_repository import MatchingStatus
from sqlmodel import Field, Relationship, SQLModel


class OcrProvider(SQLModel, table=True):
    __tablename__ = "ocr_providers"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
    unique_name: str = Field(unique=True)
    display_name: str = Field()
    models: list["OcrAiModel"] = Relationship(back_populates="ocr_provider")


class CreateOcrProvider(SQLModel):
    provider_id: str
    provider_name: str
    models: list[str] | None


class ReadOcrProvider(SQLModel):
    id: str
    unique_name: str
    display_name: str


# TODO updating and fetching ocr providers


class OcrAiModel(SQLModel, table=True):
    __tablename__ = "ocr_ai_models"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
    unique_name: str = Field(unique=True)
    display_name: str | None = Field(default=None)
    provider_id: uuid.UUID = Field(foreign_key="ocr_providers.id")
    ocr_provider: OcrProvider = Relationship(back_populates="models")


class AddOcrAiModel(SQLModel):
    model_name: str
    provider_id: str


class ReadOcrModel(SQLModel):
    model_name: str
    unique_name: str
    provider_id: str
    provider_display_name: str


class OcrProviderRepository(Protocol):

    async def create_ocr_provider(self, provider: CreateOcrProvider) -> str: ...

    async def get_ocr_provider(self, unique_name: str) -> ReadOcrProvider: ...

    async def create_ocr_model(self, model: AddOcrAiModel) -> str: ...

    async def fetch_ocr_model(self, unique_name: str) -> ReadOcrModel: ...


# OCR Job data


class OcrJob(SQLModel, table=True):
    __tablename__ = "ocr_jobs"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    job_id: str = Field(unique=True)
    state: MatchingStatus = Field(default=MatchingStatus.NOT_STARTED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
    request_payload: str | None = Field(default=None)
    result_data: str | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    model_version: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    status_message: str | None = Field(default=None)
    provider_id: uuid.UUID = Field(foreign_key="ocr_providers.id")
    campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")
    scan_id: uuid.UUID = Field(foreign_key="petition_scans.id")
    match_task_id: uuid.UUID = Field(
        foreign_key="matching_tasks.id",
        description="A single match task can contain multiple OCR jobs for each batch of scans to process.",
    )


class CreateOcrJob(SQLModel):
    job_id: str
    provider_unique_name: str
    request_payload: str | None
    campaign_unique_name: str
    petition_scan_filename: str
    match_task_id: str


class UpdateOcrJobStatus(SQLModel):
    job_id: str
    state: str
    model_version: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)


class ReadOcrJobStatus(SQLModel):
    job_id: str
    state: str
    model_version: str | None
    created_at: datetime
    updated_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    provider_id: str | None


class OcrJobDocumentLink(SQLModel, table=True):
    __tablename__ = "ocr_job_document_links"
    ocr_job_id: uuid.UUID = Field(foreign_key="ocr_jobs.id", primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="petition_scans.id", primary_key=True)


class OcrResult(SQLModel, table=True):
    __tablename__ = "ocr_results_v1"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
    file_name: str = Field()
    page_num: int = Field()
    row_num: int = Field()
    ocr_name: str = Field()
    ocr_address: str = Field()
    ocr_date: str = Field()
    ocr_ward: int = Field()
    document_id: uuid.UUID = Field(foreign_key="petition_scans.id")
    ocr_job_id: uuid.UUID = Field(foreign_key="ocr_jobs.id")
    matching_task_id: uuid.UUID = Field(foreign_key="matching_tasks.id")
    campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")
