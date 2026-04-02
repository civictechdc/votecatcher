"""Campaign domain object."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Campaign(BaseModel, frozen=True):
	"""Campaign domain object for business logic."""

	id: UUID = Field(default_factory=uuid4)
	unique_name: str
	title: str
	description: str | None = None
	year: str
	region_id: UUID
	start_date: date | None = None
	end_date: date | None = None
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = None

	def is_active(self) -> bool:
		today = date.today()
		if self.start_date and self.end_date:
			return self.start_date <= today <= self.end_date
		return self.year == str(today.year)

	def __repr__(self) -> str:
		return (
			f"Campaign(id={self.id}, "
			f"unique_name={self.unique_name!r}, "
			f"title={self.title!r})"
		)
