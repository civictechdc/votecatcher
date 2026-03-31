import json
import shutil
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import structlog
from openai._client import AsyncOpenAI
from openai._legacy_response import HttpxBinaryResponseContent
from openai.lib._pydantic import to_strict_json_schema
from openai.types.batch import Batch, Errors
from openai.types.file_object import FileObject

from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import OCRData, OCREntry
from app.ocr.ocr_manager import (
	OcrJobStatus,
	OcrMessageData,
	OcrRequest,
	OcrResult,
	create_batch_payload,
)
from app.settings import OpenAiConfig

logger = structlog.get_logger(__name__)

# https://platform.openai.com/docs/guides/batch#4-check-the-status-of-a-batch
STATUS_MAPPING: dict[str, MatchingStatus] = {
	"validating": MatchingStatus.NOT_STARTED,
	"failed": MatchingStatus.OCR_FAILED,
	"in_progress": MatchingStatus.OCR_IN_PROGRESS,
	"finalizing": MatchingStatus.OCR_IN_PROGRESS,
	"completed": MatchingStatus.OCR_COMPLETED,
	"expired": MatchingStatus.OCR_TIMED_OUT,
	"cancelling": MatchingStatus.OCR_CANCELLED,
	"cancelled": MatchingStatus.OCR_CANCELLED,
}


class OpenAiOcrClient:
	def __init__(self, config: OpenAiConfig, output_dir: Path) -> None:
		self.config: OpenAiConfig = config
		self.client: AsyncOpenAI = AsyncOpenAI(
			api_key=config.api_key,
		)
		self.parent_dir: Path = output_dir

	def _create_custom_id_format(
		self,
		campaign_id: str,
		payload: OcrMessageData,
		batch_idx: int,
		page_total: int,
	) -> str:
		return (
			f"cmpgnid-{campaign_id}__file-{payload.file_name}__page-"
			f"{payload.page}__total-{page_total}__batch-{batch_idx}"
		)

	def _create_payload(
		self, campaign_id: str, payloads: list[OcrMessageData]
	) -> list[Any]:
		total_payload_size: int = len(payloads)
		contents: list[Any] = []
		for idx, payload in enumerate[OcrMessageData](payloads):
			contents.append(
				{
					"custom_id": self._create_custom_id_format(
						campaign_id=campaign_id,
						payload=payload,
						batch_idx=idx,
						page_total=total_payload_size,
					),
					"method": "POST",
					"url": "/v1/chat/completions",
					"body": {
						# This is what you would have in your Chat Completions API call
						"model": self.config.model,
						"temperature": 0.2,
						"max_tokens": 300,
						"response_format": {
							"type": "json_schema",
							"json_schema": {
								"name": "OCREntry",
								"schema": to_strict_json_schema(model=OCRData),
								"strict": True,
							},
						},
						"messages": [
							# Add system prompt?
							{
								"role": payload.role,
								"content": payload.messages,
							}
						],
					},
				}
			)

		return contents

	async def _create_request_file(
		self, campaign_id: str, req_contents: list[Any], parent_folder: Path
	) -> Path:
		logger.debug(f"Creating OCR batch job for campaign {len(req_contents)}")

		file_path: Path = parent_folder.joinpath(f"request_batch_{campaign_id}.jsonl")
		async with aiofiles.open(file_path, "w") as f:
			for obj in req_contents:
				await f.write(json.dumps(obj) + "\n")

		return file_path

	async def create_batch_job(self, request_data: OcrRequest) -> OcrJobStatus:
		campaign_id: str = request_data.campaign_id

		content_batch: list[OcrMessageData] = [
			create_batch_payload(img) for img in request_data.encoded_pages
		]

		request_contents: list[Any] = self._create_payload(
			campaign_id=campaign_id, payloads=content_batch
		)

		parent_folder: Path = self.parent_dir.joinpath("ocr_request")

		if parent_folder.exists():
			shutil.rmtree(parent_folder)
		parent_folder.mkdir(parents=True, exist_ok=True)

		jsonl_path: Path = await self._create_request_file(
			campaign_id=campaign_id,
			req_contents=request_contents,
			parent_folder=parent_folder,
		)

		with open(jsonl_path, mode="rb") as f:
			batch_file: FileObject = await self.client.files.create(
				file=f, purpose="batch"
			)

		batch: Batch = await self.client.batches.create(
			input_file_id=batch_file.id,
			endpoint="/v1/chat/completions",
			completion_window="24h",
			metadata={
				"campaign_id": campaign_id,
				"page_count": str(request_data.total_payload_size),
				"task_id": request_data.task_id,
			},
		)

		# TODO save jsonl to db??
		shutil.rmtree(jsonl_path.parent)

		result_data: dict[str, Any] = {}
		if batch.output_file_id:
			result_data["result_id"] = batch.output_file_id

		failure_message: str | None = None
		errors: Errors | None = batch.errors
		if errors and errors.data:
			error_messages: list[str] = [e.message for e in errors.data if e.message]
			failure_message = "\n".join(error_messages)
			result_data["failure_id"] = batch.error_file_id

		return OcrJobStatus(
			ocr_job_id=batch.id,
			campaign_id=campaign_id,
			ocr_model=batch.model,
			ocr_provider_id="open_ai",
			task_status=STATUS_MAPPING[batch.status],
			task_id=request_data.task_id,
			created_at=datetime.fromtimestamp(batch.created_at, UTC),
			status_message=f"Ocr status: {batch.status}",
			failure_message=failure_message,
			result_data=result_data if len(result_data) > 0 else None,
		)

	async def fetch_job_status(self, job_id: str) -> OcrJobStatus:
		batch: Batch = await self.client.batches.retrieve(job_id)

		campaign_id: str = batch.metadata["campaign_id"]
		task_id: str = batch.metadata["task_id"]

		assert campaign_id, "No campaign has been associated with this batch"
		assert task_id, "No task has been associated with this batch"

		completed_at: int | None = (
			batch.cancelled_at
			if batch.cancelled_at
			else batch.expired_at
			if batch.expired_at
			else batch.completed_at
		)

		logger.debug(
			"Current batch status from open ai client: %s which maps to %s",
			batch.status,
			STATUS_MAPPING[batch.status],
		)

		return OcrJobStatus(
			ocr_job_id=batch.id,
			campaign_id=campaign_id,
			ocr_provider_id="open_ai",
			ocr_model=batch.model,
			task_status=STATUS_MAPPING[batch.status],
			task_id=task_id,
			created_at=datetime.fromtimestamp(batch.created_at, UTC),
			status_message=f"Ocr status: {batch.status}",
			updated_at=(
				datetime.fromtimestamp(batch.in_progress_at, UTC)
				if batch.in_progress_at is not None
				else datetime.now(UTC)
			),
			ended_at=(
				datetime.fromtimestamp(completed_at, UTC)
				if completed_at is not None
				else None
			),
		)

	@asynccontextmanager
	async def _get_results_context(self, job_id: str) -> AsyncGenerator[Path, str]:
		"""Async context manager for safely handling result file lifecycle"""
		batch: Batch = await self.client.batches.retrieve(job_id)
		batch.metadata["campaign_id"]
		batch_dir: Path = self.parent_dir.joinpath("ocr_result").joinpath("open_ai")
		if batch_dir.exists():
			shutil.rmtree(batch_dir)
		batch_dir.mkdir(parents=True, exist_ok=True)
		started_at_fmt: str = datetime.fromtimestamp(batch.created_at).strftime(
			format="%Y%m%d-%H:%M:%S"
		)
		file: Path = batch_dir.joinpath(
			f"{started_at_fmt}_{batch.id}_result_{batch.status}.jsonl"
		)

		try:
			file_content: HttpxBinaryResponseContent = await self.client.files.content(
				batch.output_file_id
			)
			byte_stream: str = file_content.content.decode("utf-8")

			async with aiofiles.open(file, "w", encoding="utf-8") as f:
				await f.write(byte_stream)

			yield file
		finally:
			# Always cleanup, even if exception or early termination
			# if batch_dir.exists():
			#     shutil.rmtree(batch_dir)
			logger.debug(f"Finally here for job {job_id}")
			pass

	def _extract_custom_id_parts(
		self, response_line: str
	) -> tuple[str, str, int, int, int]:
		json_item = json.loads(response_line)
		content_string = json_item["custom_id"]
		parts: list[str] = content_string.split("__")
		campaign_id: str = parts[0].split("-", 1)[1]
		file_name: str = parts[1].split("-", 1)[1]
		page_num: int = int(parts[2].split("-")[1])
		page_total: int = int(parts[3].split("-")[1])
		entry_number: int = int(parts[-1].split("-")[1])

		return (campaign_id, file_name, page_num, page_total, entry_number)

	def _extract_response_data(self, response_line: str) -> Generator[OCREntry, Any]:
		json_item = json.loads(response_line)
		content_string = json_item["response"]["body"]["choices"][0]["message"][
			"content"
		]
		ocr_data: OCRData = OCRData.model_validate_json(content_string)
		yield from ocr_data.data
		# return OCREntry.model_validate_json(content_string)

	async def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResult]:
		batch: Batch = await self.client.batches.retrieve(job_id)
		campaign_id = batch.metadata["campaign_id"]

		async with self._get_results_context(job_id) as path:
			with path.open(mode="r", encoding="utf-8") as f:
				row_idx: int = 0
				for line in f:
					line_stripped: str = line.strip()
					try:
						(
							campaign_id,
							file_name,
							page_num,
							page_total,
							entry_number,
						) = self._extract_custom_id_parts(line_stripped)
						for idx, item in enumerate(
							self._extract_response_data(line_stripped)
						):
							result_item: OcrResult = OcrResult(
								job_id=batch.id,
								campaign_id=campaign_id,
								page_num=page_num,
								row_num=idx,
								document_path=file_name,
								result_parts=[
									{"field_name": key, "value": value}
									for key, value in item.model_dump().items()
								],
							)
							row_idx += 1
							yield result_item
					except Exception as parse_error:
						logger.warning(
							"Failed to parse line %s for job %s, skipping",
							row_idx,
							job_id,
							error=str(parse_error),
						)
					row_idx += 1
					continue

	@property
	def provider_id(self) -> str:
		return "open_ai"
