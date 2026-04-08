"""Unit tests for OpenAI OCR client."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai.types.batch import Batch

from app.matching.match_repository import MatchingStatus
from app.ocr.clients.open_ai import STATUS_MAPPING, OpenAiOcrClient
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_client_factory import ProviderConfig
from app.ocr.ocr_manager import OcrRequest


@pytest.fixture
def mock_config():
    """Create mock OpenAI configuration."""
    return ProviderConfig(
        provider="openai",
        api_key="test-api-key",
        model="gpt-4o",
    )


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    return tmp_path / "ocr_output"


@pytest.fixture
def openai_client(mock_config, output_dir):
    """Create OpenAI OCR client instance."""
    return OpenAiOcrClient(config=mock_config, output_dir=output_dir)


@pytest.fixture
def mock_batch_response():
    """Create mock batch response from OpenAI API."""
    batch = MagicMock(spec=Batch)
    batch.id = "batch-123"
    batch.status = "in_progress"
    batch.model = "gpt-4o"
    batch.created_at = int(datetime.now(UTC).timestamp())
    batch.in_progress_at = int(datetime.now(UTC).timestamp())
    batch.completed_at = None
    batch.cancelled_at = None
    batch.expired_at = None
    batch.output_file_id = "file-output-123"
    batch.error_file_id = None
    batch.errors = None
    batch.metadata = {
        "campaign_id": "campaign-1",
        "task_id": "task-1",
        "page_count": "2",
    }
    return batch


@pytest.fixture
def sample_ocr_request():
    """Create sample OCR request."""
    return OcrRequest(
        campaign_id="campaign-1",
        provider_id="open_ai",
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
            EncodedPetitionPage(
                encoded_page="base64encoded2",
                page_num=2,
                petition_file_name="petition1.pdf",
                image_path="/tmp/page2.jpg",
                petition_file_page_total=2,
                scan_id="scan-1",
            ),
        ],
    )


class TestOpenAiOcrClientInit:
    """Tests for OpenAiOcrClient initialization."""

    def test_client_initialization(self, mock_config, output_dir):
        """Client should initialize with config and output directory."""
        client = OpenAiOcrClient(config=mock_config, output_dir=output_dir)

        assert client.config == mock_config
        assert client.parent_dir == output_dir
        assert client.client is not None

    def test_provider_id(self, openai_client):
        """Provider ID should be 'open_ai'."""
        assert openai_client.provider_id == "open_ai"


class TestStatusMapping:
    """Tests for status mapping between OpenAI and internal status."""

    def test_validating_maps_to_not_started(self):
        """Validating status should map to NOT_STARTED."""
        assert STATUS_MAPPING["validating"] == MatchingStatus.NOT_STARTED

    def test_failed_maps_to_ocr_failed(self):
        """Failed status should map to OCR_FAILED."""
        assert STATUS_MAPPING["failed"] == MatchingStatus.OCR_FAILED

    def test_in_progress_maps_to_ocr_in_progress(self):
        """In progress status should map to OCR_IN_PROGRESS."""
        assert STATUS_MAPPING["in_progress"] == MatchingStatus.OCR_IN_PROGRESS

    def test_completed_maps_to_ocr_completed(self):
        """Completed status should map to OCR_COMPLETED."""
        assert STATUS_MAPPING["completed"] == MatchingStatus.OCR_COMPLETED

    def test_expired_maps_to_ocr_timed_out(self):
        """Expired status should map to OCR_TIMED_OUT."""
        assert STATUS_MAPPING["expired"] == MatchingStatus.OCR_TIMED_OUT

    def test_cancelled_maps_to_ocr_cancelled(self):
        """Cancelled status should map to OCR_CANCELLED."""
        assert STATUS_MAPPING["cancelled"] == MatchingStatus.OCR_CANCELLED


class TestCreateBatchJob:
    """Tests for creating batch jobs."""

    @pytest.mark.asyncio
    async def test_create_batch_job_success(
        self, openai_client, sample_ocr_request, mock_batch_response
    ):
        """Should create batch job successfully."""
        with (
            patch.object(
                openai_client.client.files, "create", new_callable=AsyncMock
            ) as mock_file_create,
            patch.object(
                openai_client.client.batches, "create", new_callable=AsyncMock
            ) as mock_batch_create,
        ):
            mock_file_create.return_value = MagicMock(id="file-123")
            mock_batch_create.return_value = mock_batch_response

            result = await openai_client.create_batch_job(sample_ocr_request)

            assert result.ocr_job_id == "batch-123"
            assert result.campaign_id == "campaign-1"
            assert result.ocr_provider_id == "open_ai"
            assert result.task_status == MatchingStatus.OCR_IN_PROGRESS
            assert result.task_id == "task-1"

    @pytest.mark.asyncio
    async def test_create_batch_job_creates_request_file(
        self, openai_client, sample_ocr_request, mock_batch_response
    ):
        """Should create JSONL request file."""
        with (
            patch.object(
                openai_client.client.files, "create", new_callable=AsyncMock
            ) as mock_file_create,
            patch.object(
                openai_client.client.batches, "create", new_callable=AsyncMock
            ) as mock_batch_create,
        ):
            mock_file_create.return_value = MagicMock(id="file-123")
            mock_batch_create.return_value = mock_batch_response

            await openai_client.create_batch_job(sample_ocr_request)

            mock_file_create.assert_called_once()
            call_kwargs = mock_file_create.call_args
            assert "file" in call_kwargs[1]
            assert "purpose" in call_kwargs[1]
            assert call_kwargs[1]["purpose"] == "batch"

    @pytest.mark.asyncio
    async def test_create_batch_job_with_failure(
        self, openai_client, sample_ocr_request
    ):
        """Should handle batch job creation failure."""
        failed_batch = MagicMock(spec=Batch)
        failed_batch.id = "batch-failed"
        failed_batch.status = "failed"
        failed_batch.model = "gpt-4o"
        failed_batch.created_at = int(datetime.now(UTC).timestamp())
        failed_batch.output_file_id = None
        failed_batch.error_file_id = "file-error-123"
        failed_batch.errors = MagicMock(
            data=[MagicMock(message="Invalid request format")]
        )
        failed_batch.metadata = {
            "campaign_id": "campaign-1",
            "task_id": "task-1",
            "page_count": "2",
        }

        with (
            patch.object(
                openai_client.client.files, "create", new_callable=AsyncMock
            ) as mock_file_create,
            patch.object(
                openai_client.client.batches, "create", new_callable=AsyncMock
            ) as mock_batch_create,
        ):
            mock_file_create.return_value = MagicMock(id="file-123")
            mock_batch_create.return_value = failed_batch

            result = await openai_client.create_batch_job(sample_ocr_request)

            assert result.task_status == MatchingStatus.OCR_FAILED
            assert result.failure_message is not None
            assert "Invalid request format" in result.failure_message


class TestFetchJobStatus:
    """Tests for fetching job status."""

    @pytest.mark.asyncio
    async def test_fetch_job_status_success(self, openai_client, mock_batch_response):
        """Should fetch job status successfully."""
        with patch.object(
            openai_client.client.batches, "retrieve", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = mock_batch_response

            result = await openai_client.fetch_job_status("batch-123")

            assert result.ocr_job_id == "batch-123"
            assert result.campaign_id == "campaign-1"
            assert result.task_status == MatchingStatus.OCR_IN_PROGRESS

    @pytest.mark.asyncio
    async def test_fetch_job_status_completed(self, openai_client):
        """Should handle completed job status."""
        completed_batch = MagicMock(spec=Batch)
        completed_batch.id = "batch-123"
        completed_batch.status = "completed"
        completed_batch.model = "gpt-4o"
        completed_batch.created_at = int(datetime.now(UTC).timestamp())
        completed_batch.in_progress_at = int(datetime.now(UTC).timestamp())
        completed_batch.completed_at = int(datetime.now(UTC).timestamp())
        completed_batch.cancelled_at = None
        completed_batch.expired_at = None
        completed_batch.metadata = {
            "campaign_id": "campaign-1",
            "task_id": "task-1",
        }

        with patch.object(
            openai_client.client.batches, "retrieve", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = completed_batch

            result = await openai_client.fetch_job_status("batch-123")

            assert result.task_status == MatchingStatus.OCR_COMPLETED
            assert result.ended_at is not None


class TestGetOcrResults:
    """Tests for retrieving OCR results."""

    @pytest.mark.asyncio
    async def test_get_ocr_results_success(self, openai_client, tmp_path):
        """Should retrieve OCR results successfully."""
        batch = MagicMock(spec=Batch)
        batch.id = "batch-123"
        batch.status = "completed"
        batch.metadata = {"campaign_id": "campaign-1"}
        batch.output_file_id = "file-output-123"
        batch.created_at = int(datetime.now(UTC).timestamp())

        result_jsonl = json.dumps(
            {
                "custom_id": (
                    "cmpgnid-campaign-1__file-p1.pdf__page-1__total-2__batch-0"
                ),
                "response": {
                    "body": {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "data": [
                                                {
                                                    "Name": "John Doe",
                                                    "Address": "123 Main St",
                                                    "Date": "2024-01-15",
                                                    "Ward": 1,
                                                }
                                            ]
                                        }
                                    )
                                }
                            }
                        ]
                    }
                },
            }
        )

        with (
            patch.object(
                openai_client.client.batches, "retrieve", new_callable=AsyncMock
            ) as mock_retrieve,
            patch.object(
                openai_client.client.files, "content", new_callable=AsyncMock
            ) as mock_content,
        ):
            mock_retrieve.return_value = batch
            mock_content.return_value = MagicMock(content=result_jsonl.encode("utf-8"))

            results = []
            async for result in openai_client.get_ocr_results("batch-123"):
                results.append(result)

            assert len(results) == 1
            assert results[0].campaign_id == "campaign-1"
            assert results[0].page_num == 1
            assert len(results[0].result_parts) == 4


class TestCustomIdFormat:
    """Tests for custom ID format parsing."""

    def test_create_custom_id_format(self, openai_client):
        """Should create valid custom ID format."""
        from app.ocr.ocr_manager import OcrMessageData

        payload = OcrMessageData(
            role="user",
            messages=[{"type": "text", "text": "test"}],
            page=1,
            file_name="petition.pdf",
        )

        custom_id = openai_client._create_custom_id_format(
            campaign_id="campaign-1",
            payload=payload,
            batch_idx=0,
            page_total=10,
        )

        assert "campaign-1" in custom_id
        assert "petition.pdf" in custom_id
        assert "__page-1__" in custom_id
        assert "__total-10__" in custom_id
        assert "__batch-0" in custom_id

    def test_extract_custom_id_parts(self, openai_client):
        """Should extract parts from custom ID."""
        custom_id = "cmpgnid-campaign-1__file-petition.pdf__page-2__total-10__batch-0"
        response_line = json.dumps({"custom_id": custom_id})

        campaign_id, file_name, page_num, page_total, entry_number = (
            openai_client._extract_custom_id_parts(response_line)
        )

        assert campaign_id == "campaign-1"
        assert file_name == "petition.pdf"
        assert page_num == 2
        assert page_total == 10
        assert entry_number == 0


class TestOcrClientProtocol:
    """Tests to verify OpenAI client implements OcrClient protocol."""

    def test_implements_create_batch_job(self, openai_client):
        """Should implement create_batch_job method."""
        assert hasattr(openai_client, "create_batch_job")
        assert callable(openai_client.create_batch_job)

    def test_implements_fetch_job_status(self, openai_client):
        """Should implement fetch_job_status method."""
        assert hasattr(openai_client, "fetch_job_status")
        assert callable(openai_client.fetch_job_status)

    def test_implements_get_ocr_results(self, openai_client):
        """Should implement get_ocr_results method."""
        assert hasattr(openai_client, "get_ocr_results")
        assert callable(openai_client.get_ocr_results)

    def test_implements_provider_id_property(self, openai_client):
        """Should implement provider_id property."""
        assert hasattr(openai_client, "provider_id")
        assert isinstance(openai_client.provider_id, str)
