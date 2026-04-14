"""Persistence model for regional field specifications."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RegionFieldSpecModel(SQLModel, table=True):
    __tablename__ = "region_field_specs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    region_id: UUID = Field(
        foreign_key="regions.id", nullable=False, unique=True, index=True
    )
    region_key: str = Field(nullable=False, unique=True, index=True)
    name: str = Field(nullable=False)
    ballot_fields: list = Field(default=[], sa_column=Column(JSON))
    voter_reg_fields: list = Field(default=[], sa_column=Column(JSON))
    field_mappings: list = Field(default=[], sa_column=Column(JSON))
    hash_fields: list = Field(default=[], sa_column=Column(JSON))
    crop_config: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
