import asyncio
import contextlib
from asyncio.locks import Event
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, override

import structlog

from app.data.memory_db import get_memory_db
from app.ocr.batching.batch_ocr_client import (
	BatchJobStatus,
	BatchOcrClient,
	JobStatus,
	OcrJobMonitor,
)
from app.ocr.batching.memory_batching import InMemoryBatchJobRepository
from app.ocr.batching.ocr_batch_repository import OcrBatchJobRepository

logger = structlog.get_logger(__name__)

_POLL_INTERVAL = 5.0  # seconds


class InMemoryJobMonitor(OcrJobMonitor):
	"""
	Simple in-memory job monitor that supports:
	- register_job: store job and optionally start a provider-specific poller
	- update_status: update store and notify waiters
	- get_job_status: return latest snapshot
	- monitor_job: async generator that yields updates as they happen (SSE consumer)
	"""

	def __init__(self, batch_repository: OcrBatchJobRepository) -> None:
		self._jobs: OcrBatchJobRepository = batch_repository
		# job_id -> asyncio.Event set when update occurs
		self._events: dict[str, asyncio.Event] = {}
		# job_id -> background poller task
		self._tasks: dict[str, asyncio.Task] = {}
		# store provider-specific clients/details if needed
		self._providers: dict[str, dict[str, Any]] = {}

	@override
	async def register_job(
		self,
		job_id: str,
		provider_client: BatchOcrClient,
	) -> BatchJobStatus:
		status: BatchJobStatus = await provider_client.get_job_status(job_id)
		registered_status = await self._jobs.register_batch_job(status)
		self._events[job_id] = asyncio.Event()
		logger.debug(
			"Registered job",
			job_id=job_id,
			provider_id=provider_client.provider_id,
		)

		# If provider is openai, start poller
		# default client; caller can override via set_provider_client
		# If caller provided a client, it should be registered with set_provider_client
		self._providers[job_id] = {
			"client": provider_client,
			"provider_id": provider_client.provider_id,
		}
		# start a background polling task; it will look up client from providers map
		self._tasks[job_id] = asyncio.create_task(self._poll_batch_client_job(job_id))

		return registered_status

	def set_provider_client(self, job_id: str, client: BatchOcrClient) -> None:
		"""
		Attach a provider client (e.g. OpenAI client) to a registered job_id
		before poller runs.
		"""
		if job_id not in self._providers:
			self._providers[job_id] = {}
		self._providers[job_id]["client"] = client

	@override
	async def update_status(
		self,
		job_id: str,
		status: JobStatus,
		error: str | None = None,
	) -> BatchJobStatus:
		job: BatchJobStatus = await self._jobs.fetch_batch_job_status(job_id)
		job.status = status
		job.error = error
		if status in (
			JobStatus.COMPLETED,
			JobStatus.FAILED,
			JobStatus.EXPIRED,
			JobStatus.CANCELLED,
		):
			job.completed_at = datetime.now(UTC)
		job = await self._jobs.update_batch_job_status(job)
		# notify any waiters
		ev: Event | None = self._events.get(job_id)
		if ev:
			ev.set()
			# recreate event for next update
			self._events[job_id] = asyncio.Event()
		logger.debug("Updated job", job_id=job_id, status=status, error=error)
		return job

	@override
	async def get_job_status(self, job_id: str) -> BatchJobStatus:
		job_status: BatchJobStatus = await self._jobs.fetch_batch_job_status(job_id)
		return job_status

	@override
	async def monitor_job(self, job_id: str) -> AsyncGenerator[BatchJobStatus]:
		"""
		Async generator for SSE: yields current status, then yields further
		updates as they occur. Terminates when job reaches a terminal state.
		"""
		# initial snapshot

		all_jobs = await self._jobs.fetch_all_batch_jobs()

		logger.debug(f"batch job size: {len(list(all_jobs))}")

		yield await self._jobs.fetch_batch_job_status(job_id)

		# continue until terminal
		while True:
			# fetch event for this job; wait until set
			ev = self._events.get(job_id)
			if not ev:
				# no event object => no updates expected
				await asyncio.sleep(_POLL_INTERVAL)
			else:
				try:
					await asyncio.wait_for(ev.wait(), timeout=_POLL_INTERVAL)
				except TimeoutError:
					logger.warning("Timeout error")
					yield await self._jobs.fetch_batch_job_status(job_id)

			snapshot: BatchJobStatus = await self._jobs.fetch_batch_job_status(job_id)
			yield await self._jobs.update_batch_job_status(snapshot)

			if snapshot.status in (
				JobStatus.COMPLETED,
				JobStatus.FAILED,
				JobStatus.EXPIRED,
				JobStatus.CANCELLED,
			):
				logger.info(f"Batch OCR job {snapshot.status}")
				break

	# --- provider-specific pollers ---

	async def _poll_batch_client_job(self, job_id: str) -> None:
		"""
		Polls OpenAI for the job status and updates the in-memory store.
		Expects that self._providers[job_id]["client"] has been set to an
		BatchOcrClient.
		"""
		provider_info: dict[str, BatchOcrClient] = self._providers.get(job_id, {})
		provider_id: BatchOcrClient | None = provider_info.get("provider_id")
		client: BatchOcrClient | None = provider_info.get("client")
		if not provider_id:
			logger.error("Missing provider_id for BatchOcrClient poller", job_id=job_id)
			return

		# Wait a tiny bit to allow caller to attach client
		await asyncio.sleep(0.1)

		while True:
			try:
				client: BatchOcrClient | None = provider_info.get("client")
				if client is None:
					# no client attached yet; try again after interval
					await asyncio.sleep(_POLL_INTERVAL)
					continue

				batch: BatchJobStatus = await client.get_job_status(job_id)
				status: JobStatus = batch.status

				_ = await self.update_status(
					job_id,
					status,
					error=getattr(batch, "error", None),
				)

				if status in (
					JobStatus.COMPLETED,
					JobStatus.FAILED,
					JobStatus.CANCELLED,
					JobStatus.EXPIRED,
				):
					break

			except Exception as exc:
				# mark failed and stop polling
				logger.exception("Batch poller error", job_id=job_id, error=str(exc))
				with contextlib.suppress(Exception):
					_ = await self.update_status(
						job_id, JobStatus.FAILED, error=str(exc)
					)
				break

			await asyncio.sleep(_POLL_INTERVAL)


# Singleton monitor instance used by handlers
_default_monitor: InMemoryJobMonitor | None = None


def get_default_monitor() -> InMemoryJobMonitor:
	global _default_monitor
	if _default_monitor is None:
		_default_monitor = InMemoryJobMonitor(
			batch_repository=InMemoryBatchJobRepository(get_memory_db())
		)
	return _default_monitor
