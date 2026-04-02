"""Integration tests for Job orchestration.

Tests cover job state machine transitions, OCR → Matching coordination,
and error handling with database persistence.
"""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.user import User
from app.jobs.job_orchestrator import JobOrchestrator


class TestJobOrchestratorIntegration:
	"""Integration tests for JobOrchestrator with database."""

	@pytest.fixture
	def temp_storage_dir(self):
		"""Create temporary storage directory."""
		with TemporaryDirectory() as temp_dir:
			yield Path(temp_dir)

	@pytest.fixture
	def engine(self):
		"""Create in-memory SQLite engine for testing."""
		engine = create_engine("sqlite:///:memory:", echo=False)
		SQLModel.metadata.create_all(engine)
		yield engine
		engine.dispose()

	@pytest.fixture
	def session(self, engine):
		"""Create database session for each test."""
		with Session(engine) as session:
			yield session

	@pytest.fixture
	def sample_region(self, session):
		"""Create a sample region for testing."""
		region = Region(
			region_key="DC",
			region_name="Washington, DC",
			country_code="US",
		)
		session.add(region)
		session.commit()
		session.refresh(region)
		return region

	@pytest.fixture
	def sample_user(self, session):
		"""Create a sample user for testing."""
		user = User(
			email="test@example.com",
			name="Test User",
		)
		session.add(user)
		session.commit()
		session.refresh(user)
		return user

	@pytest.fixture
	def sample_campaign(self, session, sample_region):
		"""Create a sample campaign for testing."""
		campaign = Campaign(
			unique_name="dc-2024",
			title="DC 2024",
			description="Test campaign",
			year="2024",
			region_id=sample_region.id,
		)
		session.add(campaign)
		session.commit()
		session.refresh(campaign)
		return campaign

	@pytest.fixture
	def sample_petition_scan(self, session, sample_campaign, sample_user):
		"""Create a sample petition scan."""
		scan = PetitionScan(
			campaign_id=sample_campaign.id,
			original_filename="test_petition.pdf",
			stored_path="/tmp/test_petition.pdf",
			file_hash="abc123",
			page_count=1,
			uploaded_by=sample_user.id,
		)
		session.add(scan)
		session.commit()
		session.refresh(scan)
		return scan

	@pytest.fixture
	def sample_crops(self, session, sample_petition_scan, temp_storage_dir):
		"""Create sample petition crops with actual files."""
		crops = []
		for i in range(2):
			crop_path = temp_storage_dir / f"crop_{i}.png"
			crop_path.write_bytes(b"fake_image_data")

			crop = PetitionCrop(
				scan_id=sample_petition_scan.id,
				crop_index=i,
				stored_path=str(crop_path),
				crop_coordinates={"top": 0.0, "bottom": 0.5},
				page_number=1,
			)
			session.add(crop)
			crops.append(crop)

		session.commit()
		for crop in crops:
			session.refresh(crop)
		return crops

	@pytest.fixture
	def mock_ocr_service(self, sample_crops, sample_campaign):
		"""Create a mock OCR service."""
		service = AsyncMock()

		async def mock_create_job(**kwargs):
			return OcrJob(
				matcher_job_id=kwargs["matcher_job_id"],
				provider_job_id="test-job-123",
				status=JobStatus.OCR_PENDING,
				started_on=datetime.now(UTC),
			)

		service.create_ocr_job = mock_create_job

		async def mock_poll_status(ocr_job_id, ocr_client):
			return AsyncMock(
				id=ocr_job_id,
				status=JobStatus.OCR_COMPLETED,
			)

		service.poll_job_status = mock_poll_status
		return service

	@pytest.fixture
	def mock_matching_service(self):
		"""Create a mock matching service."""
		service = AsyncMock()
		service.run_matching = AsyncMock(return_value=[])
		return service

	def test_create_matcher_job_persists_to_db(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Should create matcher job and persist to database."""
		orchestrator = JobOrchestrator(
			session=session,
			ocr_service=AsyncMock(),
			matching_service=AsyncMock(),
			storage_base=temp_storage_dir,
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		assert job is not None
		assert job.campaign_id == sample_campaign.id
		assert job.current_status == JobStatus.NOT_STARTED

		db_job = session.get(MatcherJob, job.id)
		assert db_job is not None

	@pytest.mark.asyncio
	async def test_start_ocr_phase_creates_ocr_job(
		self,
		session,
		sample_campaign,
		sample_crops,
		temp_storage_dir,
		mock_ocr_service,
	):
		"""Should start OCR phase and update MatcherJob status."""
		orchestrator = JobOrchestrator(
			session=session,
			ocr_service=mock_ocr_service,
			matching_service=AsyncMock(),
			storage_base=temp_storage_dir,
		)

		matcher_job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		updated_job = await orchestrator.start_ocr_phase(
			job_id=matcher_job.id,
			crops=sample_crops,
			ocr_client=AsyncMock(),
			campaign_id=str(sample_campaign.id),
			task_id="test-task",
		)

		assert updated_job is not None
		assert updated_job.id == matcher_job.id

		db_matcher = session.get(MatcherJob, matcher_job.id)
		assert db_matcher.current_status == JobStatus.OCR_STARTED


class TestJobStateTransitions:
	"""Tests for job state machine transitions."""

	@pytest.fixture
	def temp_storage_dir(self):
		"""Create temporary storage directory."""
		with TemporaryDirectory() as temp_dir:
			yield Path(temp_dir)

	@pytest.fixture
	def engine(self):
		"""Create in-memory SQLite engine for testing."""
		engine = create_engine("sqlite:///:memory:", echo=False)
		SQLModel.metadata.create_all(engine)
		yield engine
		engine.dispose()

	@pytest.fixture
	def session(self, engine):
		"""Create database session for each test."""
		with Session(engine) as session:
			yield session

	@pytest.fixture
	def sample_region(self, session):
		"""Create a sample region for testing."""
		region = Region(
			region_key="DC",
			region_name="Washington, DC",
			country_code="US",
		)
		session.add(region)
		session.commit()
		session.refresh(region)
		return region

	@pytest.fixture
	def sample_campaign(self, session, sample_region):
		"""Create a sample campaign for testing."""
		campaign = Campaign(
			unique_name="dc-2024",
			title="DC 2024",
			description="Test campaign",
			year="2024",
			region_id=sample_region.id,
		)
		session.add(campaign)
		session.commit()
		session.refresh(campaign)
		return campaign

	def test_matcher_job_status_transitions(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Should transition matcher job through status states."""
		orchestrator = JobOrchestrator(
			session=session,
			ocr_service=AsyncMock(),
			matching_service=AsyncMock(),
			storage_base=temp_storage_dir,
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)
		assert job.current_status == JobStatus.NOT_STARTED

		job.current_status = JobStatus.OCR_PENDING
		session.add(job)
		session.commit()
		session.refresh(job)
		assert job.current_status == JobStatus.OCR_PENDING

		job.current_status = JobStatus.OCR_COMPLETED
		session.add(job)
		session.commit()
		session.refresh(job)
		assert job.current_status == JobStatus.OCR_COMPLETED
