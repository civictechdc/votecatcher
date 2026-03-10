import contextlib
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, override

import structlog

from app.ocr.batching.batch_ocr_client import BatchJobStatus
from app.ocr.batching.ocr_batch_repository import OcrBatchJobRepository

logger = structlog.get_logger(__name__)


class InMemoryBatchJobRepository(OcrBatchJobRepository):
	def __init__(self, memory_register: dict[str, Any] | None = None) -> None:
		self._batch_job_registry: dict[str, BatchJobStatus] = (
			memory_register if memory_register else dict[str, BatchJobStatus]()
		)

	@override
	async def register_batch_job(self, batch_job: BatchJobStatus) -> BatchJobStatus:
		self._batch_job_registry[batch_job.job_id] = batch_job
		return self._batch_job_registry[batch_job.job_id]

	@override
	async def fetch_batch_job_status(self, job_id: str) -> BatchJobStatus:
		return self._batch_job_registry[job_id]

	@override
	async def fetch_all_batch_jobs(self) -> Iterable[BatchJobStatus]:
		return self._batch_job_registry.values()

	@override
	async def update_batch_job_status(self, status: BatchJobStatus) -> BatchJobStatus:
		if status.job_id not in self._batch_job_registry:
			raise KeyError(f"Could not update status for batch job {status.job_id}")

		current_job: BatchJobStatus = self._batch_job_registry[status.job_id]

		self._batch_job_registry[status.job_id] = status.model_copy(
			update={
				"started_at": current_job.started_at,
				"last_updated_at": datetime.now(UTC),
			}
		)

		return self._batch_job_registry[status.job_id]

	@override
	async def remove_batch_job(self, job_id: str) -> None:
		with contextlib.suppress(KeyError):
			del self._batch_job_registry[job_id]

	@override
	async def clear_all_batch_records(self) -> None:
		self._batch_job_registry.clear()
