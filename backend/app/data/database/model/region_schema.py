"""Region-specific CSV schema model for parsing voter lists."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RegionSchema(SQLModel, table=True):
    """Schema definition for parsing region-specific CSV files."""

    __tablename__ = "region_schemas"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    region_id: UUID = Field(
        foreign_key="regions.id", nullable=False, unique=True, index=True
    )
    name: str = Field(nullable=False)
    column_mappings: dict = Field(default={}, sa_column=Column(JSON))
    hash_fields: list = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
