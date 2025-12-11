from collections.abc import Iterable
from typing import Any, override

import structlog
from app.data.memory_db import get_memory_db
from app.ocr.data.data_models import OCREntry, OcrResultItem
from app.ocr.data.ocr_repository import OcrResultRepository

logger = structlog.getLogger(__name__)


class InMemoryOcrResultRepo(OcrResultRepository):

    def __init__(
        self, result_holder: dict[str, Iterable[OcrResultItem] | Any] | None = None
    ) -> None:
        self._results: dict[str, Iterable[OcrResultItem]] = (
            result_holder if result_holder else {}
        )

    @override
    async def save_results(
        self, campaign_id: str, results: Iterable[OcrResultItem]
    ) -> Iterable[OcrResultItem]:
        self._results[campaign_id] = results
        logger.info(
            f"Saved {len(list[OcrResultItem](results))} results for campaign {campaign_id}."
        )
        return self._results[campaign_id]

    @override
    async def fetch_results(self, campaign_id: str) -> Iterable[OcrResultItem]:
        return self._results[campaign_id]


_memory_ocr_result_storage: InMemoryOcrResultRepo | None = None


def get_memory_ocr_result_repository() -> OcrResultRepository:
    global _memory_ocr_result_storage
    if _memory_ocr_result_storage is None:
        _memory_ocr_result_storage = InMemoryOcrResultRepo(get_memory_db())
    return _memory_ocr_result_storage
