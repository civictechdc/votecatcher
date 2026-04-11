"""Config service for data reset and configuration management."""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlmodel import Session

logger = structlog.get_logger(__name__)

RESET_TABLES = [
    "match_results",
    "ocr_results",
    "ocr_jobs",
    "matcher_jobs",
    "petition_crops",
    "petition_scans",
    "campaigns",
]


class ConfigService:
    """Service for config-level operations like data reset."""

    def __init__(self, session: Session):
        self._session = session

    def reset_all_data(self) -> dict[str, int]:
        """Delete all rows from application tables and return deletion counts.

        Returns:
            Dictionary mapping table name to count of deleted rows.
        """
        conn = self._session.connection()
        deleted_counts: dict[str, int] = {}

        for table in RESET_TABLES:
            deleted_counts[table] = conn.execute(
                text(f"DELETE FROM {table}")  # nosec B608 — table names from RESET_TABLES constant, not user input
            ).rowcount

        self._session.commit()

        logger.info("All data reset complete", deleted_counts=deleted_counts)

        return deleted_counts
