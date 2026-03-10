"""Unit tests for Mistral OCR client."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_manager import OcrRequest
from app.settings import MistralAiConfig


@pytest.fixture
def mock_config():
	"""Create mock Mistral configuration."""
	return MistralAiConfig(
		api_key="test-mistral-api-key",
		model="mistral-large-latest",
	)


@pytest.fixture
def output_dir(tmp_path):
	"""Create temporary output directory."""
	return tmp_path / "ocr_output"


@pytest.fixture
def sample_ocr_request():
	"""Create sample OCR request."""
	return OcrRequest(
		campaign_id="campaign-1",
		provider_id="mistral",
		task_id="task-1",
		encoded_pages=[
			EncodedPetitionPage(
				encoded_page="base64encoded1",
				page_num=1,
				petition_file_name="petition1.pdf",
				image_path="/tmp/page1.jpg",
				petition_file_page_total=2,
				scan_id="scan-1",
			),
		],
	)


class TestMistralOcrClientInit:
	"""Tests for Mistral OCR client initialization."""

	def test_client_initialization(self, mock_config, output_dir):
		"""Client should initialize with config and output directory."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)

		assert client.config == mock_config
		assert client.parent_dir == output_dir

	def test_provider_id(self, mock_config, output_dir):
		"""Provider ID should be 'mistral'."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)
		assert client.provider_id == "mistral"


class TestMistralCreateBatchJob:
	"""Tests for creating Mistral batch jobs."""

	@pytest.mark.asyncio
	async def test_create_batch_job_success(
		self, mock_config, output_dir, sample_ocr_request
	):
		"""Should create batch job successfully."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)

		mock_file_response = MagicMock()
		mock_file_response.id = "file-mistral-123"

		mock_batch_response = MagicMock()
		mock_batch_response.id = "batch-mistral-123"
		mock_batch_response.status = "QUEUED"
		mock_batch_response.created_at = int(datetime.now(UTC).timestamp() * 1000)
		mock_batch_response.metadata = {
			"campaign_id": "campaign-1",
			"task_id": "task-1",
		}

		mock_mistral_client = MagicMock()
		mock_mistral_client.files.upload.return_value = mock_file_response
		mock_mistral_client.batch.jobs.create.return_value = mock_batch_response

		with patch.object(client, "_get_client", return_value=mock_mistral_client):
			result = await client.create_batch_job(sample_ocr_request)

		assert result.ocr_job_id == "batch-mistral-123"
		assert result.campaign_id == "campaign-1"
		assert result.ocr_provider_id == "mistral"

	@pytest.mark.asyncio
	async def test_create_batch_job_with_failure(
		self, mock_config, output_dir, sample_ocr_request
	):
		"""Should handle batch job creation failure."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)

		mock_batch_response = MagicMock()
		mock_batch_response.id = "batch-mistral-failed"
		mock_batch_response.status = "FAILED"
		mock_batch_response.created_at = int(datetime.now(UTC).timestamp() * 1000)
		mock_batch_response.errors = ["Invalid request"]
		mock_batch_response.metadata = {
			"campaign_id": "campaign-1",
			"task_id": "task-1",
		}

		mock_mistral_client = MagicMock()
		mock_mistral_client.files.upload.return_value = MagicMock(id="file-123")
		mock_mistral_client.batch.jobs.create.return_value = mock_batch_response

		with patch.object(client, "_get_client", return_value=mock_mistral_client):
			result = await client.create_batch_job(sample_ocr_request)

		assert result.task_status == MatchingStatus.OCR_FAILED


class TestMistralFetchJobStatus:
	"""Tests for fetching Mistral job status."""

	@pytest.mark.asyncio
	async def test_fetch_job_status_running(self, mock_config, output_dir):
		"""Should fetch running job status."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)

		mock_batch_response = MagicMock()
		mock_batch_response.id = "batch-mistral-123"
		mock_batch_response.status = "RUNNING"
		mock_batch_response.created_at = int(datetime.now(UTC).timestamp() * 1000)
		mock_batch_response.metadata = {
			"campaign_id": "campaign-1",
			"task_id": "task-1",
		}

		mock_mistral_client = MagicMock()
		mock_mistral_client.batch.jobs.get.return_value = mock_batch_response

		with patch.object(client, "_get_client", return_value=mock_mistral_client):
			result = await client.fetch_job_status("batch-mistral-123")

		assert result.ocr_job_id == "batch-mistral-123"
		assert result.task_status == MatchingStatus.OCR_IN_PROGRESS

	@pytest.mark.asyncio
	async def test_fetch_job_status_completed(self, mock_config, output_dir):
		"""Should fetch completed job status."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)

		mock_batch_response = MagicMock()
		mock_batch_response.id = "batch-mistral-123"
		mock_batch_response.status = "SUCCESS"
		mock_batch_response.created_at = int(datetime.now(UTC).timestamp() * 1000)
		mock_batch_response.completed_at = int(datetime.now(UTC).timestamp() * 1000)
		mock_batch_response.metadata = {
			"campaign_id": "campaign-1",
			"task_id": "task-1",
		}

		mock_mistral_client = MagicMock()
		mock_mistral_client.batch.jobs.get.return_value = mock_batch_response

		with patch.object(client, "_get_client", return_value=mock_mistral_client):
			result = await client.fetch_job_status("batch-mistral-123")

		assert result.task_status == MatchingStatus.OCR_COMPLETED


class TestMistralOcrClientProtocol:
	"""Tests to verify Mistral client implements OcrClient protocol."""

	def test_implements_create_batch_job(self, mock_config, output_dir):
		"""Should implement create_batch_job method."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)
		assert hasattr(client, "create_batch_job")
		assert callable(client.create_batch_job)

	def test_implements_fetch_job_status(self, mock_config, output_dir):
		"""Should implement fetch_job_status method."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)
		assert hasattr(client, "fetch_job_status")
		assert callable(client.fetch_job_status)

	def test_implements_get_ocr_results(self, mock_config, output_dir):
		"""Should implement get_ocr_results method."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)
		assert hasattr(client, "get_ocr_results")
		assert callable(client.get_ocr_results)

	def test_implements_provider_id_property(self, mock_config, output_dir):
		"""Should implement provider_id property."""
		from app.ocr.clients.mistral import MistralOcrClient

		client = MistralOcrClient(config=mock_config, output_dir=output_dir)
		assert hasattr(client, "provider_id")
		assert isinstance(client.provider_id, str)
