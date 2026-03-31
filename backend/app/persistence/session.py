"""Session management with engine selection."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

import structlog
from sqlmodel import Session

from app.persistence.engines.sqlite import SqliteEngine
from app.persistence.engines.supabase import SupabaseEngine
from app.settings import get_settings

logger = structlog.get_logger(__name__)


def _mask_url(url: str) -> str:
	"""Mask project ref in Supabase URL for logging."""
	if ".supabase.co" in url:
		parts = url.split("//")
		if len(parts) == 2:
			sub = parts[1].split(".")[0]
			return f"{parts[0]}//{sub[:3]}***.supabase.co"
	return "***"


@lru_cache
def get_engine():
	"""Select engine based on configuration."""
	settings = get_settings()

	if settings.supabase.is_connected:
		logger.info("Using Supabase engine", project=_mask_url(settings.supabase.url))
		return SupabaseEngine(
			project_url=settings.supabase.url,
			service_key=settings.supabase.service_key,
			database_url=settings.supabase.database_url,
		)

	logger.info("Using SQLite engine")
	return SqliteEngine(url=settings.database.url)


def get_db_session() -> Generator[Session]:
	"""Get database session for dependency injection."""
	engine = get_engine()
	session = engine.create_session()
	try:
		yield session
	finally:
		session.close()
