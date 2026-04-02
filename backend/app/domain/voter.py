"""Registered voter domain object."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegisteredVoter(BaseModel, frozen=True):
	"""Registered voter domain object for business logic."""

	id: int | None = None
	region_id: UUID
	name_data: dict[str, str] = Field(default_factory=dict)
	address_data: dict[str, str] = Field(default_factory=dict)
	other_field_data: dict[str, str] = Field(default_factory=dict)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = None

	@property
	def full_name(self) -> str:
		"""Get full name from name_data."""
		parts = [
			self.name_data.get("first_name", ""),
			self.name_data.get("middle_name", ""),
			self.name_data.get("last_name", ""),
		]
		return " ".join(p for p in parts if p)

	def is_matchable(self) -> bool:
		"""Check if voter has enough data for matching."""
		return bool(self.name_data.get("last_name"))

	def __repr__(self) -> str:
		return f"RegisteredVoter(id={self.id}, full_name={self.full_name!r})"
