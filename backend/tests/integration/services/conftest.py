import uuid

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.schema import Region


@pytest.fixture(name="session", scope="function")
def session_fixture():
	"""Create a test database session using an in-memory SQLite database."""
	test_engine = create_engine(
		"sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
		connect_args={"check_same_thread": False},
	)
	SQLModel.metadata.create_all(test_engine)

	with Session(test_engine) as session:
		yield session


@pytest.fixture
def test_region(session: Session):
	"""Create test region with unique key."""
	region = Region(
		region_key=f"TEST_VLT_{uuid.uuid4().hex[:8]}",
		region_name="Test Region for Voter Lists",
		country_code="US",
	)
	session.add(region)
	session.commit()
	session.refresh(region)
	return region
