import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.data.database.model.region_field_spec  # noqa: F401 — ensures table creation
from app.data.database.model.schema import Campaign, Region


@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create a test database session using an in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def client(session: Session):
    """Create test client with the test database session.

    Uses the same engine as the session fixture so data is shared.
    """
    from app.api import app
    from app.data.database.session import get_db_session
    from app.dependencies import get_field_spec_service, get_session
    from app.persistence.session import clear_engine_cache
    from app.repositories.field_spec_repo import FieldSpecRepositoryImpl
    from app.services.field_spec_service import FieldSpecService

    test_engine = session.get_bind()

    class _TestEngine:
        def create_session(self):
            return Session(test_engine)

        def health_check(self) -> bool:
            return True

    def override_get_session():
        yield session

    def override_get_field_spec_service():
        repo = FieldSpecRepositoryImpl(_TestEngine())
        yield FieldSpecService(repo)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_db_session] = override_get_session
    app.dependency_overrides[get_field_spec_service] = override_get_field_spec_service

    clear_engine_cache()
    with (
        patch("app.persistence.session.get_engine", return_value=_TestEngine()),
        TestClient(app) as test_client,
    ):
        yield test_client

    session.close()
    app.dependency_overrides.clear()
    clear_engine_cache()


@pytest.fixture
def test_region(session: Session):
    """Create test region with unique key."""
    region = Region(
        region_key=f"TEST_DC_{uuid.uuid4().hex[:8]}",
        region_name="Test District of Columbia",
        country_code="US",
    )
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


@pytest.fixture
def test_campaign(session: Session, test_region: Region):
    """Create test campaign with proper foreign keys."""
    campaign = Campaign(
        unique_name=f"test_campaign_{uuid.uuid4().hex[:8]}",
        title="Test Campaign 2024",
        year="2024",
        region_id=test_region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign
