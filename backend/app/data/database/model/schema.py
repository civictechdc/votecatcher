import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Region(SQLModel, table=True):
	__tablename__ = "regions"
	id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
	region_key: str = Field(unique=True)
	region_name: str = Field()
	country_code: str = Field()


class Campaign(SQLModel, table=True):
	__tablename__ = "campaigns"
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	unique_name: str = Field(unique=True)
	title: str = Field()
	description: str | None = Field(default=None, nullable=True)
	year: str = Field()
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	region_id: uuid.UUID = Field(foreign_key="regions.id")

	# __table_args__ = (UniqueConstraint("name", "year"),)


class WashingtonDCRegisteredVoter(SQLModel, table=False):
	__tablename__ = "dc_registered_voters_"
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	last_name: str = Field()
	first_name: str = Field()
	middle_name: str = Field()
	name_style: str = Field()
	street_number: str = Field()
	street_number_suffix: str = Field()
	street_name: str = Field()
	street_type: str = Field()
	street_suffix: str = Field()
	unit_type: str = Field()
	apt_number: str = Field()
	zip_code: str = Field()
	city_name: str = Field(default="")
	registration_date: date = Field()
	registered_party: str = Field()
	smd: str = Field()
	anc: str = Field()
	ward: int = Field()
	is_active_voter: bool = Field()
	is_citizen: bool = Field()
	region_id: uuid.UUID = Field(foreign_key="regions.id")


class DcRegisteredVoterSummarise(SQLModel, table=False):
	__tablename__ = "dc_short_registered_voters"
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	page: int
	line: int
	checker: str
	check_time: datetime
	voter_id: str
	finding: str
	voter_name: str
	address: str
	ward: int
	date_signed: date
	party: str
	notes: str
	circulator_name: str
	region_id: uuid.UUID = Field(foreign_key="regions.id")
