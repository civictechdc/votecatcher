import hmac
import os
from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import structlog
from fastapi import Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.data.database.session import get_db_session as _get_db_session
from app.persistence.session import get_engine as _get_engine

logger = structlog.get_logger(__name__)

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
    tokenUrl="/api/token", scheme_name="JWT"
)

demo_petition_path: Path = Path("temp")

_no_key_warned: bool = False


def warn_database_api_key_missing() -> None:
    """Startup guard: log warning if DATABASE_API_KEY not set in production."""
    if os.getenv("ENABLE_SUPABASE") == "1" and not os.getenv("DATABASE_API_KEY"):
        logger.warning(
            "DATABASE_API_KEY is not set. Database API endpoints are unprotected. "
            "Set DATABASE_API_KEY before deploying to production."
        )


def get_session() -> Generator[Session]:
    """Get database session for API endpoints."""
    yield from _get_db_session()


def get_field_spec_service() -> Generator:
    """Get FieldSpecService with DB-backed repository."""
    from app.repositories.field_spec_repo import FieldSpecRepositoryImpl
    from app.services.field_spec_service import FieldSpecService

    engine = _get_engine()
    repo = FieldSpecRepositoryImpl(engine)
    yield FieldSpecService(repo)


def get_matching_engine():
    """Get the configured ScoreAggregator from settings."""
    from app.matching.engines import get_engine
    from app.settings.settings import get_settings

    settings = get_settings()
    return get_engine(settings.matching_engine)


def get_region_by_key(session: Session, region_key: str) -> UUID:
    """Look up a region by key, creating default DC if needed."""
    from sqlmodel import select

    from app.data.database.model.schema import Region

    normalized_key = region_key.upper()
    region = session.exec(
        select(Region).where(Region.region_key == normalized_key)
    ).first()
    if region:
        return region.id
    raise ValueError(f"Region '{region_key}' not found")


def get_engine_dependency() -> Generator[Session]:
    """Get database session — alias for FastAPI Depends injection."""
    yield from _get_db_session()


async def verify_database_api_key(
    x_api_key: str | None = Header(default=None),
) -> str:
    global _no_key_warned
    api_key = x_api_key or ""
    expected = os.getenv("DATABASE_API_KEY", "")
    if not expected:
        if not _no_key_warned:
            _no_key_warned = True
            logger.warning(
                "DATABASE_API_KEY not set — database endpoints are unprotected. "
                "Set DATABASE_API_KEY in production to enable authentication."
            )
        return api_key
    if not hmac.compare_digest(api_key, expected):
        logger.warning("Database API key mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key
