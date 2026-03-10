"""Unit tests for JobOrchestrator.

Tests cover job state machine transitions, OCR → Matching coordination,
and error handling. Follows TDD approach aligned with SPEC.md §3.3.
"""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, OcrJob
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.user import User
from app.matching.match_repository import MatchingStatus
from app.ocr.ocr_manager import OcrJobStatus


class TestJobOrchestrator:
	"""Test suite for JobOrchestrator state machine operations."""

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
		return engine

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
	def sample_petition_crops(self, session, sample_petition_scan, temp_storage_dir):
		"""Create sample petition crops with actual files."""
		crops = []
		for i in range(3):
			crop_path = temp_storage_dir / f"crop_{i}.png"
			crop_path.parent.mkdir(parents=True, exist_ok=True)
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
	def mock_ocr_service(self):
		"""Create a mock OCR service."""
		service = AsyncMock()
		return service

	@pytest.fixture
	def mock_matching_service(self):
		"""Create a mock matching service."""
		service = AsyncMock()
		return service

	def test_create_matcher_job(self, session, sample_campaign):
		"""Test creating a new matcher job with NOT_STARTED status."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session)

		job = orchestrator.create_matcher_job(
			campaign_id=sample_campaign.id,
		)

		assert job.id is not None
		assert job.campaign_id == sample_campaign.id
		assert job.current_status == JobStatus.NOT_STARTED
		assert job.started_on is None
		assert job.ended_on is None

	@pytest.mark.asyncio
	async def test_start_ocr_phase_success(
		self,
		session,
		sample_campaign,
		sample_petition_crops,
		mock_ocr_service,
		temp_storage_dir,
	):
		"""Test starting OCR phase transitions state correctly."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(
			session, ocr_service=mock_ocr_service, storage_base=temp_storage_dir
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		mock_ocr_job = OcrJob(
			id=1,
			matcher_job_id=job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_STARTED,
			started_on=datetime.now(UTC),
		)
		mock_ocr_service.create_ocr_job.return_value = mock_ocr_job

		updated_job = await orchestrator.start_ocr_phase(
			job_id=job.id,
			crops=sample_petition_crops,
			ocr_client=AsyncMock(),
			campaign_id=str(sample_campaign.id),
			task_id="task-123",
		)

		assert updated_job.current_status == JobStatus.OCR_STARTED
		assert updated_job.started_on is not None
		mock_ocr_service.create_ocr_job.assert_called_once()

	@pytest.mark.asyncio
	async def test_handle_ocr_completion(
		self,
		session,
		sample_campaign,
		sample_petition_crops,
		mock_ocr_service,
		temp_storage_dir,
	):
		"""Test OCR completion triggers transition to OCR_COMPLETED."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(
			session, ocr_service=mock_ocr_service, storage_base=temp_storage_dir
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_COMPLETED,
			started_on=datetime.now(UTC),
			ended_on=datetime.now(UTC),
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_ocr_results = [
			OcrResult(
				crop_id=crop.id,
				ocr_job_id=ocr_job.id,
				extracted_text={"name": "John Doe"},
			)
			for crop in sample_petition_crops[:2]
		]
		mock_ocr_service.retrieve_and_store_results.return_value = mock_ocr_results
		mock_ocr_service.poll_job_status.return_value = ocr_job

		mock_ocr_client = AsyncMock()
		mock_ocr_client.fetch_job_status.return_value = OcrJobStatus(
			ocr_job_id="batch-123",
			campaign_id=str(sample_campaign.id),
			task_id="task-123",
			ocr_provider_id="openai",
			task_status=MatchingStatus.OCR_COMPLETED,
			created_at=datetime.now(UTC),
			updated_at=datetime.now(UTC),
			ended_at=datetime.now(UTC),
		)

		updated_job = await orchestrator.check_ocr_completion(
			job_id=job.id,
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
			crops=sample_petition_crops,
		)

		assert updated_job.current_status == JobStatus.OCR_COMPLETED
		mock_ocr_service.retrieve_and_store_results.assert_called_once()

	@pytest.mark.asyncio
	async def test_start_matching_phase(
		self,
		session,
		sample_campaign,
		mock_matching_service,
		temp_storage_dir,
	):
		"""Test starting matching phase from OCR_COMPLETED state."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(
			session,
			matching_service=mock_matching_service,
			storage_base=temp_storage_dir,
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)
		job.current_status = JobStatus.OCR_COMPLETED
		session.commit()
		session.refresh(job)

		mock_matching_service.run_matching.return_value = {
			"processed": 10,
			"matched": 8,
			"unmatched": 2,
		}

		updated_job = await orchestrator.start_matching_phase(job_id=job.id)

		assert updated_job.current_status == JobStatus.MATCHING_COMPLETED
		assert updated_job.success_data["matched"] == 8
		mock_matching_service.run_matching.assert_called_once()

	@pytest.mark.asyncio
	async def test_handle_matching_completion(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Test matching completion transitions to MATCHING_COMPLETED."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session, storage_base=temp_storage_dir)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)
		job.current_status = JobStatus.MATCHING
		session.commit()
		session.refresh(job)

		updated_job = await orchestrator.complete_matching_phase(
			job_id=job.id,
			results={"processed": 10, "matched": 8, "unmatched": 2},
		)

		assert updated_job.current_status == JobStatus.MATCHING_COMPLETED
		assert updated_job.ended_on is not None
		assert updated_job.success_data["matched"] == 8

	@pytest.mark.asyncio
	async def test_handle_ocr_failure(
		self, session, sample_campaign, mock_ocr_service, temp_storage_dir
	):
		"""Test OCR failure transitions to OCR_FAILED state."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(
			session, ocr_service=mock_ocr_service, storage_base=temp_storage_dir
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_FAILED,
			error_data={"message": "API error"},
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		updated_job = await orchestrator.handle_ocr_failure(
			job_id=job.id, error_message="OCR processing failed"
		)

		assert updated_job.current_status == JobStatus.OCR_FAILED
		assert updated_job.ended_on is not None
		assert "OCR processing failed" in updated_job.error_data.get("message", "")

	@pytest.mark.asyncio
	async def test_handle_ocr_timeout(self, session, sample_campaign, temp_storage_dir):
		"""Test OCR timeout transitions to OCR_TIMEOUT state."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session, storage_base=temp_storage_dir)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)
		job.current_status = JobStatus.OCR_STARTED
		session.commit()
		session.refresh(job)

		updated_job = await orchestrator.handle_ocr_timeout(job_id=job.id)

		assert updated_job.current_status == JobStatus.OCR_TIMEOUT
		assert updated_job.ended_on is not None
		assert "timeout" in updated_job.error_data.get("message", "").lower()

	@pytest.mark.asyncio
	async def test_handle_matching_error(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Test matching error transitions to MATCHING_ERROR state."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session, storage_base=temp_storage_dir)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)
		job.current_status = JobStatus.MATCHING
		session.commit()
		session.refresh(job)

		updated_job = await orchestrator.handle_matching_error(
			job_id=job.id, error_message="Database connection failed"
		)

		assert updated_job.current_status == JobStatus.MATCHING_ERROR
		assert updated_job.ended_on is not None
		assert "Database connection failed" in updated_job.error_data.get("message", "")

	def test_get_job_status(self, session, sample_campaign):
		"""Test retrieving current job status."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		retrieved_job = orchestrator.get_job(job_id=job.id)

		assert retrieved_job is not None
		assert retrieved_job.id == job.id
		assert retrieved_job.current_status == JobStatus.NOT_STARTED

	@pytest.mark.asyncio
	async def test_partial_ocr_failure_continues_job(
		self,
		session,
		sample_campaign,
		sample_petition_crops,
		mock_ocr_service,
		temp_storage_dir,
	):
		"""Test partial OCR failures don't stop job progression."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(
			session, ocr_service=mock_ocr_service, storage_base=temp_storage_dir
		)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_COMPLETED,
			started_on=datetime.now(UTC),
			ended_on=datetime.now(UTC),
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_ocr_results = [
			OcrResult(
				crop_id=sample_petition_crops[0].id,
				ocr_job_id=ocr_job.id,
				extracted_text={"name": "John Doe"},
			)
		]
		mock_ocr_service.retrieve_and_store_results.return_value = mock_ocr_results
		mock_ocr_service.poll_job_status.return_value = ocr_job

		mock_ocr_client = AsyncMock()
		mock_ocr_client.fetch_job_status.return_value = OcrJobStatus(
			ocr_job_id="batch-123",
			campaign_id=str(sample_campaign.id),
			task_id="task-123",
			ocr_provider_id="openai",
			task_status=MatchingStatus.OCR_COMPLETED,
			created_at=datetime.now(UTC),
			updated_at=datetime.now(UTC),
			ended_at=datetime.now(UTC),
		)

		updated_job = await orchestrator.check_ocr_completion(
			job_id=job.id,
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
			crops=sample_petition_crops,
		)

		assert updated_job.current_status == JobStatus.OCR_COMPLETED
		assert len(mock_ocr_results) == 1

	def test_invalid_state_transition_raises_error(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Test invalid state transitions raise errors."""
		from app.jobs.job_orchestrator import JobOrchestrator

		orchestrator = JobOrchestrator(session, storage_base=temp_storage_dir)

		job = orchestrator.create_matcher_job(campaign_id=sample_campaign.id)

		with pytest.raises(ValueError, match="Cannot start matching"):
			import asyncio

			asyncio.run(orchestrator.start_matching_phase(job_id=job.id))
