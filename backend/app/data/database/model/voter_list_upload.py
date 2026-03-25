"""Voter list upload tracking model."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class UploadStatus(str, Enum):
	"""Status of a voter list upload."""

	ACTIVE = "active"
	SUPERSEDED = "superseded"


class VoterListUpload(SQLModel, table=True):
	"""Tracks voter list upload history for regions."""

	__tablename__ = "voter_list_uploads"

	id: UUID = Field(default_factory=uuid4, primary_key=True)
	region_id: UUID = Field(foreign_key="regions.id", nullable=False, index=True)
	original_filename: str = Field(nullable=False)
	file_size: int = Field(nullable=False)
	row_count: int = Field(nullable=False)
	status: UploadStatus = Field(default=UploadStatus.ACTIVE)
	uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	superseded_at: datetime | None = Field(default=None)
	superseded_by: UUID | None = Field(
		default=None, foreign_key="voter_list_uploads.id"
	)
