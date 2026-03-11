"""Unit tests for DemoDataService."""

from sqlmodel import Session, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region
from app.demo.demo_service import DemoDataService


class TestDemoDataService:
	"""Tests for demo data service."""

	def test_load_minimal_session_creates_region(self, session: Session):
		"""Test that loading creates a region with demo prefix."""
		service = DemoDataService(session)
		service.load_minimal_session()

		regions = session.exec(select(Region)).all()
		assert len(regions) == 1
		assert regions[0].region_key == "demo-dc"

	def test_load_minimal_session_creates_campaign(self, session: Session):
		"""Test that loading creates a campaign with demo prefix."""
		service = DemoDataService(session)
		service.load_minimal_session()

		campaigns = session.exec(select(Campaign)).all()
		assert len(campaigns) == 1
		assert campaigns[0].unique_name == "demo-dc-2024"
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

	def test_reset_clears_all_demo_data(self, session: Session):
		"""Test that reset clears only demo data across multiple tables."""
		service = DemoDataService(session)
		service.load_minimal_session()

		assert len(session.exec(select(Region)).all()) == 1
		assert len(session.exec(select(Campaign)).all()) == 1
		assert len(session.exec(select(RegisteredVoter)).all()) == 10
		assert len(session.exec(select(PetitionScan)).all()) == 1
		assert len(session.exec(select(PetitionCrop)).all()) == 10
		assert len(session.exec(select(MatcherJob)).all()) == 1
		assert len(session.exec(select(OcrJob)).all()) == 1
		assert len(session.exec(select(OcrResult)).all()) == 10
		assert len(session.exec(select(MatchResult)).all()) == 50

		service.reset()

		assert len(session.exec(select(Region)).all()) == 0
		assert len(session.exec(select(Campaign)).all()) == 0
		assert len(session.exec(select(RegisteredVoter)).all()) == 0
		assert len(session.exec(select(PetitionScan)).all()) == 0
		assert len(session.exec(select(PetitionCrop)).all()) == 0
		assert len(session.exec(select(MatcherJob)).all()) == 0
		assert len(session.exec(select(OcrJob)).all()) == 0
		assert len(session.exec(select(OcrResult)).all()) == 0
		assert len(session.exec(select(MatchResult)).all()) == 0

	def test_load_minimal_session_resets_before_loading(self, session: Session):
		"""Test that loading twice doesn't cause UNIQUE constraint errors."""
		service = DemoDataService(session)

		# First load
		result1 = service.load_minimal_session()
		assert result1["success"] is True
		assert len(session.exec(select(Region)).all()) == 1
		assert len(session.exec(select(Campaign)).all()) == 1
		assert len(session.exec(select(RegisteredVoter)).all()) == 10

		# Second load should reset first and not raise UNIQUE constraint error
		result2 = service.load_minimal_session()
		assert result2["success"] is True
		assert len(session.exec(select(Region)).all()) == 1
		assert len(session.exec(select(Campaign)).all()) == 1
		assert len(session.exec(select(RegisteredVoter)).all()) == 10

		# Campaign ID should be different (new data, not same records)
		assert result1["campaign_id"] != result2["campaign_id"]

	def test_reset_preserves_non_demo_data(self, session: Session):
		"""Test that reset preserves non-demo data."""
		non_demo_region = Region(
			region_key="ny",
			region_name="New York",
			country_code="US",
		)
		session.add(non_demo_region)
		non_demo_campaign = Campaign(
			unique_name="ny-2024",
			title="NY Campaign 2024",
			description="Non-demo campaign",
			year="2024",
			region_id=non_demo_region.id,
		)
		session.add(non_demo_campaign)
		session.commit()

		service = DemoDataService(session)
		service.load_minimal_session()

		assert len(session.exec(select(Region)).all()) == 2
		assert len(session.exec(select(Campaign)).all()) == 2

		service.reset()

		assert len(session.exec(select(Region)).all()) == 1
		assert len(session.exec(select(Campaign)).all()) == 1
		assert (
			session.exec(select(Region).where(Region.region_key == "ny")).first()
			is not None
		)
		assert (
			session.exec(
				select(Campaign).where(Campaign.unique_name == "ny-2024")
			).first()
			is not None
		)
