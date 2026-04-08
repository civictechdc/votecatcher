"""Unit tests for Gemini OCR client."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_client_factory import ProviderConfig
from app.ocr.ocr_manager import OcrRequest


@pytest.fixture
def mock_config():
    """Create mock Gemini configuration."""
    return ProviderConfig(
        provider="gemini",
        api_key="test-gemini-api-key",
        model="gemini-1.5-flash",
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
        provider_id="gemini",
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


class TestGeminiOcrClientInit:
    """Tests for Gemini OCR client initialization."""

    def test_client_initialization(self, mock_config, output_dir):
        """Client should initialize with config and output directory."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)

        assert client.config == mock_config
        assert client.parent_dir == output_dir

    def test_provider_id(self, mock_config, output_dir):
        """Provider ID should be 'gemini'."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)
        assert client.provider_id == "gemini"


class TestGeminiCreateBatchJob:
    """Tests for creating Gemini batch jobs."""

    @pytest.mark.asyncio
    async def test_create_batch_job_success(
        self, mock_config, output_dir, sample_ocr_request
    ):
        """Should create batch job successfully."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)

        with patch("app.ocr.clients.gemini.genai") as mock_genai:
            mock_batch = MagicMock()
            mock_batch.name = "batch-gemini-123"
            mock_batch.state.name = "JOB_STATE_RUNNING"
            mock_batch.create_time = datetime.now(UTC)
            mock_batch.metadata = {"campaign_id": "campaign-1", "task_id": "task-1"}

            mock_client = MagicMock()
            mock_client.batches.create.return_value = mock_batch
            mock_genai.Client.return_value = mock_client

            result = await client.create_batch_job(sample_ocr_request)

            assert result.ocr_job_id == "batch-gemini-123"
            assert result.campaign_id == "campaign-1"
            assert result.ocr_provider_id == "gemini"

    @pytest.mark.asyncio
    async def test_create_batch_job_with_failure(
        self, mock_config, output_dir, sample_ocr_request
    ):
        """Should handle batch job creation failure."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)

        with patch("app.ocr.clients.gemini.genai") as mock_genai:
            mock_batch = MagicMock()
            mock_batch.name = "batch-gemini-failed"
            mock_batch.state.name = "JOB_STATE_FAILED"
            mock_batch.create_time = datetime.now(UTC)
            mock_batch.error = MagicMock(message="Invalid request")

            mock_client = MagicMock()
            mock_client.batches.create.return_value = mock_batch
            mock_genai.Client.return_value = mock_client

            result = await client.create_batch_job(sample_ocr_request)

            assert result.task_status == MatchingStatus.OCR_FAILED


class TestGeminiFetchJobStatus:
    """Tests for fetching Gemini job status."""

    @pytest.mark.asyncio
    async def test_fetch_job_status_running(self, mock_config, output_dir):
        """Should fetch running job status."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)

        with patch("app.ocr.clients.gemini.genai") as mock_genai:
            mock_batch = MagicMock()
            mock_batch.name = "batch-gemini-123"
            mock_batch.state.name = "JOB_STATE_RUNNING"
            mock_batch.create_time = datetime.now(UTC)
            mock_batch.metadata = {"campaign_id": "campaign-1", "task_id": "task-1"}

            mock_client = MagicMock()
            mock_client.batches.get.return_value = mock_batch
            mock_genai.Client.return_value = mock_client

            result = await client.fetch_job_status("batch-gemini-123")

            assert result.ocr_job_id == "batch-gemini-123"
            assert result.task_status == MatchingStatus.OCR_IN_PROGRESS

    @pytest.mark.asyncio
    async def test_fetch_job_status_completed(self, mock_config, output_dir):
        """Should fetch completed job status."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)

        with patch("app.ocr.clients.gemini.genai") as mock_genai:
            mock_batch = MagicMock()
            mock_batch.name = "batch-gemini-123"
            mock_batch.state.name = "JOB_STATE_SUCCEEDED"
            mock_batch.create_time = datetime.now(UTC)
            mock_batch.end_time = datetime.now(UTC)
            mock_batch.metadata = {"campaign_id": "campaign-1", "task_id": "task-1"}

            mock_client = MagicMock()
            mock_client.batches.get.return_value = mock_batch
            mock_genai.Client.return_value = mock_client

            result = await client.fetch_job_status("batch-gemini-123")

            assert result.task_status == MatchingStatus.OCR_COMPLETED


class TestGeminiOcrClientProtocol:
    """Tests to verify Gemini client implements OcrClient protocol."""

    def test_implements_create_batch_job(self, mock_config, output_dir):
        """Should implement create_batch_job method."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)
        assert hasattr(client, "create_batch_job")
        assert callable(client.create_batch_job)

    def test_implements_fetch_job_status(self, mock_config, output_dir):
        """Should implement fetch_job_status method."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)
        assert hasattr(client, "fetch_job_status")
        assert callable(client.fetch_job_status)

    def test_implements_get_ocr_results(self, mock_config, output_dir):
        """Should implement get_ocr_results method."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)
        assert hasattr(client, "get_ocr_results")
        assert callable(client.get_ocr_results)

    def test_implements_provider_id_property(self, mock_config, output_dir):
        """Should implement provider_id property."""
        from app.ocr.clients.gemini import GeminiOcrClient

        client = GeminiOcrClient(config=mock_config, output_dir=output_dir)
        assert hasattr(client, "provider_id")
        assert isinstance(client.provider_id, str)
