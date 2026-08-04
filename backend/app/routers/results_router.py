"""Results router for match results."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.data.database.model.match_result import ConfidenceLevel
from app.dependencies import get_session
from app.responses.results import MatchPrediction as MatchPrediction
from app.responses.results import ResultResponse as ResultResponse
from app.responses.results import ResultsListResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["results"])


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/{job_id}/results", response_model=ResultsListResponse)
def get_results(
    job_id: int,
    session: SessionDep,
    confidence: ConfidenceLevel | None = None,
    cursor: int | None = None,
    page_size: int = 50,
) -> ResultsListResponse:
    from app.services.results_query_service import ResultsQueryService

    try:
        return ResultsQueryService(session).get_results(
            job_id, confidence=confidence, cursor=cursor, page_size=page_size
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
