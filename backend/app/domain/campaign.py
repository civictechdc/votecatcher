"""Campaign domain object."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Campaign(BaseModel):
	"""Campaign domain object for business logic."""

	id: UUID = Field(default_factory=uuid4)
	unique_name: str
	title: str
	description: str | None = None
	year: str
	region_id: UUID
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = None

	def is_active(self) -> bool:
		"""Check if campaign is in current year (active)."""
		from datetime import date

		return self.year == str(date.today().year)

	def __repr__(self) -> str:
		return (
			f"Campaign(id={self.id}, "
			f"unique_name={self.unique_name!r}, "
			f"title={self.title!r})"
		)
