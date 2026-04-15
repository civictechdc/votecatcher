"""Results router for match results."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api_models import ApiModel
from app.data.database.model.match_result import ConfidenceLevel
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["results"])


SessionDep = Annotated[Session, Depends(get_session)]


class MatchPrediction(ApiModel):
    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: str


class ResultResponse(ApiModel):
    ocr_result_id: int
    extracted_text: str
    crop_id: int
    thumbnail_url: str
    predictions: list[MatchPrediction]


class ResultsListResponse(ApiModel):
    results: list[ResultResponse]
    total: int
    page: int
    page_size: int


@router.get("/{job_id}/results", response_model=ResultsListResponse)
def get_results(
    job_id: int,
    session: SessionDep,
    confidence: ConfidenceLevel | None = None,
    page: int = 1,
    page_size: int = 50,
) -> ResultsListResponse:
    from app.services.results_query_service import ResultsQueryService

    try:
        return ResultsQueryService(session).get_results(
            job_id, confidence=confidence, page=page, page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{job_id}/results/export")
def export_results_csv(
    job_id: int,
    session: SessionDep,
    confidence: ConfidenceLevel | None = None,
) -> StreamingResponse:
    from app.services.results_query_service import ResultsQueryService

    try:
        generator, filename = ResultsQueryService(session).export_results_csv(
            job_id, confidence=confidence
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
