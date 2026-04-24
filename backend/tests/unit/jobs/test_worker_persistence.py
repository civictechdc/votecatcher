"""Unit tests for worker data persistence and polling contracts.

Tests that the worker persists critical identifiers at the right time,
preventing orphaned resources if the process crashes mid-operation.
Also tests that the batch OCR polling loop terminates for terminal statuses.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data.database.model.jobs import OcrJob
from app.data.database.model.petition_crop import PetitionCrop
from app.matching.match_repository import MatchingStatus
from app.ocr.ocr_manager import OcrJobStatus


class _AsyncIterator:
    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration from None


class TestBatchOcrPersistsProviderJobId:
    """After creating a remote batch job, the worker must persist the
    provider's job identifier to the database before polling begins.

    Without this, a worker crash after create_batch_job but before
    polling completes leaves an orphaned batch on the provider side
    with no recovery path.
    """

    @pytest.mark.asyncio
    async def test_provider_job_id_set_on_ocr_job_after_creation(self):
        """The ocr_job object must have provider_job_id set after create_batch_job."""
        from app.data.database.model.jobs import MatcherJob
        from app.jobs.worker import JobWorker

        with TemporaryDirectory() as tmpdir:
            crop_path = Path(tmpdir) / "crop_0.png"
            crop_path.write_bytes(b"fake_image")
            crop = MagicMock(spec=PetitionCrop)
            crop.id = 1
            crop.stored_path = str(crop_path)
            crop.scan_id = "scan-1"

            job = MagicMock(spec=MatcherJob)
            job.id = 1
            job.campaign_id = "camp-123"
            ocr_job = MagicMock(spec=OcrJob)
            ocr_job.id = 10

            mock_config = MagicMock()
            mock_config.provider = "openai"
            mock_config.api_key = "test-key"
            mock_config.model = "gpt-4o"

            mock_client = AsyncMock()
            mock_client.create_batch_job.return_value = OcrJobStatus(
                ocr_job_id="batch-abc-123",
                campaign_id="camp-123",
                task_id="task-123",
                ocr_provider_id="openai",
                task_status=MatchingStatus.COMPLETED,
            )

            from app.ocr.ocr_manager import OcrResult

            mock_client.get_ocr_results.return_value = _AsyncIterator(
                [
                    OcrResult(
                        job_id="batch-abc-123",
                        campaign_id="camp-123",
                        document_path="crop_0.png",
                        page_num=0,
                        row_num=0,
                        result_parts=[
                            {"field_name": "Name", "value": "Jane Doe"},
                            {"field_name": "Address", "value": "456 Elm St"},
                        ],
                    ),
                ]
            )

            worker = JobWorker()
            session = MagicMock()

            with (
                patch(
                    "app.jobs.worker.resolve_provider_config",
                    return_value=mock_config,
                ),
                patch(
                    "app.jobs.worker.OpenAiOcrClient",
                    return_value=mock_client,
                ),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                await worker._run_batch_ocr(session, job, ocr_job, [crop])

            assert ocr_job.provider_job_id == "batch-abc-123", (
                "provider_job_id must be set on ocr_job after batch creation"
            )

    @pytest.mark.asyncio
    async def test_provider_job_id_committed_before_polling(self):
        """session.commit must be called with provider_job_id set before any fetch_job_status."""
        from app.data.database.model.jobs import MatcherJob
        from app.jobs.worker import JobWorker

        with TemporaryDirectory() as tmpdir:
            crop_path = Path(tmpdir) / "crop_0.png"
            crop_path.write_bytes(b"fake_image")
            crop = MagicMock(spec=PetitionCrop)
            crop.id = 1
            crop.stored_path = str(crop_path)
            crop.scan_id = "scan-1"

            job = MagicMock(spec=MatcherJob)
            job.id = 1
            job.campaign_id = "camp-123"
            ocr_job = MagicMock(spec=OcrJob)
            ocr_job.id = 10

            mock_config = MagicMock()
            mock_config.provider = "openai"
            mock_config.api_key = "test-key"
            mock_config.model = "gpt-4o"

            call_order = []

            mock_client = AsyncMock()
            mock_client.create_batch_job.side_effect = lambda *a, **kw: (
                call_order.append("create"),
                OcrJobStatus(
                    ocr_job_id="batch-xyz",
                    campaign_id="camp-123",
                    task_id="task-123",
                    ocr_provider_id="openai",
                    task_status=MatchingStatus.OCR_IN_PROGRESS,
                ),
            )[1]
            mock_client.fetch_job_status.side_effect = lambda *a, **kw: (
                call_order.append("fetch"),
                OcrJobStatus(
                    ocr_job_id="batch-xyz",
                    campaign_id="camp-123",
                    task_id="task-123",
                    ocr_provider_id="openai",
                    task_status=MatchingStatus.COMPLETED,
                ),
            )[1]

            from app.ocr.ocr_manager import OcrResult

            mock_client.get_ocr_results.return_value = _AsyncIterator(
                [
                    OcrResult(
                        job_id="batch-xyz",
                        campaign_id="camp-123",
                        document_path="crop_0.png",
                        page_num=0,
                        row_num=0,
                        result_parts=[
                            {"field_name": "Name", "value": "Test User"},
                        ],
                    ),
                ]
            )

            worker = JobWorker()
            session = MagicMock()

            def track_commit(*args, **kwargs):
                call_order.append("commit")
                return MagicMock()

            session.commit = track_commit

            with (
                patch(
                    "app.jobs.worker.resolve_provider_config",
                    return_value=mock_config,
                ),
                patch(
                    "app.jobs.worker.OpenAiOcrClient",
                    return_value=mock_client,
                ),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                await worker._run_batch_ocr(session, job, ocr_job, [crop])

            create_idx = call_order.index("create")
            commit_indices = [i for i, c in enumerate(call_order) if c == "commit"]
            fetch_indices = [i for i, c in enumerate(call_order) if c == "fetch"]

            assert len(commit_indices) > 0, "session.commit must be called after batch creation"
            first_commit = commit_indices[0]
            assert create_idx < first_commit, "create must happen before commit"
            assert first_commit < (fetch_indices[0] if fetch_indices else float("inf")), (
                "provider_job_id must be committed before polling starts"
            )


class TestBatchOcrPollingTermination:
    """The batch OCR polling loop must stop as soon as a terminal status is observed.

    Previously, OCR_COMPLETED was not classified as terminal, causing the
    worker to poll for up to 30 minutes even after OCR finished successfully.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "terminal_status",
        [
            MatchingStatus.OCR_COMPLETED,
            MatchingStatus.COMPLETED,
            MatchingStatus.OCR_FAILED,
            MatchingStatus.OCR_TIMED_OUT,
            MatchingStatus.OCR_CANCELLED,
        ],
    )
    async def test_polling_stops_on_terminal_status(self, terminal_status):
        """When fetch_job_status returns a terminal status, polling must not continue.

        If the first fetch returns a terminal status, the loop should exit
        without calling fetch_job_status again.
        """
        from app.data.database.model.jobs import MatcherJob
        from app.jobs.worker import JobWorker
        from app.ocr.ocr_manager import OcrResult

        with TemporaryDirectory() as tmpdir:
            crop_path = Path(tmpdir) / "crop_0.png"
            crop_path.write_bytes(b"fake_image")
            crop = MagicMock(spec=PetitionCrop)
            crop.id = 1
            crop.stored_path = str(crop_path)
            crop.scan_id = "scan-1"

            job = MagicMock(spec=MatcherJob)
            job.id = 1
            job.campaign_id = "camp-123"
            ocr_job = MagicMock(spec=OcrJob)
            ocr_job.id = 10

            mock_config = MagicMock()
            mock_config.provider = "openai"
            mock_config.api_key = "test-key"
            mock_config.model = "gpt-4o"

            mock_client = AsyncMock()
            mock_client.create_batch_job.return_value = OcrJobStatus(
                ocr_job_id="batch-term",
                campaign_id="camp-123",
                task_id="task-123",
                ocr_provider_id="openai",
                task_status=MatchingStatus.OCR_IN_PROGRESS,
            )
            mock_client.fetch_job_status.return_value = OcrJobStatus(
                ocr_job_id="batch-term",
                campaign_id="camp-123",
                task_id="task-123",
                ocr_provider_id="openai",
                task_status=terminal_status,
            )

            has_results = terminal_status in {
                MatchingStatus.OCR_COMPLETED,
                MatchingStatus.COMPLETED,
            }
            if has_results:
                mock_client.get_ocr_results.return_value = _AsyncIterator(
                    [
                        OcrResult(
                            job_id="batch-term",
                            campaign_id="camp-123",
                            document_path="crop_0.png",
                            page_num=0,
                            row_num=0,
                            result_parts=[
                                {"field_name": "Name", "value": "Test User"},
                            ],
                        ),
                    ]
                )

            worker = JobWorker()
            session = MagicMock()

            with (
                patch(
                    "app.jobs.worker.resolve_provider_config",
                    return_value=mock_config,
                ),
                patch(
                    "app.jobs.worker.OpenAiOcrClient",
                    return_value=mock_client,
                ),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                await worker._run_batch_ocr(session, job, ocr_job, [crop])

            assert mock_client.fetch_job_status.call_count <= 1, (
                f"fetch_job_status called {mock_client.fetch_job_status.call_count} times "
                f"for {terminal_status.value}, expected at most 1"
            )
