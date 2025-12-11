import uuid
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
import structlog
from sqlmodel import Field, SQLModel


class CommonSqlTable(SQLModel):
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
