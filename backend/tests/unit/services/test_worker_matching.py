"""Tests for G7.7: worker.py delegates matching to MatchingService.

Verifies that _run_matching_phase uses MatchingService.match_ocr_result_with_spec
with spec-driven matching.
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
    async def test_matching_phase_calls_match_ocr_result_with_spec(
        self, worker, mock_session, mock_job, mock_ocr_job
    ):
        ocr_result = MagicMock()
        ocr_result.id = 42
        ocr_result.extracted_text = {"name": "John Smith", "address": "123 Main St"}

        campaign = MagicMock(spec=Campaign)
        campaign.region_id = MagicMock()
        campaign.region = MagicMock()
        campaign.region.region_key = "DC"

        mock_session.exec.return_value.all.return_value = [ocr_result]
        mock_session.get.return_value = campaign

        with (
            patch(
                "app.matching.matching_service.MatchingService"
            ) as MockMatchingService,
            patch("app.dependencies.get_field_spec_service") as mock_get_spec,
            patch("app.dependencies.get_matching_engine") as mock_get_engine,
        ):
            mock_ms_instance = MockMatchingService.return_value
            mock_ms_instance.match_ocr_result_with_spec.return_value = [
                {
                    "voter_id": 99,
                    "similarity_score": 0.9,
                    "confidence_level": MagicMock(value="HIGH"),
                    "field_scores": {"name": 0.9, "address": 0.9},
                }
            ]

            mock_spec_service = MagicMock()
            mock_spec = MagicMock()
            mock_spec_service.get_spec_by_key.return_value = mock_spec
            mock_get_spec.return_value = iter([mock_spec_service])
            mock_get_engine.return_value = MagicMock()

            await worker._run_matching_phase(mock_session, mock_job, mock_ocr_job)

            MockMatchingService.assert_called_once()
            call_kwargs = MockMatchingService.call_args.kwargs
            assert call_kwargs["session"] == mock_session
            assert "aggregator" in call_kwargs
            mock_ms_instance.match_ocr_result_with_spec.assert_called_once_with(
                spec=mock_spec,
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
        campaign.region = MagicMock()
        campaign.region.region_key = "DC"

        mock_session.exec.return_value.all.return_value = [ocr_result]
        mock_session.get.return_value = campaign

        match_data = {
            "voter_id": 7,
            "similarity_score": 0.75,
            "confidence_level": MagicMock(value="MEDIUM"),
            "field_scores": {"name": 0.8, "address": 0.7},
        }

        with (
            patch(
                "app.matching.matching_service.MatchingService"
            ) as MockMatchingService,
            patch("app.dependencies.get_field_spec_service") as mock_get_spec,
            patch("app.dependencies.get_matching_engine") as mock_get_engine,
        ):
            MockMatchingService.return_value.match_ocr_result_with_spec.return_value = [
                match_data
            ]

            mock_spec_service = MagicMock()
            mock_spec = MagicMock()
            mock_spec_service.get_spec_by_key.return_value = mock_spec
            mock_get_spec.return_value = iter([mock_spec_service])
            mock_get_engine.return_value = MagicMock()

            await worker._run_matching_phase(mock_session, mock_job, mock_ocr_job)

            mock_session.add.assert_called_once()
            added_match = mock_session.add.call_args[0][0]
            assert added_match.voter_id == match_data["voter_id"]
            assert added_match.similarity_score == match_data["similarity_score"]
            assert added_match.rank == 1
