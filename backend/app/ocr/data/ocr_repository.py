from collections.abc import AsyncGenerator, Iterable
from dataclasses import dataclass
from typing import Protocol

from app.data.database.model.ocr_model import (
    CreateOcrJob,
    OcrJob,
    ReadOcrJobStatus,
    UpdateOcrJobStatus,
)
from app.matching.match_repository import MatchingStatus, MatchingTask
from app.ocr.data.data_models import OcrResultItem
from app.ocr.ocr_manager import OcrClient


class OcrResultRepository(Protocol):
    async def save_results(
        self, campaign_id: str, results: Iterable[OcrResultItem]
    ) -> Iterable[OcrResultItem]:
        raise NotImplementedError("This function should be implemented")

    async def fetch_results(self, campaign_id: str) -> Iterable[OcrResultItem]:
        raise NotImplementedError("This function should be implemented")


class OcrJobRepository(Protocol):
    async def save_ocr_job(self, ocr_job: CreateOcrJob) -> OcrJob: ...

    async def update_ocr_job_status(self, ocr_job: UpdateOcrJobStatus) -> OcrJob: ...

    async def get_ocr_job_status(self, job_id: str) -> ReadOcrJobStatus: ...


@dataclass
class RegisterOcrJob:
    job_id: str
    campaign_id: str
    provider_id: str
    request_payload: str
    crop_file_id: str


@dataclass
class UpdateOcrJob:
    job_id: str
    status: MatchingStatus
    error_message: str | None = None
    status_message: str | None = None


class OcrManager(Protocol):
    async def start_ocr_job(
        self, ocr_client: OcrClient, ocr_data: RegisterOcrJob
    ) -> MatchingTask: ...

    async def update_status(self, ocr_status: UpdateOcrJob) -> MatchingTask: ...

    async def get_job_status(self, job_id: str) -> MatchingTask: ...

    def monitor_job(self, job_id: str) -> AsyncGenerator[MatchingTask]: ...
