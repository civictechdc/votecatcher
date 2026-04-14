import uuid
from datetime import UTC, datetime

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
