"""Mistral OCR client implementation."""

import json
import shutil
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import structlog

from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import OCRData
from app.ocr.ocr_manager import (
	OcrClient,
	OcrJobStatus,
	OcrMessageData,
	OcrRequest,
	OcrResult,
	create_batch_payload,
)
from app.settings import MistralAiConfig

logger = structlog.get_logger(__name__)

STATUS_MAPPING: dict[str, MatchingStatus] = {
	"QUEUED": MatchingStatus.NOT_STARTED,
	"RUNNING": MatchingStatus.OCR_IN_PROGRESS,
	"SUCCESS": MatchingStatus.OCR_COMPLETED,
	"FAILED": MatchingStatus.OCR_FAILED,
	"CANCELLED": MatchingStatus.OCR_CANCELLED,
	"TIMEOUT": MatchingStatus.OCR_TIMED_OUT,
}


class MistralOcrClient(OcrClient):
	def __init__(self, config: MistralAiConfig, output_dir: Path) -> None:
		self.config: MistralAiConfig = config
		self.parent_dir: Path = output_dir

	def _get_client(self):
		"""Get or create Mistral client (lazy initialization for testing)."""
		from mistralai import Mistral

		return Mistral(api_key=self.config.api_key)

	async def _create_request_file(
		self, campaign_id: str, req_contents: list[Any], parent_folder: Path
	) -> Path:
		"""Create a JSONL request file for Mistral batch API."""
		logger.debug(f"Creating Mistral batch request for campaign {campaign_id}")

		file_path: Path = parent_folder.joinpath(f"request_batch_{campaign_id}.jsonl")
		async with aiofiles.open(file_path, "w") as f:
			for obj in req_contents:
				await f.write(json.dumps(obj) + "\n")

		return file_path

	def _create_payload(
		self, campaign_id: str, payloads: list[OcrMessageData]
	) -> list[Any]:
		"""Create request payloads for Mistral batch API."""
		total_payload_size: int = len(payloads)
		contents: list[Any] = []

		for idx, payload in enumerate(payloads):
			contents.append(
				{
					"custom_id": f"cmpgnid-{campaign_id}__file-{payload.file_name}__page-{payload.page}__total-{total_payload_size}__batch-{idx}",
					"method": "POST",
					"url": "/v1/chat/completions",
					"body": {
						"model": self.config.model,
						"temperature": 0.2,
						"messages": [
							{
								"role": payload.role,
								"content": payload.messages,
							}
						],
					},
				}
			)

		return contents

	async def create_batch_job(self, request_data: OcrRequest) -> OcrJobStatus:
		"""Create a Mistral batch OCR job."""
		client = self._get_client()
		campaign_id: str = request_data.campaign_id

		content_batch: list[OcrMessageData] = [
			create_batch_payload(img) for img in request_data.encoded_pages
		]

		request_contents: list[Any] = self._create_payload(
			campaign_id=campaign_id, payloads=content_batch
		)

		parent_folder: Path = self.parent_dir.joinpath("ocr_request", "mistral")

		if parent_folder.exists():
			shutil.rmtree(parent_folder)
		parent_folder.mkdir(parents=True, exist_ok=True)

		jsonl_path: Path = await self._create_request_file(
			campaign_id=campaign_id,
			req_contents=request_contents,
			parent_folder=parent_folder,
		)

		batch_file = client.files.upload(
			file={
				"file_name": f"batch_{campaign_id}.jsonl",
				"content": open(jsonl_path, "rb"),
			},
			purpose="batch",
		)

		batch_job = client.batch.jobs.create(
			input_file_id=batch_file.id,
			model=self.config.model,
			endpoint="/v1/chat/completions",
			metadata={
				"campaign_id": campaign_id,
				"task_id": request_data.task_id,
				"page_count": str(request_data.total_payload_size),
			},
		)

		shutil.rmtree(jsonl_path.parent)

		result_data: dict[str, Any] = {}
		failure_message: str | None = None

		if batch_job.status == "FAILED" and batch_job.errors:
			failure_message = "\n".join([str(e) for e in batch_job.errors])

		return OcrJobStatus(
			ocr_job_id=batch_job.id,
			campaign_id=campaign_id,
			ocr_model=self.config.model,
			ocr_provider_id="mistral",
			task_status=STATUS_MAPPING.get(
				batch_job.status, MatchingStatus.OCR_PENDING
			),
			task_id=request_data.task_id,
			created_at=datetime.fromtimestamp(batch_job.created_at / 1000, UTC),
			status_message=f"Mistral status: {batch_job.status}",
			failure_message=failure_message,
			result_data=result_data if result_data else None,
		)

	async def fetch_job_status(self, job_id: str) -> OcrJobStatus:
		"""Fetch the status of a Mistral batch job."""
		client = self._get_client()
		batch_job = client.batch.jobs.get(job_id=job_id)

		campaign_id = batch_job.metadata.get("campaign_id", "unknown")
		task_id = batch_job.metadata.get("task_id", "unknown")

		completed_at: int | None = batch_job.completed_at

		logger.debug(
			f"Mistral batch status: {batch_job.status} -> {STATUS_MAPPING.get(batch_job.status, MatchingStatus.OCR_PENDING)}"
		)

		return OcrJobStatus(
			ocr_job_id=batch_job.id,
			campaign_id=campaign_id,
			ocr_provider_id="mistral",
			ocr_model=self.config.model,
			task_status=STATUS_MAPPING.get(
				batch_job.status, MatchingStatus.OCR_PENDING
			),
			task_id=task_id,
			created_at=datetime.fromtimestamp(batch_job.created_at / 1000, UTC),
			status_message=f"Mistral status: {batch_job.status}",
			updated_at=datetime.now(UTC),
			ended_at=(
				datetime.fromtimestamp(completed_at / 1000, UTC)
				if completed_at
				else None
			),
		)

	async def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResult]:
		"""Retrieve OCR results from a completed Mistral batch job."""
		client = self._get_client()
		batch_job = client.batch.jobs.get(job_id=job_id)
		campaign_id = batch_job.metadata.get("campaign_id", "unknown")

		if not batch_job.output_file_id:
			logger.warning(f"No output file available for job {job_id}")
			return

		output_file = client.files.download(file_id=batch_job.output_file_id)
		content = output_file.content.decode("utf-8")

		row_idx: int = 0
		for line in content.strip().split("\n"):
			try:
				json_item = json.loads(line)
				content_string = json_item["response"]["body"]["choices"][0]["message"][
					"content"
				]

				ocr_data: OCRData = OCRData.model_validate_json(content_string)

				custom_id = json_item["custom_id"]
				parts = custom_id.split("__")
				page_num = int(parts[2].split("-")[1])

				for item_idx, item in enumerate(ocr_data.data):
					result_item: OcrResult = OcrResult(
						job_id=job_id,
						campaign_id=campaign_id,
						page_num=page_num,
						row_num=item_idx,
						document_path=f"page_{page_num}",
						result_parts=[
							{"field_name": key, "value": value}
							for key, value in item.model_dump().items()
						],
					)
					row_idx += 1
					yield result_item
			except Exception as parse_error:
				logger.warning(
					f"Failed to parse line {row_idx} for job {job_id}, skipping",
					error=str(parse_error),
				)
				row_idx += 1
				continue

	@property
	def provider_id(self) -> str:
		return "mistral"
