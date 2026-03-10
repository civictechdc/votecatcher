"""Unit tests for DemoDataService."""

from sqlmodel import Session, select

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region
from app.demo.demo_service import DemoDataService


class TestDemoDataService:
	"""Tests for demo data service."""

	def test_load_minimal_session_creates_region(self, session: Session):
		"""Test that loading creates a region."""
		service = DemoDataService(session)
		service.load_minimal_session()

		regions = session.exec(select(Region)).all()
		assert len(regions) == 1
		assert regions[0].region_key == "dc"

	def test_load_minimal_session_creates_campaign(self, session: Session):
		"""Test that loading creates a campaign."""
		service = DemoDataService(session)
		service.load_minimal_session()

		campaigns = session.exec(select(Campaign)).all()
		assert len(campaigns) == 1
		assert campaigns[0].title == "DC Demo 2024"

	def test_load_minimal_session_creates_voters(self, session: Session):
		"""Test that loading creates 10 voters."""
		service = DemoDataService(session)
		service.load_minimal_session()

		voters = session.exec(select(RegisteredVoter)).all()
		assert len(voters) == 10

	def test_load_minimal_session_creates_matcher_job(self, session: Session):
		"""Test that loading creates a completed matcher job."""
		service = DemoDataService(session)
		service.load_minimal_session()

		jobs = session.exec(select(MatcherJob)).all()
		assert len(jobs) == 1
		assert jobs[0].current_status == JobStatus.MATCHING_COMPLETED

	def test_reset_clears_all_data(self, session: Session):
		"""Test that reset clears all demo data."""
		service = DemoDataService(session)
		service.load_minimal_session()

		# Verify data exists
		assert len(session.exec(select(Region)).all()) == 1

		# Reset
		service.reset()

		# Verify data is cleared
		assert len(session.exec(select(Region)).all()) == 0
		assert len(session.exec(select(Campaign)).all()) == 0
