"""Gemini OCR client implementation."""

import shutil
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from google import genai
from google.genai.types import BatchJob

from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import OCRData
from app.ocr.ocr_client_factory import ProviderConfig
from app.ocr.ocr_manager import (
	OcrClient,
	OcrJobStatus,
	OcrMessageData,
	OcrRequest,
	OcrResult,
	create_batch_payload,
)

logger = structlog.get_logger(__name__)

STATUS_MAPPING: dict[str, MatchingStatus] = {
	"JOB_STATE_UNSPECIFIED": MatchingStatus.NOT_STARTED,
	"JOB_STATE_QUEUED": MatchingStatus.NOT_STARTED,
	"JOB_STATE_PENDING": MatchingStatus.NOT_STARTED,
	"JOB_STATE_RUNNING": MatchingStatus.OCR_IN_PROGRESS,
	"JOB_STATE_SUCCEEDED": MatchingStatus.OCR_COMPLETED,
	"JOB_STATE_FAILED": MatchingStatus.OCR_FAILED,
	"JOB_STATE_CANCELLED": MatchingStatus.OCR_CANCELLED,
	"JOB_STATE_EXPIRED": MatchingStatus.OCR_TIMED_OUT,
}


class GeminiOcrClient(OcrClient):
	def __init__(self, config: ProviderConfig, output_dir: Path) -> None:
		self.config: ProviderConfig = config
		self.parent_dir: Path = output_dir

	async def create_batch_job(self, request_data: OcrRequest) -> OcrJobStatus:
		"""Create a Gemini batch OCR job."""
		campaign_id: str = request_data.campaign_id

		content_batch: list[OcrMessageData] = [
			create_batch_payload(img) for img in request_data.encoded_pages
		]

		req_contents: list[Any] = []
		for payload in content_batch:
			req_contents.append(
				{
					"role": payload.role,
					"parts": payload.messages,
				}
			)

		parent_folder: Path = self.parent_dir.joinpath("ocr_request", "gemini")
		if parent_folder.exists():
			shutil.rmtree(parent_folder)
		parent_folder.mkdir(parents=True, exist_ok=True)

		client = genai.Client(api_key=self.config.api_key)

		batch_job: BatchJob = client.batches.create(
			model=f"models/{self.config.model}",
			src=req_contents,
			config={
				"display_name": f"ocr-campaign-{campaign_id}",
			},
		)

		logger.debug(f"Created Gemini batch job: {batch_job.name}")

		result_data: dict[str, Any] = {}
		failure_message: str | None = None

		if batch_job.error:
			failure_message = str(batch_job.error)

		return OcrJobStatus(
			ocr_job_id=batch_job.name,
			campaign_id=campaign_id,
			ocr_model=self.config.model,
			ocr_provider_id="gemini",
			task_status=STATUS_MAPPING.get(
				batch_job.state.name, MatchingStatus.OCR_PENDING
			),
			task_id=request_data.task_id,
			created_at=batch_job.create_time or datetime.now(UTC),
			status_message=f"Gemini status: {batch_job.state.name}",
			failure_message=failure_message,
			result_data=result_data if result_data else None,
		)

	async def fetch_job_status(self, job_id: str) -> OcrJobStatus:
		"""Fetch the status of a Gemini batch job."""
		client = genai.Client(api_key=self.config.api_key)
		batch_job = client.batches.get(name=job_id)

		campaign_id = batch_job.metadata.get("campaign_id", "unknown")
		task_id = batch_job.metadata.get("task_id", "unknown")

		logger.debug(
			"Gemini batch status: %s -> %s",
			batch_job.state.name,
			STATUS_MAPPING.get(batch_job.state.name, MatchingStatus.OCR_PENDING),
		)

		return OcrJobStatus(
			ocr_job_id=batch_job.name,
			campaign_id=campaign_id,
			ocr_provider_id="gemini",
			ocr_model=self.config.model,
			task_status=STATUS_MAPPING.get(
				batch_job.state.name, MatchingStatus.OCR_PENDING
			),
			task_id=task_id,
			created_at=batch_job.create_time or datetime.now(UTC),
			status_message=f"Gemini status: {batch_job.state.name}",
			updated_at=datetime.now(UTC),
			ended_at=batch_job.end_time if hasattr(batch_job, "end_time") else None,
		)

	async def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResult]:
		"""Retrieve OCR results from a completed Gemini batch job."""
		client = genai.Client(api_key=self.config.api_key)
		batch_job = client.batches.get(name=job_id)
		campaign_id = batch_job.metadata.get("campaign_id", "unknown")

		if not batch_job.dest:
			logger.warning(f"No results available for job {job_id}")
			return

		results = batch_job.dest

		row_idx: int = 0
		for idx, result in enumerate(results):
			try:
				if not result.response:
					continue

				content = result.response
				ocr_data: OCRData = OCRData.model_validate_json(content)

				for item_idx, item in enumerate(ocr_data.data):
					result_item: OcrResult = OcrResult(
						job_id=job_id,
						campaign_id=campaign_id,
						page_num=idx,
						row_num=item_idx,
						document_path=f"page_{idx}",
						result_parts=[
							{"field_name": key, "value": value}
							for key, value in item.model_dump().items()
						],
					)
					row_idx += 1
					yield result_item
			except Exception as parse_error:
				logger.warning(
					f"Failed to parse result {row_idx} for job {job_id}, skipping",
					error=str(parse_error),
				)
				row_idx += 1
				continue

	@property
	def provider_id(self) -> str:
		return "gemini"
