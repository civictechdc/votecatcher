"""Integration tests for OCR service with database.

Tests cover OCR service integration with database for job creation,
status updates, and result storage. Mocks external LLM APIs.
"""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.user import User
from app.matching.match_repository import MatchingStatus
from app.ocr.ocr_manager import OcrJobStatus
from app.ocr.ocr_manager import OcrResult as OcrResultData
from app.ocr.ocr_service import OCRService


class TestOCRServiceIntegration:
	"""Integration tests for OCRService with database."""

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
		for i in range(3):
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
	def sample_matcher_job(self, session, sample_campaign):
		"""Create a sample matcher job."""
		job = MatcherJob(
			campaign_id=sample_campaign.id,
			current_status=JobStatus.NOT_STARTED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)
		return job

	@pytest.fixture
	def mock_ocr_client(self, sample_crops):
		"""Create a mock OCR client following OcrClient protocol."""
		client = AsyncMock()
		client.provider_id = "openai"

		client.create_batch_job = AsyncMock(
			return_value=OcrJobStatus(
				campaign_id="test-campaign-id",
				task_id="test-task-123",
				ocr_job_id="test-job-123",
				ocr_provider_id="openai",
				task_status=MatchingStatus.OCR_PENDING,
				created_at=datetime.now(UTC),
			)
		)

		client.fetch_job_status = AsyncMock(
			return_value=OcrJobStatus(
				campaign_id="test-campaign-id",
				task_id="test-task-123",
				ocr_job_id="test-job-123",
				ocr_provider_id="openai",
				task_status=MatchingStatus.OCR_COMPLETED,
				created_at=datetime.now(UTC),
			)
		)

		crop_paths = [crop.stored_path for crop in sample_crops]

		async def mock_get_ocr_results(job_id):
			for i, path in enumerate(crop_paths[:2]):
				yield OcrResultData(
					job_id=job_id,
					campaign_id="test-campaign-id",
					document_path=path,
					page_num=1,
					row_num=0,
					result_parts=[
						{"field_name": "name", "value": f"Test Name {i}"},
						{"field_name": "address", "value": f"{i + 1}23 Test St"},
					],
				)

		client.get_ocr_results = mock_get_ocr_results
		return client

	@pytest.mark.asyncio
	async def test_encode_crops_with_files(
		self, session, sample_crops, sample_campaign, temp_storage_dir
	):
		"""Should encode crops to base64 and return metadata."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		encoded = await service.encode_crops(
			crops=sample_crops,
			campaign_id=str(sample_campaign.id),
		)

		assert len(encoded) == 3
		for item in encoded:
			assert item.encoded_page is not None
			assert item.image_path is not None

	@pytest.mark.asyncio
	async def test_create_ocr_job_stores_in_db(
		self,
		session,
		sample_crops,
		sample_matcher_job,
		sample_campaign,
		temp_storage_dir,
		mock_ocr_client,
	):
		"""Should create OCR job in database."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = await service.create_ocr_job(
			matcher_job_id=sample_matcher_job.id,
			crops=sample_crops,
			ocr_client=mock_ocr_client,
			campaign_id=str(sample_campaign.id),
			task_id="test-task-123",
		)

		assert ocr_job is not None
		assert ocr_job.matcher_job_id == sample_matcher_job.id
		assert ocr_job.provider_job_id == "test-job-123"

		db_job = session.get(OcrJob, ocr_job.id)
		assert db_job is not None
		assert db_job.status == JobStatus.OCR_PENDING

	@pytest.mark.asyncio
	async def test_poll_job_status_updates_db(
		self,
		session,
		sample_crops,
		sample_matcher_job,
		sample_campaign,
		temp_storage_dir,
		mock_ocr_client,
	):
		"""Should poll job status and update database."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = await service.create_ocr_job(
			matcher_job_id=sample_matcher_job.id,
			crops=sample_crops,
			ocr_client=mock_ocr_client,
			campaign_id=str(sample_campaign.id),
			task_id="test-task-123",
		)

		updated_job = await service.poll_job_status(
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
		)

		assert updated_job.status == JobStatus.OCR_COMPLETED

	@pytest.mark.asyncio
	async def test_retrieve_results_stores_in_db(
		self,
		session,
		sample_crops,
		sample_matcher_job,
		sample_campaign,
		temp_storage_dir,
		mock_ocr_client,
	):
		"""Should retrieve OCR results and store in database."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = await service.create_ocr_job(
			matcher_job_id=sample_matcher_job.id,
			crops=sample_crops,
			ocr_client=mock_ocr_client,
			campaign_id=str(sample_campaign.id),
			task_id="test-task-123",
		)

		results = await service.retrieve_and_store_results(
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
			crops=sample_crops,
		)

		assert len(results) >= 1

		db_results = session.exec(
			select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id)
		).all()
		assert len(db_results) >= 1


class TestOCRServiceErrorHandling:
	"""Integration tests for OCR service error handling."""

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

	@pytest.mark.asyncio
	async def test_encode_crops_skips_missing_files(
		self, session, sample_crops, sample_campaign, temp_storage_dir
	):
		"""Should skip crops with missing files."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		sample_crops[0].stored_path = "/nonexistent/crop.png"
		session.add(sample_crops[0])
		session.commit()

		encoded = await service.encode_crops(
			crops=sample_crops,
			campaign_id=str(sample_campaign.id),
		)

		assert len(encoded) == 1

	@pytest.mark.asyncio
	async def test_create_ocr_job_raises_on_empty_crops(
		self, session, sample_campaign, temp_storage_dir
	):
		"""Should raise ValueError when no crops provided."""
		service = OCRService(session=session, storage_base=temp_storage_dir)
		mock_client = AsyncMock()
		mock_client.provider_id = "test"

		with pytest.raises(ValueError, match="No crops provided"):
			await service.create_ocr_job(
				matcher_job_id=1,
				crops=[],
				ocr_client=mock_client,
				campaign_id=str(sample_campaign.id),
				task_id="test-task",
			)
