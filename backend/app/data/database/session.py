import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.settings.env_settings import get_settings

settings = get_settings()

database_url = os.getenv("DATABASE_URL", "sqlite:///./votecatcher.db")

engine = create_engine(database_url, echo=False)


def init_db() -> None:
	"""Initialize database and create all tables."""
	from app.data.database.model import (
		jobs,
		match_result,
		ocr_result,
		petition_crop,
		petition_scan,
		registered_voter,
		schema,
		session,
		user,
	)

	SQLModel.metadata.create_all(engine)


def get_db_session() -> Generator[Session, None, None]:
	"""Get database session for dependency injection."""
	with Session(engine) as session:
		yield session
