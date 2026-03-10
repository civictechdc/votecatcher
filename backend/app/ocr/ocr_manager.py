from collections.abc import AsyncGenerator, Iterable
from datetime import UTC, datetime
from typing import Any, Protocol, TypedDict

from pydantic import BaseModel, Field

from app.matching.match_repository import MatchingStatus, MatchingTask
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_client_factory import TEXT_PROMPTS


class OcrResultFieldValues(TypedDict):
	field_name: str
	value: str | int | float | bool


class OcrResult(BaseModel):
	job_id: str = Field()
	campaign_id: str = Field()
	document_path: str = Field()
	page_num: int = Field()
	row_num: int = Field()
	result_parts: list[OcrResultFieldValues] = Field()


class ReadOcrResult(BaseModel):
	page_num: int = Field()
	row_num: int = Field()
	result_parts: list[OcrResultFieldValues] = Field()


# TODO???
class OcrEncodedPage(BaseModel):
	image: str = Field()
	row: int = Field()
	encoded_page: int = Field()
	file_name: str = Field()
	file_id_or_path: str = Field()
	document_file_total: int = Field()


class OcrRequest(BaseModel):
	campaign_id: str = Field()
	provider_id: str = Field()
	task_id: str = Field()
	encoded_pages: list[EncodedPetitionPage] = Field()

	@property
	def total_payload_size(self) -> int:
		return len(self.encoded_pages)


class OcrJobStatus(BaseModel):
	campaign_id: str = Field()
	task_id: str = Field()
	ocr_job_id: str = Field()
	ocr_provider_id: str = Field()
	ocr_model: str | None = Field(default=None)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(default=None)
	ended_at: datetime | None = Field(default=None)
	status_message: str | None = Field(default=None)
	failure_message: str | None = Field(default=None)
	task_status: MatchingStatus = Field(default=MatchingStatus.OCR_PENDING)
	result_data: dict[str, Any] | None = Field(default=None)


class OcrHandler(Protocol):
	async def start_ocr_job(self, ocr_data: OcrRequest) -> MatchingTask: ...

	async def get_job_status(self, job_id: str) -> MatchingTask: ...

	async def get_ocr_results(self, task_id: str) -> Iterable[ReadOcrResult]: ...


class OcrMessageData(BaseModel):
	role: str
	messages: list[dict[str, Any]]
	page: int
	file_name: str


class OcrClient(Protocol):
	async def create_batch_job(self, request_data: OcrRequest) -> OcrJobStatus: ...

	async def fetch_job_status(self, job_id: str) -> OcrJobStatus: ...

	def get_ocr_results(self, job_id: str) -> AsyncGenerator[OcrResult]: ...

	@property
	def provider_id(self) -> str: ...


# TODO: Swap out encoded page
def create_batch_payload(page: EncodedPetitionPage) -> OcrMessageData:
	return OcrMessageData(
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
