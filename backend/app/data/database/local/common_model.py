import uuid
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class CommonSqlTable(SQLModel):
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
        ),
    )
