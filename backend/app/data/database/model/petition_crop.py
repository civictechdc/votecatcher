"""Petition crop model for individual signature entries."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class PetitionCrop(SQLModel, table=True):
    __tablename__ = "petition_crops"

    id: int | None = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="petition_scans.id", nullable=False, index=True)
    crop_index: int = Field(nullable=False)
    stored_path: str = Field(nullable=False, unique=True)
    crop_coordinates: dict = Field(default={}, sa_column=Column(JSON))
    page_number: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PetitionCropCreate(SQLModel):
    """Schema for creating a petition crop."""

    scan_id: int
    crop_index: int
    stored_path: str
    crop_coordinates: dict = {}
    page_number: int


class PetitionCropRead(SQLModel):
    """Schema for reading a petition crop."""

    id: int
    scan_id: int
    crop_index: int
    stored_path: str
    crop_coordinates: dict
    page_number: int
    created_at: datetime
