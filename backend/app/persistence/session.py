"""Session management with engine selection."""

from __future__ import annotations

from collections.abc import Generator

import structlog
from sqlmodel import Session

from app.persistence.engines.base import BaseEngine
from app.persistence.engines.sqlite import SqliteEngine
from app.persistence.engines.supabase import SupabaseEngine
from app.settings import get_settings
from app.utils.masking import mask_url

logger = structlog.get_logger(__name__)

_cached_engine: BaseEngine | None = None


def get_engine() -> BaseEngine:
    """Select engine based on configuration.

    Uses a module-level cache that is cleared together with settings
    cache to prevent desync between get_settings() and get_engine().
    """
    global _cached_engine
    if _cached_engine is not None:
        return _cached_engine

    settings = get_settings()

    if settings.supabase.is_connected:
        logger.info("Using Supabase engine", project=mask_url(settings.supabase.url))
        _cached_engine = SupabaseEngine(
            project_url=settings.supabase.url,
            service_key=settings.supabase.service_key,
            database_url=settings.supabase.database_url,
        )
    else:
        logger.info("Using SQLite engine")
        _cached_engine = SqliteEngine(url=settings.database.url)

    return _cached_engine


def clear_engine_cache() -> None:
    """Clear the cached engine so next get_engine() call re-evaluates config."""
    global _cached_engine
    _cached_engine = None
    logger.info("Engine cache cleared")


def get_db_session() -> Generator[Session]:
    """Get database session for dependency injection."""
    engine = get_engine()
    session = engine.create_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
