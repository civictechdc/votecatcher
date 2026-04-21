"""Campaign query service for handling campaign-level result and status queries."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.data.database.model.match_result import MatchResult

from sqlalchemy import func

from app.data.database.model.match_result import ConfidenceLevel
from app.routers.campaign_router import (
    CampaignMatchPrediction,
    CampaignResultResponse,
    CampaignResultsListResponse,
    JobsStatus,
    PetitionsStatus,
    SetupStatusResponse,
    VoterListStatus,
)
from app.services.ocr_text_parser import OcrTextParser
from app.services.prediction_truncation import truncate_predictions
from app.services.results_shared import (
    build_predictions,
    compute_next_cursor,
    enrich_ocr_lookup,
    validate_pagination_params,
)


class CampaignQueryService:
    """Service for querying campaign results and setup status."""

    def __init__(self, session: Session):
        self._session = session

    def get_campaign_results(
        self,
        campaign_id: uuid.UUID,
        confidence: ConfidenceLevel | None = None,
        cursor: int | None = None,
        page_size: int = 50,
    ) -> CampaignResultsListResponse:
        validate_pagination_params(cursor, page_size)

        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import MatchResult
        from app.data.database.model.schema import Campaign

        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        latest_job_id = self._session.exec(
            select(func.max(MatcherJob.id)).where(MatcherJob.campaign_id == campaign_id)
        ).one()

        if latest_job_id is None:
            return CampaignResultsListResponse(
                results=[], total=0, page_size=page_size, next_cursor=None
            )

        base_where = [MatchResult.matcher_job_id == latest_job_id]
        if confidence:
            base_where.append(MatchResult.confidence_level == confidence)

        latest_job = self._session.get(MatcherJob, latest_job_id)

        if confidence is None and latest_job and latest_job.distinct_ocr_count is not None:
            total = latest_job.distinct_ocr_count
        else:
            total = self._session.exec(
                select(func.count()).select_from(
                    select(func.distinct(MatchResult.ocr_result_id))
                    .where(*base_where)
                    .subquery()
                )
            ).one()

        if total == 0:
            return CampaignResultsListResponse(
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
                MatchResult.matcher_job_id == latest_job_id,
            )
        ).all()

        predictions_by_ocr = self._build_campaign_predictions(page_match_results)
        enrichment_by_ocr = enrich_ocr_lookup(self._session, paginated_ocr_ids)

        job_ids_by_ocr: dict[int, int] = {}
        for result in page_match_results:
            if result.ocr_result_id not in job_ids_by_ocr:
                job_ids_by_ocr[result.ocr_result_id] = result.matcher_job_id

        results = []
        for ocr_id in paginated_ocr_ids:
            enrichment = enrichment_by_ocr.get(ocr_id)

            extracted_name = ""
            extracted_address = ""
            if enrichment and enrichment.raw_extracted_text:
                extracted_name, extracted_address = (
                    OcrTextParser.extract_name_and_address(enrichment.raw_extracted_text)
                )

            predictions = truncate_predictions(predictions_by_ocr.get(ocr_id, []))
            job_id = job_ids_by_ocr.get(ocr_id, 0)

            results.append(
                CampaignResultResponse(
                    ocr_result_id=ocr_id,
                    extracted_name=extracted_name,
                    extracted_address=extracted_address,
                    crop_id=enrichment.crop_id if enrichment else 0,
                    job_id=job_id,
                    thumbnail_url=enrichment.thumbnail_url if enrichment else "",
                    predictions=predictions,
                    crop_coordinates=enrichment.crop_coordinates if enrichment else None,
                    entry_coordinates=enrichment.entry_coordinates if enrichment else None,
                    page_number=enrichment.page_number if enrichment else None,
                    document_name=enrichment.document_name if enrichment else "",
                    scan_id=enrichment.scan_id if enrichment else None,
                )
            )

        count_after = 0
        if len(paginated_ocr_ids) == page_size:
            last_id = paginated_ocr_ids[-1]
            next_page_where = [
                MatchResult.matcher_job_id == latest_job_id,
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

        next_cursor = compute_next_cursor(paginated_ocr_ids, page_size, count_after)

        return CampaignResultsListResponse(
            results=results,
            total=total,
            page_size=page_size,
            next_cursor=next_cursor,
        )

    def _build_campaign_predictions(
        self, match_results: list[MatchResult]
    ) -> dict[int, list[CampaignMatchPrediction]]:
        """Build predictions grouped by OCR result ID for campaign results."""
        raw = build_predictions(self._session, match_results)

        predictions_by_ocr: dict[int, list[CampaignMatchPrediction]] = {}
        for ocr_id, preds in raw.items():
            predictions_by_ocr[ocr_id] = [
                CampaignMatchPrediction(
                    rank=p.rank,
                    voter_name=p.voter_name,
                    voter_address=p.voter_address,
                    similarity_score=p.similarity_score,
                    confidence=p.confidence,
                )
                for p in preds
            ]

        return predictions_by_ocr

    def get_setup_status(self, campaign_id: uuid.UUID) -> SetupStatusResponse:
        """Get campaign setup status for progress stepper.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Setup status with voter list, petitions, and job info

        Raises:
            ValueError: If campaign not found
        """
        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.petition_scan import PetitionScan
        from app.data.database.model.schema import Campaign, Region
        from app.services.voter_list_service import VoterListService

        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        voter_list_service = VoterListService(self._session)
        voter_upload = voter_list_service.get_active_upload(campaign.region_id)

        scans = self._session.exec(
            select(PetitionScan).where(PetitionScan.campaign_id == campaign_id)
        ).all()

        jobs = self._session.exec(
            select(MatcherJob).where(MatcherJob.campaign_id == campaign_id)
        ).all()

        has_voter_list = voter_upload is not None
        has_petitions = len(scans) > 0
        has_jobs = len(jobs) > 0

        if not has_voter_list and not has_petitions:
            state = "empty"
        elif has_voter_list and not has_petitions:
            state = "voter_only"
        elif not has_voter_list and has_petitions:
            state = "petitions_only"
        elif not has_jobs:
            state = "ready_to_process"
        else:
            state = "has_jobs"

        region_key = None
        if campaign.region_id:
            region = self._session.get(Region, campaign.region_id)
            region_key = region.region_key if region else None

        return SetupStatusResponse(
            voter_list=VoterListStatus(
                exists=has_voter_list,
                row_count=voter_upload.row_count if voter_upload else None,
                uploaded_at=voter_upload.uploaded_at.isoformat()
                if voter_upload
                else None,
                region_name=region_key,
            ),
            petitions=PetitionsStatus(
                exists=has_petitions,
                file_count=len(scans),
                signature_count=sum(s.page_count or 0 for s in scans),
            ),
            jobs=JobsStatus(
                total=len(jobs),
                active=len(
                    [
                        j
                        for j in jobs
                        if j.current_status
                        in [
                            "NOT_STARTED",
                            "OCR_PENDING",
                            "OCR_STARTED",
                            "MATCHING",
                        ]
                    ]
                ),
            ),
            state=state,
        )
