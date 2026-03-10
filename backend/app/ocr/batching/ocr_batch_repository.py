from collections.abc import Iterable
from typing import Protocol

from app.ocr.batching.batch_ocr_client import BatchJobStatus


class OcrBatchJobRepository(Protocol):
	async def register_batch_job(self, batch_job: BatchJobStatus) -> BatchJobStatus:
		raise NotImplementedError

	async def fetch_batch_job_status(self, job_id: str) -> BatchJobStatus:
		raise NotImplementedError

	async def fetch_all_batch_jobs(self) -> Iterable[BatchJobStatus]:
		raise NotImplementedError

	async def update_batch_job_status(self, status: BatchJobStatus) -> BatchJobStatus:
		raise NotImplementedError

	async def remove_batch_job(self, job_id: str) -> None:
		raise NotImplementedError

	async def clear_all_batch_records(self) -> None:
		raise NotImplementedError
