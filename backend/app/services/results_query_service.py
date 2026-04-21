"""Results query service for handling match result queries."""

import csv
import io
from collections.abc import Iterator
from typing import TYPE_CHECKING, Optional

from sqlmodel import Session, select

from sqlalchemy import func
from app.services.ocr_text_parser import OcrTextParser
from app.services.prediction_truncation import truncate_predictions
from app.services.results_shared import (
    build_predictions,
    compute_next_cursor,
    enrich_ocr_lookup,
    validate_pagination_params,
)

if TYPE_CHECKING:
    from app.data.database.model.match_result import ConfidenceLevel, MatchResult
    from app.routers.results_router import MatchPrediction, ResultsListResponse


class ResultsQueryService:
    """Service for querying match results."""

    CSV_HEADER = [
        "Crop ID",
        "Extracted Text",
        "Rank",
        "Predicted Name",
        "Predicted Address",
        "Similarity Score",
        "Confidence",
    ]

    def __init__(self, session: Session):
        self._session = session

    def get_results(
        self,
        job_id: int,
        confidence: Optional["ConfidenceLevel"] = None,
        cursor: Optional[int] = None,
        page_size: int = 50,
    ) -> "ResultsListResponse":
        validate_pagination_params(cursor, page_size)

        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import MatchResult
        from app.routers.results_router import (
            MatchPrediction,
            ResultResponse,
            ResultsListResponse,
        )

        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        base_where = [MatchResult.matcher_job_id == job_id]
        if confidence:
            base_where.append(MatchResult.confidence_level == confidence)

        if confidence is None and job.distinct_ocr_count is not None:
            total = job.distinct_ocr_count
        else:
            total = self._session.exec(
                select(func.count()).select_from(
                    select(func.distinct(MatchResult.ocr_result_id))
                    .where(*base_where)
                    .subquery()
                )
            ).one()

        if total == 0:
            return ResultsListResponse(
                results=[], total=0, page_size=page_size, next_cursor=None
            )

        cursor_where = list(base_where)
        if cursor is not None and cursor > 0:
            cursor_where.append(MatchResult.ocr_result_id > cursor)

        paginated_ocr_ids = list(
            self._session.exec(
                select(MatchResult.ocr_result_id)
                .where(*cursor_where)
                .distinct()
                .order_by(MatchResult.ocr_result_id)
                .limit(page_size)
            ).all()
        )

        page_match_results = self._session.exec(
            select(MatchResult).where(
                MatchResult.ocr_result_id.in_(paginated_ocr_ids),
                MatchResult.matcher_job_id == job_id,
            )
        ).all()

        predictions_by_ocr = build_predictions(self._session, page_match_results)
        enrichment_by_ocr = enrich_ocr_lookup(self._session, paginated_ocr_ids)

        results = []
        for ocr_id in paginated_ocr_ids:
            enrichment = enrichment_by_ocr.get(ocr_id)
            raw_preds = truncate_predictions(predictions_by_ocr.get(ocr_id, []))
            predictions = [
                MatchPrediction(
                    rank=p.rank,
                    voter_name=p.voter_name,
                    voter_address=p.voter_address,
                    similarity_score=p.similarity_score,
                    confidence=p.confidence,
                )
                for p in raw_preds
            ]

            results.append(
                ResultResponse(
                    ocr_result_id=ocr_id,
                    extracted_text=enrichment.extracted_text if enrichment else "",
                    crop_id=enrichment.crop_id if enrichment else 0,
                    thumbnail_url=enrichment.thumbnail_url if enrichment else "",
                    predictions=predictions,
                    crop_coordinates=enrichment.crop_coordinates
                    if enrichment
                    else None,
                    entry_coordinates=enrichment.entry_coordinates
                    if enrichment
                    else None,
                    page_number=enrichment.page_number if enrichment else None,
                    document_name=enrichment.document_name if enrichment else "",
                    scan_id=enrichment.scan_id if enrichment else None,
                )
            )

        count_after = 0
        if len(paginated_ocr_ids) == page_size:
            last_id = paginated_ocr_ids[-1]
            next_page_where = list(base_where) + [MatchResult.ocr_result_id > last_id]
            count_after = self._session.exec(
                select(func.count()).select_from(
                    select(func.distinct(MatchResult.ocr_result_id))
                    .where(*next_page_where)
                    .subquery()
                )
            ).one()

        next_cursor = compute_next_cursor(paginated_ocr_ids, page_size, count_after)

        return ResultsListResponse(
            results=results,
            total=total,
            page_size=page_size,
            next_cursor=next_cursor,
        )

    def _build_predictions_from_match_results(
        self, match_results: list["MatchResult"]
    ) -> dict[int, list["MatchPrediction"]]:
        """Build predictions grouped by OCR result ID."""
        from app.routers.results_router import MatchPrediction

        raw = build_predictions(self._session, match_results)

        predictions_by_ocr: dict[int, list[MatchPrediction]] = {}
        for ocr_id, preds in raw.items():
            predictions_by_ocr[ocr_id] = [
                MatchPrediction(
                    rank=p.rank,
                    voter_name=p.voter_name,
                    voter_address=p.voter_address,
                    similarity_score=p.similarity_score,
                    confidence=p.confidence,
                )
                for p in preds
            ]

        return predictions_by_ocr

    def export_results_csv(
        self,
        job_id: int,
        confidence: Optional["ConfidenceLevel"] = None,
        chunk_size: int = 1000,
    ) -> tuple[Iterator[str], str]:
        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import MatchResult

        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        statement = (
            select(MatchResult)
            .where(MatchResult.matcher_job_id == job_id)
            .order_by(MatchResult.ocr_result_id, MatchResult.rank)
        )
        if confidence:
            statement = statement.where(MatchResult.confidence_level == confidence)

        filename = f"job_{job_id}_results.csv"
        generator = self._generate_csv_rows(statement, chunk_size)
        return generator, filename

    @staticmethod
    def _csv_row(values: list) -> str:
        buf = io.StringIO()
        csv.writer(buf).writerow(values)
        return buf.getvalue()

    def _generate_csv_rows(self, statement, chunk_size: int) -> Iterator[str]:
        from app.data.database.model.ocr_result import OcrResult
        from app.data.database.model.registered_voter import RegisteredVoter
        from app.services.prediction_builder import PredictionBuilder

        yield self._csv_row(self.CSV_HEADER)

        match_results = list(self._session.exec(statement).yield_per(chunk_size))

        ocr_ids = {mr.ocr_result_id for mr in match_results}
        voter_ids = {mr.voter_id for mr in match_results if mr.voter_id}

        ocr_cache: dict[int, OcrResult] = {}
        if ocr_ids:
            for batch in self._chunk(sorted(ocr_ids), chunk_size):
                rows = self._session.exec(
                    select(OcrResult).where(OcrResult.id.in_(batch))
                ).all()
                ocr_cache.update({r.id: r for r in rows})

        voter_cache: dict[int, RegisteredVoter] = {}
        if voter_ids:
            for batch in self._chunk(sorted(voter_ids), chunk_size):
                rows = self._session.exec(
                    select(RegisteredVoter).where(RegisteredVoter.id.in_(batch))
                ).all()
                voter_cache.update({r.id: r for r in rows})

        for mr in match_results:
            ocr_result = ocr_cache.get(mr.ocr_result_id)
            extracted_text = (
                OcrTextParser.format_text(ocr_result.extracted_text)
                if ocr_result
                else ""
            )
            crop_id = str(ocr_result.crop_id) if ocr_result else ""

            voter = voter_cache.get(mr.voter_id) if mr.voter_id else None
            voter_name = PredictionBuilder.format_voter_name(voter) if voter else ""
            voter_address = (
                PredictionBuilder.format_voter_address(voter) if voter else ""
            )

            confidence = mr.confidence_level.value if mr.confidence_level else "LOW"
            yield self._csv_row(
                [
                    crop_id,
                    extracted_text,
                    mr.rank,
                    voter_name,
                    voter_address,
                    mr.similarity_score,
                    confidence,
                ]
            )

    @staticmethod
    def _chunk(ids: list[int], size: int) -> Iterator[list[int]]:
        for i in range(0, len(ids), size):
            yield ids[i : i + size]
