"""Tests for G7.7: worker.py delegates matching to MatchingService.

Verifies that _run_matching_phase uses MatchingService.match_ocr_result
instead of inline duplicate matching logic.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.schema import Campaign
from app.jobs.worker import JobWorker


@pytest.fixture
def worker():
    return JobWorker(settings=MagicMock(feature_simulation=True))


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.commit = MagicMock()
    session.add = MagicMock()
    session.get = MagicMock()
    return session


@pytest.fixture
def mock_job():
    job = MagicMock(spec=MatcherJob)
    job.id = 1
    job.campaign_id = MagicMock()
    job.current_status = JobStatus.OCR_COMPLETED
    return job


@pytest.fixture
def mock_ocr_job():
    ocr_job = MagicMock(spec=OcrJob)
    ocr_job.id = 10
    return ocr_job


class TestWorkerDelegatesToMatchingService:
    @pytest.mark.asyncio
    async def test_matching_phase_calls_matching_service(
        self, worker, mock_session, mock_job, mock_ocr_job
    ):
        ocr_result = MagicMock()
        ocr_result.id = 42
        ocr_result.extracted_text = {"name": "John Smith", "address": "123 Main St"}

        campaign = MagicMock(spec=Campaign)
        campaign.region_id = MagicMock()

        mock_session.exec.return_value.all.return_value = [ocr_result]
        mock_session.get.return_value = campaign

        with patch(
            "app.matching.matching_service.MatchingService"
        ) as MockMatchingService:
            mock_ms_instance = MockMatchingService.return_value
            mock_ms_instance.match_ocr_result.return_value = [
                {
                    "voter_id": 99,
                    "similarity_score": 0.9,
                    "confidence_level": MagicMock(value="HIGH"),
                    "field_scores": {"name": 0.9, "address": 0.9},
                }
            ]

            await worker._run_matching_phase(mock_session, mock_job, mock_ocr_job)

            MockMatchingService.assert_called_once_with(session=mock_session)
            mock_ms_instance.match_ocr_result.assert_called_once_with(
                ocr_text=ocr_result.extracted_text,
                region_id=campaign.region_id,
                top_n=5,
            )

    @pytest.mark.asyncio
    async def test_matching_phase_creates_match_results_from_service_output(
        self, worker, mock_session, mock_job, mock_ocr_job
    ):
        ocr_result = MagicMock()
        ocr_result.id = 42
        ocr_result.extracted_text = {"name": "Jane Doe", "address": "456 Oak Ave"}

        campaign = MagicMock(spec=Campaign)
        campaign.region_id = MagicMock()

        mock_session.exec.return_value.all.return_value = [ocr_result]
        mock_session.get.return_value = campaign

        match_data = {
            "voter_id": 7,
            "similarity_score": 0.75,
            "confidence_level": MagicMock(value="MEDIUM"),
            "field_scores": {"name": 0.8, "address": 0.7},
        }

        with patch(
            "app.matching.matching_service.MatchingService"
        ) as MockMatchingService:
            MockMatchingService.return_value.match_ocr_result.return_value = [
                match_data
            ]

            await worker._run_matching_phase(mock_session, mock_job, mock_ocr_job)

            mock_session.add.assert_called_once()
            added_match = mock_session.add.call_args[0][0]
            assert added_match.voter_id == match_data["voter_id"]
            assert added_match.similarity_score == match_data["similarity_score"]
            assert added_match.rank == 1
