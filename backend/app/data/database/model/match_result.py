"""Match result model for fuzzy matching predictions."""

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ConfidenceLevel(str, Enum):
    """Confidence levels for match results."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MatchResult(SQLModel, table=True):
    __tablename__ = "match_results"

    id: int | None = Field(default=None, primary_key=True)
    ocr_result_id: int = Field(foreign_key="ocr_results.id", nullable=False)
    matcher_job_id: int = Field(foreign_key="matcher_jobs.id", nullable=False)
    rank: int = Field(ge=1, le=5, nullable=False)
    voter_id: int | None = Field(default=None, foreign_key="registered_voters.id")
    similarity_score: float = Field(nullable=False)
    confidence_level: ConfidenceLevel = Field(nullable=False)
    field_scores: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MatchResultCreate(SQLModel):
    """Schema for creating a match result."""

    ocr_result_id: int
    matcher_job_id: int
    rank: int
    voter_id: int | None = None
    similarity_score: float
    confidence_level: ConfidenceLevel
    field_scores: dict = {}


class MatchResultRead(SQLModel):
    """Schema for reading a match result."""

    id: int
    ocr_result_id: int
    matcher_job_id: int
    rank: int
    voter_id: int | None
    similarity_score: float
    confidence_level: ConfidenceLevel
    field_scores: dict
    created_at: datetime
