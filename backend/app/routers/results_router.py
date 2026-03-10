"""Results router for match results."""

import csv
import io
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.data.database.model.jobs import MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["results"])


SessionDep = Annotated[Session, Depends(get_session)]


class MatchPrediction(BaseModel):
	"""Schema for a single match prediction."""

	rank: int
	voter_name: str
	voter_address: str
	similarity_score: float
	confidence: str


class ResultResponse(BaseModel):
	"""Response schema for a single result."""

	ocr_result_id: int
	extracted_text: str
	crop_id: int
	predictions: list[MatchPrediction]


class ResultsListResponse(BaseModel):
	"""Response schema for paginated results."""

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
	"""Get match results for a job.

	Args:
		job_id: Job ID
		session: Database session
		confidence: Filter by confidence level (optional)
		page: Page number (1-indexed)
		page_size: Items per page

	Returns:
		Paginated match results

	Raises:
		HTTPException: 404 if job not found
	"""
	job = session.get(MatcherJob, job_id)
	if not job:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Job {job_id} not found",
		)

	statement = select(MatchResult).where(MatchResult.matcher_job_id == job_id)

	if confidence:
		statement = statement.where(MatchResult.confidence_level == confidence)

	total_statement = select(MatchResult).where(MatchResult.matcher_job_id == job_id)
	if confidence:
		total_statement = total_statement.where(
			MatchResult.confidence_level == confidence
		)

	total = len(session.exec(total_statement).all())

	offset = (page - 1) * page_size
	statement = statement.offset(offset).limit(page_size)

	match_results = session.exec(statement).all()

	results = []
	for result in match_results:
		predictions = [
			MatchPrediction(
				rank=i + 1,
				voter_name=pred.predicted_voter_name or "",
				voter_address=pred.predicted_address or "",
				similarity_score=pred.similarity_score or 0.0,
				confidence=result.confidence_level.value
				if result.confidence_level
				else "LOW",
			)
			for i, pred in enumerate(result.predictions[:5])
		]

		results.append(
			ResultResponse(
				ocr_result_id=result.ocr_result_id or 0,
				extracted_text=result.ocr_result.extracted_text
				if result.ocr_result
				else "",
				crop_id=result.ocr_result.crop_id if result.ocr_result else 0,
				predictions=predictions,
			)
		)

	return ResultsListResponse(
		results=results,
		total=total,
		page=page,
		page_size=page_size,
	)


@router.get("/{job_id}/results/export")
def export_results_csv(
	job_id: int,
	session: SessionDep,
	confidence: ConfidenceLevel | None = None,
) -> StreamingResponse:
	"""Export match results as CSV.

	Args:
		job_id: Job ID
		session: Database session
		confidence: Filter by confidence level (optional)

	Returns:
		CSV file download

	Raises:
		HTTPException: 404 if job not found
	"""
	job = session.get(MatcherJob, job_id)
	if not job:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Job {job_id} not found",
		)

	statement = select(MatchResult).where(MatchResult.matcher_job_id == job_id)

	if confidence:
		statement = statement.where(MatchResult.confidence_level == confidence)

	match_results = session.exec(statement).all()

	output = io.StringIO()
	writer = csv.writer(output)

	writer.writerow(
		[
			"Crop ID",
			"Extracted Text",
			"Rank",
			"Predicted Name",
			"Predicted Address",
			"Similarity Score",
			"Confidence",
		]
	)

	for result in match_results:
		for i, pred in enumerate(result.predictions[:5]):
			writer.writerow(
				[
					result.ocr_result.crop_id if result.ocr_result else "",
					result.ocr_result.extracted_text if result.ocr_result else "",
					i + 1,
					pred.predicted_voter_name or "",
					pred.predicted_address or "",
					pred.similarity_score or 0.0,
					result.confidence_level.value if result.confidence_level else "LOW",
				]
			)

	output.seek(0)

	return StreamingResponse(
		iter([output.getvalue()]),
		media_type="text/csv",
		headers={
			"Content-Disposition": f"attachment; filename=job_{job_id}_results.csv"
		},
	)
