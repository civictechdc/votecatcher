"""Match-results API response models."""

from app.api_models import ApiModel
from app.data.database.model.match_result import ConfidenceLevel


class MatchPrediction(ApiModel):
    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: ConfidenceLevel


class ResultResponse(ApiModel):
    ocr_result_id: int
    extracted_text: str
    crop_id: int
    thumbnail_url: str
    predictions: list[MatchPrediction]
    crop_coordinates: dict[str, float] | None = None
    entry_coordinates: dict[str, float] | None = None
    page_number: int | None = None
    document_name: str = ""
    scan_id: int | None = None


class ResultsListResponse(ApiModel):
    results: list[ResultResponse]
    total: int
    page_size: int
    next_cursor: int | None = None
