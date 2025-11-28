import shutil
from collections.abc import AsyncGenerator, Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from multiprocessing import Value
from pathlib import Path
from typing import Any, Iterable

import structlog
from app.logging.app_logger import AppLogger
from app.ocr.batching.batch_ocr_client import (
    BatchJobStatus,
    BatchOcrClient,
    JobStatus,
    OcrJobMonitor,
)
from app.ocr.batching.gemini_ocr_batch import create_gemini_batch_job
from app.ocr.batching.memory_job_monitor import get_default_monitor
from app.ocr.batching.openai_ocr_batch import OpenAiBatchClient
from app.ocr.batching.request_types import (
    BatchEncodedImage,
    BatchOcrRequestInput,
    BatchRequestPayload,
    Payload,
)
from app.ocr.data.ocr_memory_storage import get_memory_ocr_result_repository
from app.ocr.data.ocr_repository import OcrResultItem, OcrResultRepository
from app.ocr.data_model import EncodedPetitionPage, OCREntry
from app.ocr.ocr_client_factory import TEXT_PROMPTS
from app.settings import GeminiAiConfig, MistralAiConfig, OpenAiConfig
from app.settings.settings_repo import override_settings

logger = structlog.get_logger(__name__)

BATCH_JSONL_FOLDER: Path = Path("batch")

BATCH_JOB_MONITOR: OcrJobMonitor = get_default_monitor()

_current_ocr_client: BatchOcrClient | None = None


def get_ocr_provider_config(
    provider_name: str,
    api_key: str,
    model_name: str,
    override_existing_settings: bool = False,
) -> OpenAiConfig | GeminiAiConfig | MistralAiConfig:

    # Temporary shortcut to set the OCR provider without config
    config: OpenAiConfig | GeminiAiConfig | MistralAiConfig | None = None
    if provider_name:
        match provider_name:
            case "open_ai":
                config = OpenAiConfig(api_key=api_key, model=model_name)
            case "mistral_ai":
                config = MistralAiConfig(api_key=api_key, model=model_name)
            case "gemini_ai":
                config = GeminiAiConfig(api_key=api_key, model=model_name)
            case _:
                raise ValueError(
                    f"Provider name {provider_name} is invalid. Please use an authorised OCR provider.",
                )

    if config is None:
        raise ValueError(f"OCR provider config not set.")

    if override_existing_settings:
        override_settings(config)

    return config


def _create_batch_ocr_client(
    config: OpenAiConfig | GeminiAiConfig | MistralAiConfig,
) -> BatchOcrClient:
    match config:
        case GeminiAiConfig():
            raise NotImplementedError()
        case OpenAiConfig():
            return OpenAiBatchClient(config=config, result_store=_get_result_storage())
        case MistralAiConfig():
            raise NotImplementedError()


def _get_result_storage() -> OcrResultRepository:
    return get_memory_ocr_result_repository()


def get_current_ocr_client() -> BatchOcrClient:
    global _current_ocr_client
    if _current_ocr_client is None:
        raise ValueError(f"OCR Batch client was not initialised.")
    return _current_ocr_client


async def _save_ocr_results(ocr_job: BatchJobStatus) -> None:
    client: BatchOcrClient = get_current_ocr_client()
    results: list[OcrResultItem] = [
        item async for item in client.get_ocr_results(ocr_job.job_id)
    ]
    saved_results: Iterable[OcrResultItem] = await _get_result_storage().save_results(
        campaign_id=ocr_job.campaign_id, results=results
    )
    logger.debug(f"Saved {len(list[OcrResultItem](saved_results))} results.")


def _create_batch_payload(page: EncodedPetitionPage) -> Payload:
    return Payload(
        role="user",
        messages=[
            {
                "type": "text",
                "text": TEXT_PROMPTS[0],
            },
            {
                "type": "text",
                "text": TEXT_PROMPTS[1],
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{page.encoded_page}"},
            },
        ],
        page=page.page_num,
        file_name=page.petition_file_name,
    )


async def create_batch_payload(
    config: OpenAiConfig | GeminiAiConfig | MistralAiConfig,
    request_data: BatchOcrRequestInput,
) -> BatchJobStatus:
    content_batch: list[Payload] = [
        _create_batch_payload(img)
        for img in request_data.encoded_petition_pages.encoded_pages
    ]

    if BATCH_JSONL_FOLDER.exists():
        shutil.rmtree(BATCH_JSONL_FOLDER)

    if not BATCH_JSONL_FOLDER.exists():
        BATCH_JSONL_FOLDER.mkdir(exist_ok=True)

    batch_request: BatchRequestPayload = BatchRequestPayload(
        campaign_id=request_data.campaign_id, batch_payloads=content_batch
    )

    global _current_ocr_client
    client: BatchOcrClient = _create_batch_ocr_client(config)
    _current_ocr_client = client
    job: BatchJobStatus = await client.create_batch_job(
        request_data=batch_request,
        jsonl_path=BATCH_JSONL_FOLDER,
    )
    return await BATCH_JOB_MONITOR.register_job(
        job_id=job.job_id, provider_client=client
    )


async def save_completed_batch(
    campaign_id: str, results: Iterable[OcrResultItem]
) -> Iterable[OcrResultItem]:
    return await _get_result_storage().save_results(campaign_id, results)


async def get_ocr_results(campaign_id: str) -> Iterable[OcrResultItem]:
    return await _get_result_storage().fetch_results(campaign_id)


async def get_current_batch_job_status(job_id: str) -> BatchJobStatus:
    return await BATCH_JOB_MONITOR.get_job_status(job_id)


async def observe_batch_job_status(job_id: str) -> AsyncGenerator[BatchJobStatus, None]:

    try:
        async for job in BATCH_JOB_MONITOR.monitor_job(job_id):

            match job.status:
                case (
                    JobStatus.COMPLETED
                    | JobStatus.CANCELLED
                    | JobStatus.FAILED
                    | JobStatus.EXPIRED
                ):
                    logger.info(
                        f"Job completed with status {job.status}", job_id=job_id
                    )
                    _ = await _save_ocr_results(job)
                    yield job
                    break
                case _:
                    yield job
                    break
    except Exception as e:
        logger.error(f"Job failed with exception", exception=e)
        yield BatchJobStatus(
            job_id=job_id,
            campaign_id="",
            status=JobStatus.FAILED,
            provider_id="",
            completed_at=datetime.now(timezone.utc),
            error=str(e),
        )


async def stream_ocr_result(
    job_id: str, config: OpenAiConfig | GeminiAiConfig | MistralAiConfig
) -> AsyncGenerator[OcrResultItem, None]:
    client: BatchOcrClient = _create_batch_ocr_client(config)
    result: AsyncGenerator[OcrResultItem, None] = client.get_ocr_results(job_id)
    return result
