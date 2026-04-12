"""Petition domain object."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Petition(BaseModel, frozen=True):
    """Petition domain object for business logic."""

    id: int | None = None
    campaign_id: UUID
    original_filename: str
    stored_path: str
    file_hash: str
    file_size: int | None = None
    page_count: int | None = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    uploaded_by: int | None = None

    def is_processed(self) -> bool:
        """Check if petition has been fully processed."""
        return self.page_count is not None and self.page_count > 0

    def __repr__(self) -> str:
        return f"Petition(id={self.id}, filename={self.original_filename!r})"
