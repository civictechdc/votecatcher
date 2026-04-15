"""Results query service for handling match result queries."""

import csv
import io
from typing import TYPE_CHECKING, Optional

from sqlmodel import Session, select

from app.services.ocr_text_parser import OcrTextParser

if TYPE_CHECKING:
    from app.data.database.model.match_result import ConfidenceLevel, MatchResult
    from app.routers.results_router import MatchPrediction, ResultsListResponse


class ResultsQueryService:
    """Service for querying match results."""

    def __init__(self, session: Session):
        self._session = session

    def get_results(
        self,
        job_id: int,
        confidence: Optional["ConfidenceLevel"] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> "ResultsListResponse":
        """Get match results for a job.

        Args:
            job_id: Job ID
            confidence: Filter by confidence level (optional)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated match results

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

        total_statement = select(MatchResult).where(
            MatchResult.matcher_job_id == job_id
        )
        if confidence:
            total_statement = total_statement.where(
                MatchResult.confidence_level == confidence
            )

        all_match_results = self._session.exec(total_statement).all()
        total = len({r.ocr_result_id for r in all_match_results})

        ocr_result_ids = sorted({r.ocr_result_id for r in all_match_results})
        offset = (page - 1) * page_size
        paginated_ocr_ids = ocr_result_ids[offset : offset + page_size]

        page_match_results = [
            r for r in all_match_results if r.ocr_result_id in paginated_ocr_ids
        ]

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

        results = []
        for ocr_id in paginated_ocr_ids:
            ocr_result = ocr_results_by_id.get(ocr_id)

            extracted_text = ""
            crop_id = 0
            if ocr_result:
                if isinstance(ocr_result.extracted_text, dict):
                    text_parts = []
                    for key in sorted(ocr_result.extracted_text.keys()):
                        val = ocr_result.extracted_text.get(key)
                        if val:
                            text_parts.append(str(val))
                    extracted_text = " ".join(text_parts)
                elif ocr_result.extracted_text:
                    extracted_text = str(ocr_result.extracted_text)
                crop_id = ocr_result.crop_id

            predictions = predictions_by_ocr.get(ocr_id, [])[:5]

            results.append(
                ResultResponse(
                    ocr_result_id=ocr_id,
                    extracted_text=extracted_text,
                    crop_id=crop_id,
                    predictions=predictions,
                )
            )

        return ResultsListResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size,
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
    ):
        from fastapi.responses import StreamingResponse

        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import MatchResult
        from app.data.database.model.ocr_result import OcrResult

        job = self._session.get(MatcherJob, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        statement = select(MatchResult).where(MatchResult.matcher_job_id == job_id)
        if confidence:
            statement = statement.where(MatchResult.confidence_level == confidence)

        match_results = self._session.exec(statement).all()
        predictions_by_ocr = self._build_predictions_from_match_results(match_results)

        ocr_ids_to_fetch = {r.ocr_result_id for r in match_results}
        ocr_results_by_id: dict[int, OcrResult] = {}
        if ocr_ids_to_fetch:
            ocr_results = self._session.exec(
                select(OcrResult).where(OcrResult.id.in_(ocr_ids_to_fetch))
            ).all()
            ocr_results_by_id = {o.id: o for o in ocr_results}

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

        for ocr_id in sorted(predictions_by_ocr.keys()):
            ocr_result = ocr_results_by_id.get(ocr_id)

            extracted_text = ""
            crop_id = ""
            if ocr_result:
                extracted_text = OcrTextParser.format_text(ocr_result.extracted_text)
                crop_id = str(ocr_result.crop_id)

            predictions = predictions_by_ocr.get(ocr_id, [])[:5]
            for pred in predictions:
                writer.writerow(
                    [
                        crop_id,
                        extracted_text,
                        pred.rank,
                        pred.voter_name,
                        pred.voter_address,
                        pred.similarity_score,
                        pred.confidence,
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
