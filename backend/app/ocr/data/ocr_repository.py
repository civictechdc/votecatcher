from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from app.ocr.data_model import OCREntry
from pydantic import BaseModel, Field


class OcrResultItem(BaseModel):
    campaign_id: str
    file_name: str
    page_num: int
    row_num: int
    ocr_entry: OCREntry


class OcrResult(BaseModel):
    campaign_id: str
    columns_order: list[str] = Field(default_factory=list)
    result_items: list[OcrResultItem] = Field(default_factory=list)


class OcrResultRepository(Protocol):

    async def save_results(
        self, campaign_id: str, results: Iterable[OcrResultItem]
    ) -> Iterable[OcrResultItem]:
        raise NotImplementedError(f"This function should be implemented")

    async def fetch_results(self, campaign_id: str) -> Iterable[OcrResultItem]:
        raise NotImplementedError(f"This function should be implemented")
