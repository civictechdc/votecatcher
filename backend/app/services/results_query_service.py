"""Results query service for handling match result queries."""

import csv
import io
from collections.abc import Iterator
from typing import TYPE_CHECKING, Optional

from sqlmodel import Session, select

from sqlalchemy import func
from app.services.entry_coordinates import compute_entry_coordinates
from app.services.ocr_text_parser import OcrTextParser
from app.services.prediction_truncation import truncate_predictions

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
        """Get match results for a job.

        Args:
            job_id: Job ID
            confidence: Filter by confidence level (optional)
            cursor: ocr_result_id to start after (keyset pagination). None starts from beginning.
            page_size: Items per page

        Returns:
            Paginated match results with next_cursor for keyset pagination

        Raises:
            ValueError: If job not found
        """
        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import MatchResult
        from app.data.database.model.ocr_result import OcrResult
        from app.routers.results_router import ResultResponse, ResultsListResponse

        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        base_where = [MatchResult.matcher_job_id == job_id]
        if confidence:
            base_where.append(MatchResult.confidence_level == confidence)

        total = self._session.exec(
            select(func.count()).select_from(
                select(func.distinct(MatchResult.ocr_result_id))
                .where(*base_where)
                .subquery()
            )
        ).one()

        if total == 0:
            from app.routers.results_router import ResultsListResponse

            return ResultsListResponse(
                results=[], total=0, page_size=page_size, next_cursor=None
            )

        if cursor is not None and cursor > 0:
            base_where.append(MatchResult.ocr_result_id > cursor)

        paginated_ocr_ids = list(
            self._session.exec(
                select(MatchResult.ocr_result_id)
                .where(*base_where)
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

        predictions_by_ocr = self._build_predictions_from_match_results(
            page_match_results
        )

        ocr_ids_to_fetch = {r.ocr_result_id for r in page_match_results}
        ocr_results_by_id: dict[int, OcrResult] = {}

        if ocr_ids_to_fetch:
            ocr_results = self._session.exec(
                select(OcrResult).where(OcrResult.id.in_(ocr_ids_to_fetch))
            ).all()
            ocr_results_by_id = {o.id: o for o in ocr_results}

        crop_ids = {o.crop_id for o in ocr_results_by_id.values() if o.crop_id}
        crop_by_id: dict[int, "PetitionCrop"] = {}
        scan_by_id: dict[int, "PetitionScan"] = {}

        if crop_ids:
            from app.data.database.model.petition_crop import PetitionCrop

            crops = self._session.exec(
                select(PetitionCrop).where(PetitionCrop.id.in_(crop_ids))
            ).all()
            crop_by_id = {c.id: c for c in crops}

            scan_ids = {c.scan_id for c in crops}
            if scan_ids:
                from app.data.database.model.petition_scan import PetitionScan

                scans = self._session.exec(
                    select(PetitionScan).where(PetitionScan.id.in_(scan_ids))
                ).all()
                scan_by_id = {s.id: s for s in scans}

        results = []
        for ocr_id in paginated_ocr_ids:
            ocr_result = ocr_results_by_id.get(ocr_id)

            extracted_text = (
                OcrTextParser.format_text(ocr_result.extracted_text)
                if ocr_result
                else ""
            )
            crop_id = ocr_result.crop_id if ocr_result else 0
            thumbnail_url = f"/api/crops/{crop_id}/image" if crop_id else ""

            crop = crop_by_id.get(crop_id) if crop_id else None
            scan = scan_by_id.get(crop.scan_id) if crop else None
            crop_coords = crop.crop_coordinates if crop else None

            predictions = truncate_predictions(predictions_by_ocr.get(ocr_id, []))

            results.append(
                ResultResponse(
                    ocr_result_id=ocr_id,
                    extracted_text=extracted_text,
                    crop_id=crop_id,
                    thumbnail_url=thumbnail_url,
                    predictions=predictions,
                    crop_coordinates=crop_coords,
                    entry_coordinates=(
                        compute_entry_coordinates(crop_coords, ocr_result.ocr_index)
                        if crop_coords and ocr_result
                        else None
                    ),
                    page_number=crop.page_number if crop else None,
                    document_name=scan.original_filename if scan else "",
                    scan_id=crop.scan_id if crop else None,
                )
            )

        next_cursor = None
        if len(paginated_ocr_ids) == page_size:
            last_id = paginated_ocr_ids[-1]
            next_page_where = [
                MatchResult.matcher_job_id == job_id,
                MatchResult.ocr_result_id > last_id,
            ]
            if confidence:
                next_page_where.append(MatchResult.confidence_level == confidence)
            count_after = self._session.exec(
                select(func.count()).select_from(
                    select(func.distinct(MatchResult.ocr_result_id))
                    .where(*next_page_where)
                    .subquery()
                )
            ).one()
            if count_after:
                next_cursor = last_id

        return ResultsListResponse(
            results=results,
            total=total,
            page_size=page_size,
            next_cursor=next_cursor,
        )

    def _build_predictions_from_match_results(
        self, match_results: list["MatchResult"]
    ) -> dict[int, list["MatchPrediction"]]:
        """Build predictions grouped by OCR result ID.

        Args:
            match_results: List of MatchResult records

        Returns:
            Dict mapping ocr_result_id to list of predictions
        """
        from app.data.database.model.registered_voter import RegisteredVoter
        from app.routers.results_router import MatchPrediction
        from app.services.prediction_builder import PredictionBuilder

        voter_ids = {r.voter_id for r in match_results if r.voter_id}
        voters_by_id: dict[int, RegisteredVoter] = {}

        if voter_ids:
            voters = self._session.exec(
                select(RegisteredVoter).where(RegisteredVoter.id.in_(voter_ids))
            ).all()
            voters_by_id = {v.id: v for v in voters}

        raw_predictions = PredictionBuilder.build(match_results, voters_by_id)

        predictions_by_ocr: dict[int, list[MatchPrediction]] = {}
        for ocr_id, preds in raw_predictions.items():
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
            voter_address = PredictionBuilder.format_voter_address(voter) if voter else ""

            confidence = (
                mr.confidence_level.value if mr.confidence_level else "LOW"
            )
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
