import asyncio
import json
import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from app.logging.app_logger import AppLogger
from app.ocr.batching.batch_ocr_client import BatchJobStatus, BatchOcrClient, JobStatus
from app.ocr.batching.request_types import BatchRequestPayload, Payload
from app.ocr.data.ocr_repository import OcrResultItem, OcrResultRepository
from app.ocr.data_model import OCREntry
from app.ocr.ocr_client_factory import OpenAiConfig
from openai import OpenAI
from openai.lib._pydantic import to_strict_json_schema
from openai.types.batch import Batch
from openai.types.file_object import FileObject
from typing_extensions import override

logger = structlog.get_logger(__name__)


class OpenAiBatchClient(BatchOcrClient):

    def __init__(self, config: OpenAiConfig, result_store: OcrResultRepository) -> None:
        self.client: OpenAI = OpenAI(
            api_key=config.api_key,
        )
        self.config: OpenAiConfig = config
        self._result_store: OcrResultRepository = result_store

    @property
    @override
    def provider_id(self) -> str:
        return "open_ai"

    def update_config(self, config: OpenAiConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def _create_request_jsonl(
        self, req_contents: list[Any], parent_folder: Path
    ) -> Path:
        file_path: Path = parent_folder.joinpath("match_batch.jsonl")
        with open(file_path, "w") as file:
            for obj in req_contents:
                file.write(json.dumps(obj) + "\n")

        return file_path

    def _create_custom_id_format(
        self, campaign_id: str, payload: Payload, batch_idx: int, page_total: int
    ) -> str:

        return f"cmpgnid-{campaign_id}__file-{payload.file_name}__page-{payload.page + 1}__total-{page_total}__batch-{batch_idx}"

    def _extract_custom_id_parts(
        self, response_line: str
    ) -> tuple[str, str, int, int, int]:
        json_item = json.loads(response_line)
        content_string = json_item["custom_id"]
        parts: list[str] = content_string.split("__")
        campaign_id: str = parts[0].split("-")[1]
        file_name: str = parts[1].split("-")[1]
        page_num: int = int(parts[2].split("-")[1])
        page_total: int = int(parts[3].split("-")[1])
        entry_number: int = int(parts[-1].split("-")[1])

        return (campaign_id, file_name, page_num, page_total, entry_number)

    def _extract_response_data(self, response_line: str) -> OCREntry:
        json_item = json.loads(response_line)
        content_string = json_item["response"]["body"]["choices"][0]["message"][
            "content"
        ]
        return OCREntry.model_validate_json(content_string)

    @override
    async def create_batch_job(
        self, request_data: BatchRequestPayload, jsonl_path: Path
    ) -> BatchJobStatus:

        request_batch: list[Payload] = request_data.batch_payloads
        campaign_id: str = request_data.campaign_id

        # TODO Calculate the sizes of each file group and adjust batch sizes according to api limits

        req_contents: list[Any] = []
        for idx, request in enumerate[Payload](request_batch):

            req_contents.append(
                {
                    "custom_id": self._create_custom_id_format(
                        campaign_id=campaign_id,
                        payload=request,
                        batch_idx=idx + 1,
                        page_total=request_data.total_payload_size,
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
                                "schema": to_strict_json_schema(model=OCREntry),
                                "strict": True,
                            },
                        },
                        "messages": [
                            # Add system prompt?
                            {
                                "role": request.role,
                                "content": request.messages,
                            }
                        ],
                    },
                }
            )

        jsonl: Path = self._create_request_jsonl(req_contents, jsonl_path)
        batch_file: FileObject = self.client.files.create(
            file=open(jsonl, "rb"), purpose="batch"
        )

        batch: Batch = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "campaign_id": campaign_id,
                "page_count": str(request_data.total_payload_size),
            },
        )

        shutil.rmtree(jsonl_path)

        return BatchJobStatus(
            job_id=batch.id,
            campaign_id=campaign_id,
            status=JobStatus.PENDING,
            provider_id="open_ai",
            started_at=datetime.fromtimestamp(batch.created_at),
        )

    @override
    async def get_job_status(self, job_id: str) -> BatchJobStatus:

        batch_dir: Path = Path("batch_results")
        batch_dir.mkdir(exist_ok=True)

        status_mapping: dict[str, JobStatus] = {
            "validating": JobStatus.PENDING,
            "failed": JobStatus.FAILED,
            "in_progress": JobStatus.IN_PROGRESS,
            "finalizing": JobStatus.IN_PROGRESS,
            "completed": JobStatus.COMPLETED,
            "expired": JobStatus.EXPIRED,
            "cancelling": JobStatus.IN_PROGRESS,
            "cancelled": JobStatus.CANCELLED,
        }

        try:
            batch: Batch = self.client.batches.retrieve(job_id)
            assert batch.metadata, "No campaign has been associated with this batch"
            job_status: JobStatus = status_mapping[batch.status]
            batch_job: BatchJobStatus = BatchJobStatus(
                job_id=batch.id,
                campaign_id=batch.metadata["campaign_id"],
                status=job_status,
                provider_id="open_ai",
                started_at=datetime.fromtimestamp(batch.created_at),
            )

            match job_status:
                case JobStatus.COMPLETED:
                    completed_at: datetime = (
                        datetime.fromtimestamp(batch.completed_at)
                        if batch.completed_at
                        else datetime.now()
                    )
                    completed_job: BatchJobStatus = batch_job.model_copy(
                        update={
                            "status": job_status,
                            "completed_at": completed_at,
                            "result_url": batch.output_file_id,
                        }
                    )
                    return completed_job
                case JobStatus.CANCELLED | JobStatus.EXPIRED | JobStatus.FAILED:
                    failed_at: datetime = (
                        datetime.fromtimestamp(batch.failed_at)
                        if batch.failed_at
                        else (
                            datetime.fromtimestamp(batch.cancelled_at)
                            if batch.cancelled_at
                            else (
                                datetime.fromtimestamp(batch.expired_at)
                                if batch.expired_at
                                else datetime.now()
                            )
                        )
                    )
                    completed_job: BatchJobStatus = batch_job.model_copy(
                        update={
                            "status": job_status,
                            "completed_at": failed_at,
                            "error": batch.error_file_id,
                            "last_updated_at": datetime.now(timezone.utc),
                        }
                    )
                    return completed_job
                case _:
                    return batch_job

        except Exception as e:
            failed_job: BatchJobStatus = BatchJobStatus(
                job_id=job_id,
                campaign_id=batch.metadata["campaign_id"],
                status=JobStatus.FAILED,
                provider_id="open_ai",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error=str(e),
            )
            return failed_job

    @asynccontextmanager
    async def _get_results_context(self, job_id: str) -> AsyncGenerator[Path, str]:
        """Async context manager for safely handling result file lifecycle"""
        batch: Batch = self.client.batches.retrieve(job_id)
        batch_dir: Path = Path("open_ai_batch_results")
        batch_dir.mkdir(exist_ok=True)
        started_at_fmt: str = datetime.fromtimestamp(batch.created_at).strftime(
            format="%Y%m%d-%H:%M:%S"
        )
        file: Path = batch_dir.joinpath(
            f"{started_at_fmt}_{batch.id}_result_{batch.status}.jsonl"
        )

        try:
            byte_stream: str = self.client.files.content(
                batch.output_file_id
            ).content.decode("utf-8")

            with open(file, "w", encoding="utf-8") as f:
                f.write(byte_stream)

            yield file
        finally:
            # Always cleanup, even if exception or early termination
            if batch_dir.exists():
                shutil.rmtree(batch_dir)

    @override
    async def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResultItem]:
        try:
            async with self._get_results_context(job_id) as file:
                with file.open("r", encoding="utf-8") as f:
                    row_idx: int = 0
                    for line in f:
                        l: str = line.strip()
                        try:
                            (
                                campaign_id,
                                file_name,
                                page_num,
                                page_total,
                                entry_number,
                            ) = self._extract_custom_id_parts(l)
                            item: OCREntry = self._extract_response_data(l)
                            result_item: OcrResultItem = OcrResultItem(
                                campaign_id=campaign_id,
                                file_name=file_name,
                                page_num=page_num,
                                row_num=row_idx,
                                ocr_entry=item,
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

        except Exception as e:
            logger.error(f"Failed to save results for open ai batch for {job_id}", e)
            raise e
