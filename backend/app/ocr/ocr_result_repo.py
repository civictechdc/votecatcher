from collections.abc import Iterable
from typing import Protocol

from pydantic import BaseModel
from sqlmodel import Field

from app.ocr.ocr_manager import OcrResult, ReadOcrResult


class CreateOcrResult(BaseModel):
	task_id: str = Field()
	ocr_job_id: str = Field()
	ocr_result: OcrResult = Field()


class OcrResultRepository(Protocol):
	async def save_ocr_result(self, result_data: CreateOcrResult) -> str: ...

	async def save_ocr_results(self, results: Iterable[CreateOcrResult]) -> None: ...

	async def fetch_ocr_results_by_task(
		self, task_id: str
	) -> Iterable[ReadOcrResult]: ...
