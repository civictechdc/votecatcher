import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

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

	Patches init_db and get_engine to prevent any real DB connections.
	Overrides both get_session and get_db_session dependencies.
	"""
	from app.api import app
	from app.data.database.session import get_db_session
	from app.dependencies import get_session
	from app.persistence.session import clear_engine_cache

	test_engine = create_engine(
		"sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
		connect_args={"check_same_thread": False},
	)
	SQLModel.metadata.create_all(test_engine)

	def override_get_session():
		yield session

	app.dependency_overrides[get_session] = override_get_session
	app.dependency_overrides[get_db_session] = override_get_session

	clear_engine_cache()
	with (
		patch("app.api.init_db"),
		patch("app.persistence.session.get_engine", return_value=test_engine),
		TestClient(app) as test_client,
	):
		yield test_client

	session.close()
	app.dependency_overrides.clear()
	clear_engine_cache()
	test_engine.dispose()


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
