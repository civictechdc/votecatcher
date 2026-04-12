"""OCR result model for extracted text from crops."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class OcrResult(SQLModel, table=True):
    __tablename__ = "ocr_results"

    id: int | None = Field(default=None, primary_key=True)
    crop_id: int = Field(foreign_key="petition_crops.id", nullable=False)
    ocr_job_id: int = Field(foreign_key="ocr_jobs.id", nullable=False)
    ocr_index: int = Field(
        default=0, description="Index of OCR entry within crop (0-4 for 5 signatures)"
    )
    extracted_text: dict = Field(default={}, sa_column=Column(JSON))
    confidence_score: float | None = Field(default=None)
    raw_response: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OcrResultCreate(SQLModel):
    """Schema for creating an OCR result."""

    crop_id: int
    ocr_job_id: int
    ocr_index: int = 0
    extracted_text: dict = {}
    confidence_score: float | None = None
    raw_response: dict = {}


class OcrResultRead(SQLModel):
    """Schema for reading an OCR result."""

    id: int
    crop_id: int
    ocr_job_id: int
    ocr_index: int
    extracted_text: dict
    confidence_score: float | None
    raw_response: dict
    created_at: datetime
