from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field


class MatchingStatus(StrEnum):
	NOT_STARTED = "not started"
	PENDING = "pending"
	OCR_PENDING = "ocr_pending"
	OCR_IN_PROGRESS = "ocr extract"
	MATCHING = "matching"
	COMPLETED = "completed"
	OCR_COMPLETED = "ocr_completed"
	OCR_FAILED = "ocr_failed"
	MATCHING_FAILED = "matching failed"
	OCR_TIMED_OUT = "ocr timed out"
	OCR_CANCELLED = "ocr cancelled"
	CANCELLED = "cancelled"
	TIMED_OUT = "timed out"
	MISC_ERROR = "error"


def is_terminal_matching_status(status: MatchingStatus) -> bool:
	return status in {
		MatchingStatus.COMPLETED,
		MatchingStatus.CANCELLED,
		MatchingStatus.OCR_CANCELLED,
		MatchingStatus.OCR_FAILED,
		MatchingStatus.MATCHING_FAILED,
		MatchingStatus.OCR_TIMED_OUT,
		MatchingStatus.TIMED_OUT,
		MatchingStatus.MISC_ERROR,
	}


class MatchingTask(BaseModel):
	id: str
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(default=None)
	ended_at: datetime | None = None
	status: MatchingStatus = MatchingStatus.NOT_STARTED
	status_message: str | None = None
	failure_message: str | None = None
	ocr_result_data: str | None = None
	campaign_id: str

	def has_failed(self) -> bool:
		return self.status in {
			MatchingStatus.CANCELLED,
			MatchingStatus.OCR_CANCELLED,
			MatchingStatus.MATCHING_FAILED,
			MatchingStatus.OCR_FAILED,
			MatchingStatus.OCR_TIMED_OUT,
			MatchingStatus.TIMED_OUT,
			MatchingStatus.MISC_ERROR,
		}

	def has_ended(self) -> bool:
		return self.status in {
			MatchingStatus.COMPLETED,
			MatchingStatus.CANCELLED,
			MatchingStatus.OCR_CANCELLED,
			MatchingStatus.OCR_FAILED,
			MatchingStatus.MATCHING_FAILED,
			MatchingStatus.OCR_TIMED_OUT,
			MatchingStatus.TIMED_OUT,
			MatchingStatus.MISC_ERROR,
			MatchingStatus.OCR_COMPLETED,
		}

	def is_in_progress(self) -> bool:
		return self.status != MatchingStatus.NOT_STARTED and not self.has_ended()


class CreateMatchingTask(BaseModel):
	status_message: str | None = None
	campaign_id: str


class UpdateMatchingTask(BaseModel):
	task_id: str
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	ended_at: datetime | None = None
	status: MatchingStatus
	status_message: str | None = None
	failure_message: str | None = None
	ocr_result_data: str | None = None


class MatchTaskRepository(Protocol):
	async def register_matching_task(
		self, task: CreateMatchingTask
	) -> MatchingTask: ...

	async def update_matching_task_status(
		self, task: UpdateMatchingTask
	) -> MatchingTask: ...

	async def get_matching_task(self, task_id: str) -> MatchingTask: ...

	async def get_completed_task_for_campaign(
		self, campaign_id: str
	) -> Iterable[MatchingTask]: ...


class CreateColumnSpec(BaseModel):
	name: str
	data_type: str
	position_index: int
	is_sortable: bool = Field(default=False)
	campaign_id: str


class ReadColumnSpec(BaseModel):
	name: str
	data_type: str
	position_index: int
	is_sortable: bool
	campaign_id: str


class CreateMatchResult(BaseModel):
	fuzzy_match_threshold: float
	match_score: float
	petition_page_number: int
	petition_row_number: int
	petition_file_name: str
	row_values: dict[str, str | bool | int | float | None]
	ocr_result_id: str
	campaign_id: str


class ReadMatchResult(BaseModel):
	fuzzy_match_threshold: float
	match_score: float
	petition_page_number: int
	petition_row_number: int
	petition_file_name: str
	row_values: dict[str, str | bool | int | float | None]
	ocr_result_id: str
	campaign_id: str


class EntryMatchRepository(Protocol):
	async def create_column_spec(self, column_spec: CreateColumnSpec) -> str | UUID: ...

	async def fetch_column_spec(self, campaign_id: str) -> Iterable[ReadColumnSpec]: ...

	async def save_match_results(
		self, matches: Iterable[CreateMatchResult]
	) -> None: ...

	async def fetch_match_results(
		self, campaign_id: str
	) -> Iterable[ReadMatchResult]: ...
