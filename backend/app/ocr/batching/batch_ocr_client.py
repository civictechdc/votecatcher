from abc import ABC, ABCMeta, abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from pathlib import Path

from app.ocr.batching.request_types import BatchRequestPayload
from app.ocr.data.ocr_repository import OcrResultItem
from app.ocr.data_model import OCREntry
from pydantic import BaseModel, Field, field_serializer


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BatchJobStatus(BaseModel):
    job_id: str
    campaign_id: str
    status: JobStatus
    provider_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    last_updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    error: str | None = None
    result_url: str | None = None

    @field_serializer("completed_at", "started_at", when_used="json")
    def datestring(self, value: datetime) -> str:
        return value.isoformat()


class BatchOcrClient(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "create_batch_job")
            and callable(subclass.create_batch_job)
            and hasattr(subclass, "get_job_status")
            and callable(subclass.get_job_status)
            and hasattr(subclass, "get_ocr_results")
            and callable(subclass.get_ocr_results)
            or NotImplemented
        )

    @abstractmethod
    async def create_batch_job(
        self, request_data: BatchRequestPayload, jsonl_path: Path
    ) -> BatchJobStatus:
        """Load in the data set"""
        raise NotImplementedError

    @abstractmethod
    async def get_job_status(self, job_id: str) -> BatchJobStatus:
        """Extract text from the data set"""
        raise NotImplementedError

    @abstractmethod
    def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResultItem]:
        """Extract text from the data set"""
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError


class OcrJobMonitor(ABC):
    @abstractmethod
    async def register_job(
        self, job_id: str, provider_client: BatchOcrClient
    ) -> BatchJobStatus:
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self, job_id: str, status: JobStatus, error: str | None = None
    ) -> BatchJobStatus:
        raise NotImplementedError

    @abstractmethod
    async def get_job_status(self, job_id: str) -> BatchJobStatus:
        """
        Return the current snapshot for job_id.
        """
        raise NotImplementedError

    @abstractmethod
    def monitor_job(self, job_id: str) -> AsyncGenerator[BatchJobStatus, None]:
        """
        Async generator yielding BatchJobStatus snapshots until the job reaches a terminal state.
        """
        pass
