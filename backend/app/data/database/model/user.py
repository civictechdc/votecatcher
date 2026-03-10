"""Minimal user model for MVP."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
	"""Minimal user model for foreign key references."""

	__tablename__ = "users"

	id: int | None = Field(default=None, primary_key=True)
	email: str = Field(unique=True, nullable=False)
	name: str = Field(nullable=False)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
