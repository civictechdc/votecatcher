"""Test fixtures for demo unit tests."""

import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create an in-memory SQLite session for unit tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
