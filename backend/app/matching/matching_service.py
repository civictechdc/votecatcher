"""Matching service for fuzzy matching OCR results against voter registration lists.

Implements the matching pipeline from SPEC.md §3.4:
1. Load Voter List → Load OCR Results
2. For each OCR result:
   - DB pre-filter (region, zipcode)
   - Extract name + address components
   - RapidFuzz fuzzy match
   - Calculate weighted similarity score
   - Rank top 5 predictions
   - Store match results with confidence levels
"""

from typing import Any

import structlog
from rapidfuzz import fuzz
from sqlmodel import Session, col, select

from app.data.database.model.jobs import MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.registered_voter import RegisteredVoter
from app.domain.field_spec import RegionFieldSpecConfig, render_template
from app.matching.engines import ScoreAggregator, get_engine
from app.matching.voter_data_adapter import flatten_voter_data

logger = structlog.get_logger(__name__)


class MatchingService:
    """Service for fuzzy matching OCR results against registered voters.

    Confidence Thresholds (defaults, can be calibrated):
        - HIGH: >= 0.85
        - MEDIUM: 0.60 - 0.84
        - LOW: < 0.60

    Attributes:
        session: Database session for queries and persistence
        high_threshold: Minimum score for HIGH confidence (default 0.85)
        medium_threshold: Minimum score for MEDIUM confidence (default 0.60)
        aggregator: ScoreAggregator strategy for combining field scores
    """

    def __init__(
        self,
        session: Session,
        high_threshold: float = 0.85,
        medium_threshold: float = 0.60,
        aggregator: ScoreAggregator | None = None,
    ) -> None:
        self.session = session
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.aggregator = aggregator or get_engine()

    def pre_filter_voters_with_spec(
        self,
        spec: RegionFieldSpecConfig,
        region_id: Any,
        filter_value: str | None = None,
    ) -> list[RegisteredVoter]:
        statement = select(RegisteredVoter).where(
            RegisteredVoter.region_id == region_id
        )

        if filter_value and spec.pre_filter_field_id:
            pf = spec.pre_filter_field()
            if pf:
                blob_attr = (
                    "address_data"
                    if pf.category in ("address",)
                    else "other_field_data"
                )
                if pf.category == "name":
                    blob_attr = "name_data"
                statement = statement.where(
                    col(getattr(RegisteredVoter, blob_attr))[
                        spec.pre_filter_field_id
                    ].as_string()
                    == filter_value
                )

        voters = self.session.exec(statement).all()
        return list(voters)

    def calculate_spec_driven_similarity(
        self,
        spec: RegionFieldSpecConfig,
        ocr_text: dict[str, Any],
        voter: RegisteredVoter,
    ) -> dict[str, Any]:
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        matchable = spec.matchable_fields()

        field_scores: dict[str, float] = {}
        weights: dict[str, float] = {}

        for field in matchable:
            mapping = spec.get_mapping_for(field.id)
            if not mapping:
                continue

            ocr_value = str(ocr_text.get(field.id, ""))
            voter_value = render_template(mapping.template, flat)

            score = fuzz.ratio(ocr_value, voter_value) / 100.0
            field_scores[field.id] = score
            weights[field.id] = field.match_weight

        overall = self.aggregator.aggregate(field_scores, weights)

        return {
            "similarity_score": overall,
            "confidence_level": self.assign_confidence(overall),
            "field_scores": field_scores,
        }

    def assign_confidence(self, similarity_score: float) -> ConfidenceLevel:
        """Assign confidence level based on similarity score.

        Uses thresholds defined in SPEC.md §3.4:
            - HIGH: >= 0.85
            - MEDIUM: 0.60 - 0.84
            - LOW: < 0.60

        Args:
            similarity_score: Similarity score between 0.0 and 1.0

        Returns:
            ConfidenceLevel enum value
        """
        if similarity_score >= self.high_threshold:
            return ConfidenceLevel.HIGH
        elif similarity_score >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def match_ocr_result_with_spec(
        self,
        spec: RegionFieldSpecConfig,
        ocr_text: dict[str, Any],
        region_id: Any,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Spec-driven matching pipeline using dynamic field weights."""
        voters = self.pre_filter_voters_with_spec(
            spec=spec,
            region_id=region_id,
        )

        if not voters:
            logger.warning(
                "No voters found for region",
                region_id=str(region_id),
            )
            return []

        matches: list[dict[str, Any]] = []

        for voter in voters:
            result = self.calculate_spec_driven_similarity(spec, ocr_text, voter)
            matches.append(
                {
                    "voter_id": voter.id,
                    "similarity_score": result["similarity_score"],
                    "confidence_level": result["confidence_level"],
                    "field_scores": result["field_scores"],
                }
            )

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)

        top_matches = matches[:top_n]

        logger.debug(
            "Matched OCR result (spec-driven)",
            top_score=top_matches[0]["similarity_score"] if top_matches else 0,
            matches_returned=len(top_matches),
        )

        return top_matches

    async def run_matching(self, job_id: int) -> dict[str, Any]:
        """Run complete matching pipeline for a matcher job.

        Processes all OCR results associated with the job's campaign
        and creates MatchResult records for top predictions.

        Args:
            job_id: MatcherJob database ID

        Returns:
            Summary dictionary with:
                - total_ocr_results: Number of OCR results processed
                - total_matches_created: Total match results created
                - high_confidence_count: Matches with HIGH confidence
                - medium_confidence_count: Matches with MEDIUM confidence
                - low_confidence_count: Matches with LOW confidence

        Raises:
            ValueError: If job not found
        """
        job = self.session.get(MatcherJob, job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        logger.info(
            "Starting matching pipeline",
            job_id=job_id,
            campaign_id=str(job.campaign_id),
        )

        ocr_results = self.session.exec(
            select(OcrResult)
            .join(MatcherJob, OcrResult.ocr_job_id == MatcherJob.id)
            .where(MatcherJob.campaign_id == job.campaign_id)
        ).all()

        logger.info(
            "Found OCR results to process",
            job_id=job_id,
            ocr_result_count=len(ocr_results),
        )

        total_matches = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        from app.dependencies import get_field_spec_service

        spec_service = next(get_field_spec_service())
        region_key = "DC"
        if hasattr(job.campaign, "region") and job.campaign.region:
            region_key = job.campaign.region.region_key
        spec = spec_service.get_spec_by_key(region_key)

        for ocr_result in ocr_results:
            matches = self.match_ocr_result_with_spec(
                spec=spec,
                ocr_text=ocr_result.extracted_text,
                region_id=job.campaign.region_id,
                top_n=5,
            )

            self.store_match_results(
                ocr_result_id=ocr_result.id,
                matcher_job_id=job_id,
                matches=matches,
            )

            total_matches += len(matches)

            for match in matches:
                if match["confidence_level"] == ConfidenceLevel.HIGH:
                    high_count += 1
                elif match["confidence_level"] == ConfidenceLevel.MEDIUM:
                    medium_count += 1
                else:
                    low_count += 1

        logger.info(
            "Matching pipeline complete",
            job_id=job_id,
            total_matches=total_matches,
            high=high_count,
            medium=medium_count,
            low=low_count,
        )

        return {
            "total_ocr_results": len(ocr_results),
            "total_matches_created": total_matches,
            "high_confidence_count": high_count,
            "medium_confidence_count": medium_count,
            "low_confidence_count": low_count,
        }

    def store_match_results(
        self,
        ocr_result_id: int,
        matcher_job_id: int,
        matches: list[dict[str, Any]],
    ) -> None:
        """Store match results in database.

        Clears any existing match results for the OCR result before
        creating new records.

        Args:
            ocr_result_id: OCR result database ID
            matcher_job_id: Matcher job database ID
            matches: List of match dictionaries from match_ocr_result
        """
        existing = self.session.exec(
            select(MatchResult).where(MatchResult.ocr_result_id == ocr_result_id)
        ).all()

        for match in existing:
            self.session.delete(match)

        self.session.commit()

        for rank, match in enumerate(matches, start=1):
            match_result = MatchResult(
                ocr_result_id=ocr_result_id,
                matcher_job_id=matcher_job_id,
                rank=rank,
                voter_id=match["voter_id"],
                similarity_score=match["similarity_score"],
                confidence_level=match["confidence_level"],
                field_scores=match["field_scores"],
            )
            self.session.add(match_result)

        self.session.commit()

        logger.debug(
            "Stored match results",
            ocr_result_id=ocr_result_id,
            match_count=len(matches),
        )
