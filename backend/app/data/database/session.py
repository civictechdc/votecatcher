import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.settings.env_settings import get_settings

settings = get_settings()

database_url = os.getenv("DATABASE_URL", "sqlite:///./votecatcher.db")

engine = create_engine(database_url, echo=False)


def init_db() -> None:
	"""Initialize database and create all tables."""
	# Import models to register them with SQLModel metadata
	from app.data.database.model.jobs import (  # noqa: F401
		MatcherJob,
		OcrJob,
		OcrModel,
		OcrProvider,
	)
	from app.data.database.model.match_result import MatchResult  # noqa: F401
	from app.data.database.model.ocr_result import OcrResult  # noqa: F401
	from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
	from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
	from app.data.database.model.registered_voter import RegisteredVoter  # noqa: F401
	from app.data.database.model.schema import Campaign, Region  # noqa: F401
	from app.data.database.model.session import Session as SessionModel  # noqa: F401
	from app.data.database.model.user import User  # noqa: F401

	SQLModel.metadata.create_all(engine)


def get_db_session() -> Generator[Session]:
	"""Get database session for dependency injection."""
	with Session(engine) as session:
		yield session
