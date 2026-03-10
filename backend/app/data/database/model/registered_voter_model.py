import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class DemoFakeRegisteredVoter(SQLModel, table=True):
	__tablename__ = "demo_fake_registered_voters"
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	first_name: str = Field()
	last_name: str = Field()
	street_number: str = Field()
	street_name: str = Field()
	street_type: str = Field()
	street_dir_suffix: str = Field()
	local_path: str = Field()
	file_name: str = Field()
	region_id: uuid.UUID = Field(foreign_key="regions.id")


class CreateDemoFakeRegisteredVoter(SQLModel):
	first_name: str
	last_name: str
	street_number: str
	street_name: str
	street_type: str | None = None
	street_dir_suffix: str | None = None
	file_name: str
	local_path: str
	region_id: uuid.UUID


class ReadDemoFakeRegisteredVoter(SQLModel):
	id: str
	first_name: str
	last_name: str
	street_number: str
	street_name: str
	street_type: str | None
	street_dir_suffix: str | None
	file_name: str
