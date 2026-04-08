"""Test fixtures for demo unit tests."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

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


@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create an in-memory SQLite session for unit tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
