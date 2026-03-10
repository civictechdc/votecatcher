"""Registered voter model for voter list data."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RegisteredVoter(SQLModel, table=True):
	"""Voter list data - generic structure for any region."""

	__tablename__ = "registered_voters"

	id: int = Field(primary_key=True)
	region_id: UUID = Field(foreign_key="regions.id", index=True)
	name_data: dict = Field(
		default={}, sa_column=Column(JSON)
	)  # {first_name, last_name, middle_name, etc.}
	address_data: dict = Field(
		default={}, sa_column=Column(JSON)
	)  # {street, city, state, zip, etc.}
	other_field_data: dict = Field(
		default={}, sa_column=Column(JSON)
	)  # {party, registration_date, etc.}
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None, sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
	)

	class Config:
		arbitrary_types_allowed = True
