"""BDD tests for Commit 7: Delete ocr/batching/ — Consolidate to ocr/clients/

Each test class maps to a task. Tests describe behavioural rules and invariants
that must hold after the migration. Follows TDD red-green-refactor.

Task 1: Migrate ocr/data/ocr_repository.py types
Task 2: Migrate worker.py:_run_batch_ocr()
Task 3: Migrate ocr_helper.py off batch_handler.py
Task 4: Delete ocr/batching/ directory
Task 5: Delete dead BatchOcrHandler from clients/batch_ocr_manager.py
"""

import inspect

import pytest

from app.matching.match_repository import MatchingStatus


class TestTask1OcrRepositoryTypes:
    """Task 1: ocr/data/ocr_repository.py uses MatchingStatus + OcrClient."""

    def test_update_ocr_job_status_type_is_matching_status(self):
        """UpdateOcrJob.status field must be MatchingStatus, not JobStatus."""
        from app.ocr.data.ocr_repository import UpdateOcrJob

        hints = inspect.get_annotations(UpdateOcrJob)
        assert hints["status"] is MatchingStatus, (
            f"UpdateOcrJob.status should be MatchingStatus, got {hints['status']}"
        )

    def test_update_ocr_job_constructs_with_matching_status(self):
        """UpdateOcrJob must accept MatchingStatus values."""
        from app.ocr.data.ocr_repository import UpdateOcrJob

        job = UpdateOcrJob(
            job_id="test-123",
            status=MatchingStatus.OCR_FAILED,
            error_message="API error",
        )
        assert job.status == MatchingStatus.OCR_FAILED

    def test_ocr_manager_protocol_uses_ocr_client(self):
        """OcrManager.start_ocr_job must accept OcrClient, not BatchOcrClient."""
        from app.ocr.data.ocr_repository import OcrManager
        from app.ocr.ocr_manager import OcrClient

        sig = inspect.signature(OcrManager.start_ocr_job)
        ocr_client_param = sig.parameters["ocr_client"]
        assert ocr_client_param.annotation is OcrClient, (
            f"OcrManager.start_ocr_job ocr_client param should be OcrClient, "
            f"got {ocr_client_param.annotation}"
        )

    def test_no_batching_imports_in_ocr_repository(self):
        """ocr_repository.py must not import from app.ocr.batching."""
        import app.ocr.data.ocr_repository as mod

        source = inspect.getsource(mod)
        assert "from app.ocr.batching" not in source


class TestTask2WorkerBatchOcr:
    """Task 2: worker._run_batch_ocr uses OpenAiOcrClient + OcrRequest."""

    def test_run_batch_ocr_no_batching_imports(self):
        """_run_batch_ocr must not import from app.ocr.batching."""
        import app.jobs.worker as mod

        source = inspect.getsource(mod)
        assert "from app.ocr.batching" not in source

    def test_run_batch_ocr_imports_ocr_client(self):
        """_run_batch_ocr must import OpenAiOcrClient."""
        import app.jobs.worker as mod

        source = inspect.getsource(mod)
        assert "from app.ocr.clients.open_ai import OpenAiOcrClient" in source

    def test_run_batch_ocr_imports_ocr_request(self):
        """_run_batch_ocr must import OcrRequest."""
        import app.jobs.worker as mod

        source = inspect.getsource(mod)
        assert "from app.ocr.ocr_manager import OcrRequest" in source

    def test_run_batch_ocr_uses_matching_status(self):
        """_run_batch_ocr must use MatchingStatus, not JobStatus from batching."""
        import app.jobs.worker as mod

        source = inspect.getsource(mod)
        assert "is_terminal_matching_status" in source
        assert "JobStatus.COMPLETED" not in source or "from app.jobs" in source

    @pytest.mark.asyncio
    async def test_batch_ocr_creates_ocr_request_from_crops(self):
        """_run_batch_ocr must create OcrRequest with EncodedPetitionPage list."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.data.database.model.jobs import MatcherJob, OcrJob
        from app.data.database.model.petition_crop import PetitionCrop
        from app.ocr.ocr_manager import OcrJobStatus

        with TemporaryDirectory() as tmpdir:
            crops = []
            for i in range(3):
                crop_path = Path(tmpdir) / f"crop_{i}.png"
                crop_path.write_bytes(b"fake_image")
                crop = MagicMock(spec=PetitionCrop)
                crop.id = i
                crop.stored_path = str(crop_path)
                crop.scan_id = f"scan-{i}"
                crops.append(crop)

            job = MagicMock(spec=MatcherJob)
            job.id = 1
            job.campaign_id = "camp-123"
            ocr_job = MagicMock(spec=OcrJob)
            ocr_job.id = 10

            mock_config = MagicMock()
            mock_config.provider = "openai"
            mock_config.api_key = "test-key"  # pragma: allowlist secret
            mock_config.model = "gpt-4o"

            mock_client = AsyncMock()
            mock_client.create_batch_job.return_value = OcrJobStatus(
                ocr_job_id="batch-123",
                campaign_id="camp-123",
                task_id="task-123",
                ocr_provider_id="openai",
                task_status=MatchingStatus.OCR_IN_PROGRESS,
            )
            mock_client.fetch_job_status.return_value = OcrJobStatus(
                ocr_job_id="batch-123",
                campaign_id="camp-123",
                task_id="task-123",
                ocr_provider_id="openai",
                task_status=MatchingStatus.OCR_COMPLETED,
            )

            from app.ocr.ocr_manager import OcrResult

            mock_client.get_ocr_results.return_value = AsyncIterator(
                [
                    OcrResult(
                        job_id="batch-123",
                        campaign_id="camp-123",
                        document_path="crop_0.png",
                        page_num=0,
                        row_num=0,
                        result_parts=[
                            {"field_name": "Name", "value": "John Smith"},
                            {"field_name": "Address", "value": "123 Main St"},
                        ],
                    ),
                ]
            )

            from app.jobs.worker import JobWorker

            worker = JobWorker()

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
                session = MagicMock()

                await worker._run_batch_ocr(session, job, ocr_job, crops)

                mock_client.create_batch_job.assert_called_once()
                call_args = mock_client.create_batch_job.call_args
                request_data = call_args[0][0]

                assert request_data.campaign_id == "camp-123"
                assert request_data.provider_id == "openai"
                assert len(request_data.encoded_pages) == 3

    @pytest.mark.asyncio
    async def test_batch_ocr_falls_back_on_failure(self):
        """_run_batch_ocr must fall back to _run_real_ocr on failure."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.data.database.model.jobs import MatcherJob, OcrJob
        from app.data.database.model.petition_crop import PetitionCrop

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
            mock_config.api_key = "test-key"  # pragma: allowlist secret
            mock_config.model = "gpt-4o"

            mock_client = AsyncMock()
            mock_client.create_batch_job.side_effect = RuntimeError("API down")

            from app.jobs.worker import JobWorker

            worker = JobWorker()
            worker._run_real_ocr = AsyncMock()

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
                session = MagicMock()

                await worker._run_batch_ocr(session, job, ocr_job, [crop])

                worker._run_real_ocr.assert_called_once_with(
                    session, job, ocr_job, [crop]
                )


class TestTask3OcrHelperBatchingRemoved:
    """Task 3: ocr_helper.py has no batching imports or dead functions."""

    def test_no_batching_imports(self):
        """ocr_helper.py must not import from app.ocr.batching."""
        import app.ocr.ocr_helper as mod

        source = inspect.getsource(mod)
        assert "from app.ocr.batching" not in source

    def test_emit_batch_job_status_removed(self):
        """emit_batch_job_status must not exist in ocr_helper."""
        import app.ocr.ocr_helper as mod

        assert not hasattr(mod, "emit_batch_job_status"), (
            "emit_batch_job_status should be deleted"
        )

    def test_create_ocr_results_removed(self):
        """create_ocr_results must not exist in ocr_helper."""
        import app.ocr.ocr_helper as mod

        assert not hasattr(mod, "create_ocr_results"), (
            "create_ocr_results should be deleted"
        )

    def test_no_batchocr_request_input_in_source(self):
        """BatchOcrRequestInput must not appear in ocr_helper source."""
        import app.ocr.ocr_helper as mod

        source = inspect.getsource(mod)
        assert "BatchOcrRequestInput" not in source


class TestTask4BatchingDirectoryDeleted:
    """Task 4: app.ocr.batching module no longer exists."""

    def test_batching_module_not_importable(self):
        """import app.ocr.batching must raise ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            import app.ocr.batching  # noqa: F401

    def test_batching_submodules_not_importable(self):
        """All batching submodules must be unresolvable."""
        submodules = [
            "app.ocr.batching.batch_handler",
            "app.ocr.batching.batch_ocr_client",
            "app.ocr.batching.openai_ocr_batch",
            "app.ocr.batching.request_types",
            "app.ocr.batching.memory_job_monitor",
            "app.ocr.batching.memory_batching",
            "app.ocr.batching.ocr_batch_repository",
            "app.ocr.batching.gemini_ocr_batch",
            "app.ocr.batching.mistral_ocr_batch",
        ]
        for mod_name in submodules:
            with pytest.raises(ModuleNotFoundError):
                __import__(mod_name)


class TestTask5BatchOcrHandlerDeleted:
    """Task 5: BatchOcrHandler is not importable."""

    def test_batch_ocr_manager_not_importable(self):
        """batch_ocr_manager.py must not exist."""
        with pytest.raises(ModuleNotFoundError):
            import app.ocr.clients.batch_ocr_manager  # noqa: F401

    def test_batch_ocr_handler_not_importable(self):
        """BatchOcrHandler must not be importable."""
        with pytest.raises((ModuleNotFoundError, ImportError)):
            from app.ocr.clients.batch_ocr_manager import BatchOcrHandler  # noqa: F401


class AsyncIterator:
    """Helper to mock async generators in tests."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration from None
