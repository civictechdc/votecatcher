"""Database session management - backwards compatible."""

from collections.abc import Generator

from sqlmodel import Session

from app.persistence.session import get_engine as _get_engine


def init_db() -> None:
	"""Initialize database and create all tables."""
	engine = _get_engine()
	engine.initialize()


def get_db_session() -> Generator[Session]:
	"""Get database session for dependency injection."""
	engine = _get_engine()
	with engine.create_session() as session:
		yield session


def __getattr__(name: str):
	if name == "engine":
		return _get_engine().raw_engine
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
