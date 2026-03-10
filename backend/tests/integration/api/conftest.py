import uuid

import pytest
from sqlmodel import Session

from app.data.database.model.schema import Campaign, Region
from app.data.database.session import engine, init_db


@pytest.fixture(name="session", scope="function")
def session_fixture():
	"""Create a test database session using the real database.

	Ensures tables exist before running tests.
	"""
	init_db()
	with Session(engine) as session:
		yield session


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
