import asyncio
import json
from asyncio.locks import Lock
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import structlog

from app.data.database.model.ocr_model import (
	CreateOcrJob,
	OcrJob,
	OcrProviderRepository,
	ReadOcrProvider,
	UpdateOcrJobStatus,
)
from app.events.matching_task_events import MatchingTaskMonitor
from app.matching.match_repository import (
	MatchingStatus,
	MatchingTask,
	MatchTaskRepository,
	UpdateMatchingTask,
	is_terminal_matching_status,
)
from app.ocr.clients.open_ai import OpenAiOcrClient
from app.ocr.data.ocr_repository import OcrJobRepository
from app.ocr.ocr_manager import (
	OcrClient,
	OcrJobStatus,
	OcrRequest,
	OcrResult,
	ReadOcrResult,
)
from app.ocr.ocr_result_repo import CreateOcrResult, OcrResultRepository
from app.settings import OpenAiConfig
from app.settings.env_settings import AppSettings
from app.settings.settings_repo import OpenAiConfig

logger = structlog.get_logger(__name__)
_POLLING_INTERVAL_IN_SECONDS: float = 5.0


class BatchOcrHandler:
	def __init__(
		self,
		settings: AppSettings,
		ocr_provider_repo: OcrProviderRepository,
		ocr_job_repo: OcrJobRepository,
		matching_task_repo: MatchTaskRepository,
		matching_task_monitor: MatchingTaskMonitor,
		ocr_result_repo: OcrResultRepository,
	) -> None:
		self._lock: Lock = asyncio.Lock()
		self.match_monitor: MatchingTaskMonitor = matching_task_monitor
		self.ocr_provider_repo: OcrProviderRepository = ocr_provider_repo
		self.match_task_repo: MatchTaskRepository = matching_task_repo
		self.ocr_result_repo: OcrResultRepository = ocr_result_repo
		self.ocr_job_repo: OcrJobRepository = ocr_job_repo
		self.settings: AppSettings = settings
		self._active_clients_from_job: dict[str, OcrClient] = {}
		self._active_ocr_state: dict[str, MatchingTask] = {}
		self.tasks_events: dict[str, asyncio.Event] = {}
		self._active_ocr_polling: dict[str, asyncio.Task] = {}
		self._active_ocr_jobs: dict[str, OcrJob] = {}

	def _create_batch_ocr_client(self, config: OpenAiConfig) -> OcrClient:
		output_dir: Path = self.settings.local_campaign_base_dir().joinpath(
			self.settings.ocr_dir
		)
		return OpenAiOcrClient(config=config, output_dir=output_dir)

	async def _update_task_status(self, ocr_job: OcrJobStatus) -> MatchingTask:
		task_update: UpdateMatchingTask = UpdateMatchingTask(
			task_id=ocr_job.task_id,
			status=ocr_job.task_status,
			status_message=ocr_job.status_message,
			failure_message=ocr_job.failure_message,
			ended_at=ocr_job.ended_at,
			updated_at=(
				ocr_job.updated_at if ocr_job.updated_at else datetime.now(UTC)
			),
			ocr_result_data=(
				json.dumps(ocr_job.result_data) if ocr_job.result_data else None
			),
		)

		job_update: UpdateOcrJobStatus = UpdateOcrJobStatus(
			job_id=ocr_job.ocr_job_id,
			state=ocr_job.task_status,
			model_version=ocr_job.ocr_model,
		)

		self._active_ocr_jobs[
			ocr_job.ocr_job_id
		] = await self.ocr_job_repo.update_ocr_job_status(job_update)

		if (
			is_terminal_matching_status(ocr_job.task_status)
			or ocr_job.task_status == MatchingStatus.OCR_COMPLETED
		):
			logger.debug("Ocr Job is terminal in update")
			self._active_ocr_polling.pop(ocr_job.ocr_job_id, None)
			self._active_ocr_jobs.pop(ocr_job.ocr_job_id, None)

		# TODO - Improve architecture on data & event publishing
		matching_task: MatchingTask = (
			await self.match_monitor.publish_updated_task_status(task_update)
		)
		return matching_task

	async def start_ocr_job(self, ocr_data: OcrRequest) -> MatchingTask:
		config: OpenAiConfig = OpenAiConfig(
			api_key=self.settings.ocr_api_key,
			model=self.settings.ocr_model,
			name=self.settings.ocr_provider_name,
		)
		ocr_client: OcrClient = self._create_batch_ocr_client(config)
		ocr_job_status: OcrJobStatus = await ocr_client.create_batch_job(ocr_data)
		job_id: str = ocr_job_status.ocr_job_id
		self._active_clients_from_job[job_id] = ocr_client
		self._active_ocr_polling[job_id] = asyncio.create_task(
			self._poll_active_ocr_jobs(job_id)
		)

		provider: ReadOcrProvider = await self.ocr_provider_repo.get_ocr_provider(
			config.name
		)

		new_job: CreateOcrJob = CreateOcrJob(
			job_id=ocr_job_status.ocr_job_id,
			match_task_id=ocr_job_status.task_id,
			provider_unique_name=provider.unique_name,
			campaign_unique_name=ocr_data.campaign_id,
			request_payload="",
			petition_scan_filename=ocr_data.encoded_pages[0].petition_file_name,
		)
		self._active_ocr_jobs[job_id] = await self.ocr_job_repo.save_ocr_job(new_job)

		return await self._update_task_status(ocr_job_status)

	async def get_job_status(self, job_id: str) -> MatchingTask:
		client: OcrClient = self._active_clients_from_job[job_id]
		assert client is not None, "OCR client was not initalised"
		job_status: OcrJobStatus = await client.fetch_job_status(job_id)
		return await self._update_task_status(job_status)

	async def _save_ocr_results(self, ocr_job: OcrJobStatus, client: OcrClient) -> None:
		job_id: str = ocr_job.ocr_job_id
		ocr_results: list[OcrResult] = [
			result async for result in client.get_ocr_results(job_id)
		]

		save_results: list[CreateOcrResult] = [
			CreateOcrResult(task_id=ocr_job.task_id, ocr_job_id=job_id, ocr_result=r)
			for r in ocr_results
		]
		await self.ocr_result_repo.save_ocr_results(save_results)

	async def _poll_active_ocr_jobs(self, job_id: str) -> None:
		client: OcrClient | None = self._active_clients_from_job.get(job_id)

		if not client:
			logger.error("Ocr client not active for job")
			return

		await asyncio.sleep(0.1)

		current_task: MatchingTask | None = None
		while True:
			try:
				ocr_status: OcrJobStatus = await client.fetch_job_status(job_id)
				if current_task is None:
					current_task = await self.match_task_repo.get_matching_task(
						ocr_status.task_id
					)

				if (
					is_terminal_matching_status(ocr_status.task_status)
					or ocr_status.task_status == MatchingStatus.OCR_COMPLETED
				):
					logger.debug("Job has reached terminal in ocr batch loop")
					# Remove client if task is no longer active
					ocr_client: OcrClient = self._active_clients_from_job.pop(job_id)
					# End polling
					# Save results if success
					current_task = await self._update_task_status(ocr_status)
					if ocr_status.task_status == MatchingStatus.OCR_COMPLETED:
						await self._save_ocr_results(ocr_status, ocr_client)
					break

				# Update the matching task from the latest ocr job state
				logger.debug(
					f"Current job status: {current_task.status}. Ocr task status: {ocr_status.task_status}"
				)
				if current_task.status != ocr_status.task_status:
					logger.debug(
						f"Job has switched status from {current_task.status} to {ocr_status.task_status}"
					)
					current_task = await self._update_task_status(ocr_status)
				else:
					await asyncio.sleep(_POLLING_INTERVAL_IN_SECONDS)
					continue
			except Exception as exc:
				logger.error("OCR poller error", job_id=job_id, error=str(exc))
				task_update: UpdateMatchingTask = UpdateMatchingTask(
					task_id=current_task.id,
					status=MatchingStatus.OCR_FAILED,
					status_message=None,
					failure_message=f"OCR polling error: {str(exc)}",
					ended_at=datetime.now(UTC),
					updated_at=datetime.now(UTC),
					ocr_result_data=None,
				)
				(
					await self.match_monitor.publish_updated_task_status(task_update)
				)
				break

		await asyncio.sleep(_POLLING_INTERVAL_IN_SECONDS)

	async def get_ocr_results(
		self,
		task_id: str,
	) -> Iterable[ReadOcrResult]:
		return await self.ocr_result_repo.fetch_ocr_results_by_task(task_id)
