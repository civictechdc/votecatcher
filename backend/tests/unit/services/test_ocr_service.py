"""Unit tests for OCRService.

Tests cover batch OCR job submission, status polling, and result retrieval.
Follows TDD approach aligned with SPEC.md §3.2 and §3.3.
"""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

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


class TestOCRService:
	"""Test suite for OCRService batch processing operations."""

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
	def sample_matcher_job(self, session, sample_campaign):
		"""Create a sample matcher job."""
		job = MatcherJob(
			id=1,
			campaign_id=sample_campaign.id,
			current_status=JobStatus.NOT_STARTED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)
		return job

	@pytest.fixture
	def mock_ocr_client(self):
		"""Create a mock OCR client."""
		client = AsyncMock()
		client.provider_id = "open_ai"
		return client

	@pytest.mark.asyncio
	async def test_encode_crops_to_base64(
		self, session, sample_petition_crops, temp_storage_dir
	):
		"""Test encoding petition crops to base64 images."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		encoded_pages = await service.encode_crops(
			crops=sample_petition_crops,
			campaign_id="dc-2024",
		)

		assert len(encoded_pages) == 3
		assert all(hasattr(page, "encoded_page") for page in encoded_pages)

	@pytest.mark.asyncio
	async def test_poll_job_status_pending(
		self, session, sample_matcher_job, mock_ocr_client, temp_storage_dir
	):
		"""Test polling OCR job status when still pending."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=sample_matcher_job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_PENDING,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_ocr_client.fetch_job_status.return_value = OcrJobStatus(
			ocr_job_id="batch-123",
			campaign_id="dc-2024",
			task_id="task-456",
			ocr_provider_id="open_ai",
			ocr_model="gpt-4-vision",
			task_status=MatchingStatus.OCR_IN_PROGRESS,
			created_at=datetime.now(UTC),
		)

		status = await service.poll_job_status(
			ocr_job_id=ocr_job.id, ocr_client=mock_ocr_client
		)

		assert status.status == JobStatus.OCR_STARTED

	@pytest.mark.asyncio
	async def test_poll_job_status_completed(
		self, session, sample_matcher_job, mock_ocr_client, temp_storage_dir
	):
		"""Test polling OCR job status when completed."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=sample_matcher_job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_PENDING,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_ocr_client.fetch_job_status.return_value = OcrJobStatus(
			ocr_job_id="batch-123",
			campaign_id="dc-2024",
			task_id="task-456",
			ocr_provider_id="open_ai",
			ocr_model="gpt-4-vision",
			task_status=MatchingStatus.OCR_COMPLETED,
			created_at=datetime.now(UTC),
			ended_at=datetime.now(UTC),
		)

		status = await service.poll_job_status(
			ocr_job_id=ocr_job.id, ocr_client=mock_ocr_client
		)

		assert status.status == JobStatus.OCR_COMPLETED
		assert status.ended_on is not None

	@pytest.mark.asyncio
	async def test_retrieve_and_store_results(
		self,
		session,
		sample_petition_crops,
		sample_matcher_job,
		mock_ocr_client,
		temp_storage_dir,
	):
		"""Test retrieving OCR results and storing in database."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=sample_matcher_job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_COMPLETED,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_results = []
		for i in range(len(sample_petition_crops)):
			mock_results.append(
				OcrResultData(
					job_id="batch-123",
					campaign_id="dc-2024",
					document_path=sample_petition_crops[i].stored_path,
					page_num=1,
					row_num=i,
					result_parts=[
						{"field_name": "Name", "value": f"Test Name {i}"},
						{"field_name": "Address", "value": f"123 Test St {i}"},
					],
				)
			)

		async def mock_get_results(job_id):
			for result in mock_results:
				yield result

		mock_ocr_client.get_ocr_results = mock_get_results

		results = await service.retrieve_and_store_results(
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
			crops=sample_petition_crops,
		)

		assert len(results) == 3
		assert all(isinstance(r, OcrResult) for r in results)
		assert all(r.ocr_job_id == ocr_job.id for r in results)
		assert all(hasattr(r, "extracted_text") for r in results)

	@pytest.mark.asyncio
	async def test_partial_failure_handling(
		self,
		session,
		sample_petition_crops,
		sample_matcher_job,
		mock_ocr_client,
		temp_storage_dir,
	):
		"""Test handling partial failures during result retrieval."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=sample_matcher_job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_COMPLETED,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_results = [
			OcrResultData(
				job_id="batch-123",
				campaign_id="dc-2024",
				document_path=sample_petition_crops[0].stored_path,
				page_num=1,
				row_num=0,
				result_parts=[
					{"field_name": "Name", "value": "Valid Name"},
					{"field_name": "Address", "value": "123 Valid St"},
				],
			),
			OcrResultData(
				job_id="batch-123",
				campaign_id="dc-2024",
				document_path=sample_petition_crops[1].stored_path,
				page_num=1,
				row_num=1,
				result_parts=[
					{"field_name": "Name", "value": "Another Valid Name"},
					{"field_name": "Address", "value": "456 Valid St"},
				],
			),
		]

		async def mock_get_results(job_id):
			for result in mock_results:
				yield result

		mock_ocr_client.get_ocr_results = mock_get_results

		results = await service.retrieve_and_store_results(
			ocr_job_id=ocr_job.id,
			ocr_client=mock_ocr_client,
			crops=sample_petition_crops,
		)

		assert len(results) == 2
		assert all(r.ocr_job_id == ocr_job.id for r in results)

	@pytest.mark.asyncio
	async def test_ocr_job_failure_status(
		self, session, sample_matcher_job, mock_ocr_client, temp_storage_dir
	):
		"""Test handling OCR job failure status."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		ocr_job = OcrJob(
			id=1,
			matcher_job_id=sample_matcher_job.id,
			provider_job_id="batch-123",
			status=JobStatus.OCR_PENDING,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		mock_ocr_client.fetch_job_status.return_value = OcrJobStatus(
			ocr_job_id="batch-123",
			campaign_id="dc-2024",
			task_id="task-456",
			ocr_provider_id="open_ai",
			ocr_model="gpt-4-vision",
			task_status=MatchingStatus.OCR_FAILED,
			created_at=datetime.now(UTC),
			ended_at=datetime.now(UTC),
			failure_message="API quota exceeded",
		)

		status = await service.poll_job_status(
			ocr_job_id=ocr_job.id, ocr_client=mock_ocr_client
		)

		assert status.status == JobStatus.OCR_FAILED
		assert status.error_data is not None
		assert "API quota exceeded" in status.error_data.get("message", "")

	@pytest.mark.asyncio
	async def test_encode_crops_with_missing_file(
		self, session, sample_petition_scan, temp_storage_dir
	):
		"""Test handling missing crop files during encoding."""
		service = OCRService(session=session, storage_base=temp_storage_dir)

		crops = []
		for i in range(3):
			crop = PetitionCrop(
				scan_id=sample_petition_scan.id,
				crop_index=i,
				stored_path=f"/nonexistent/crop_{i}.png",
				crop_coordinates={"top": 0.0, "bottom": 0.5},
				page_number=1,
			)
			session.add(crop)
			crops.append(crop)
		session.commit()

		encoded_pages = await service.encode_crops(
			crops=crops,
			campaign_id="dc-2024",
		)

		assert len(encoded_pages) == 0
