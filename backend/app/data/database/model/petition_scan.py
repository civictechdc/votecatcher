"""Petition scan model for uploaded PDF files."""

from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class PetitionScan(SQLModel, table=True):
    __tablename__ = "petition_scans"

    id: int | None = Field(default=None, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    original_filename: str = Field(nullable=False)
    stored_path: str = Field(nullable=False, unique=True)
    file_hash: str = Field(nullable=False, index=True)
    file_size: int | None = Field(default=None)
    page_count: int | None = Field(default=None)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    uploaded_by: int | None = Field(default=None, foreign_key="users.id")


class PetitionScanCreate(SQLModel):
    """Schema for creating a petition scan."""

    campaign_id: UUID
    original_filename: str
    stored_path: str
    file_hash: str
    page_count: int | None = None


class PetitionScanRead(SQLModel):
    """Schema for reading a petition scan."""

    id: int
    campaign_id: UUID
    original_filename: str
    stored_path: str
    file_hash: str
    page_count: int | None
    uploaded_at: datetime
    uploaded_by: int | None
