import asyncio
import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.schema import Campaign, Region
from app.dependencies import get_session

_test_engine = create_engine(
    "sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
    connect_args={"check_same_thread": False},
)


@pytest.fixture(name="session", scope="function")
def session_fixture() -> Generator[Session]:
    """Create a test database session using an in-memory SQLite database."""
    SQLModel.metadata.create_all(_test_engine)
    with Session(_test_engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    """Create a test client with test DB session and mocked lifespan."""
    from app.api import app

    def override_get_session() -> Generator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async def _noop():
        await asyncio.sleep(0)

    with (
        patch("app.api.init_db"),
        patch("app.api.job_worker.start_worker", return_value=_noop()),
        patch("app.api.job_worker.stop_worker", new_callable=AsyncMock),
        TestClient(app) as test_client,
    ):
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_region(session: Session) -> Region:
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
def test_campaign(session: Session, test_region: Region) -> Campaign:
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
