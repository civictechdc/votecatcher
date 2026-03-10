"""Session model for workspace snapshots."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class SessionType(str, Enum):
	"""Types of sessions."""

	DEMO = "DEMO"
	REAL = "REAL"


class Session(SQLModel, table=True):
	"""Saved workspace snapshots."""

	__tablename__ = "sessions"

	id: int = Field(primary_key=True)
	campaign_id: UUID | None = Field(default=None, foreign_key="campaigns.id")
	name: str = Field(nullable=False)
	session_type: SessionType = Field(nullable=False)
	snapshot_data: dict = Field(
		default={}, sa_column=Column(JSON)
	)  # {job_ids, crop_ids, result_ids}
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
