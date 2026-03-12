import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.api import app
from app.data.database.model.schema import Campaign, Region
from app.dependencies import get_session as get_db_session


@pytest.fixture(name="session", scope="function")
def session_fixture():
	"""Create a test database session using an in-memory SQLite database.

	Uses check_same_thread=False to to prevent threading issues with SQLite.
	"""
	test_engine = create_engine("sqlite:///:memory:")
	SQLModel.metadata.create_all(test_engine)

	with Session(test_engine) as session:
		yield session


@pytest.fixture
def client(session: Session):
	"""Create a test client with the test database session."""

	def override_get_session():
		yield session

	app.dependency_overrides[get_db_session] = override_get_session
	with TestClient(app) as test_client:
		yield test_client
	app.dependency_overrides.clear()


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
