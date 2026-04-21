"""Campaign query service for handling campaign-level result and status queries."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.data.database.model.match_result import MatchResult

from sqlalchemy import func

from app.routers.campaign_router import (
    CampaignMatchPrediction,
    CampaignResultResponse,
    CampaignResultsListResponse,
    JobsStatus,
    PetitionsStatus,
    SetupStatusResponse,
    VoterListStatus,
)
from app.services.entry_coordinates import compute_entry_coordinates
from app.services.ocr_text_parser import OcrTextParser
from app.services.prediction_truncation import truncate_predictions


class CampaignQueryService:
    """Service for querying campaign results and setup status."""

    def __init__(self, session: Session):
        self._session = session

    def get_campaign_results(
        self,
        campaign_id: uuid.UUID,
        confidence: str | None = None,
        cursor: int | None = None,
        page_size: int = 50,
    ) -> CampaignResultsListResponse:
        """Get match results for all jobs in a campaign.

        Args:
            campaign_id: Campaign UUID
            confidence: Filter by confidence level (HIGH/MEDIUM/LOW, optional)
            cursor: ocr_result_id to start after (keyset pagination). None starts from beginning.
            page_size: Items per page

        Returns:
            Paginated match results for the campaign with next_cursor

        Raises:
            ValueError: If campaign not found
        """
        from app.data.database.model.jobs import MatcherJob
        from app.data.database.model.match_result import ConfidenceLevel, MatchResult
        from app.data.database.model.ocr_result import OcrResult
        from app.data.database.model.schema import Campaign

        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        job_ids_statement = (
            select(MatcherJob.id)
            .where(MatcherJob.campaign_id == campaign_id)
            .order_by(MatcherJob.id.desc())
        )
        job_ids: list[int] = list(self._session.exec(job_ids_statement).all())

        if not job_ids:
            return CampaignResultsListResponse(
                results=[], total=0, page_size=page_size, next_cursor=None
            )

        latest_job_id = job_ids[0]

        confidence_filter = None
        if confidence:
            try:
                confidence_filter = ConfidenceLevel(confidence.upper())
            except ValueError:
                confidence_filter = None

        base_where = [MatchResult.matcher_job_id == latest_job_id]
        if confidence_filter:
            base_where.append(MatchResult.confidence_level == confidence_filter)

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

        job_ids_by_ocr: dict[int, int] = {}
        for result in page_match_results:
            if result.ocr_result_id not in job_ids_by_ocr:
                job_ids_by_ocr[result.ocr_result_id] = result.matcher_job_id

        ocr_ids_to_fetch = set(paginated_ocr_ids)
        ocr_results_by_id: dict[int, OcrResult] = {}

        if ocr_ids_to_fetch:
            ocr_results = self._session.exec(
                select(OcrResult).where(OcrResult.id.in_(ocr_ids_to_fetch))
            ).all()
            ocr_results_by_id = {o.id: o for o in ocr_results}

        crop_ids = {o.crop_id for o in ocr_results_by_id.values() if o.crop_id}
        crop_by_id: dict = {}
        scan_by_id: dict = {}

        if crop_ids:
            from app.data.database.model.petition_crop import PetitionCrop

            crops = self._session.exec(
                select(PetitionCrop).where(PetitionCrop.id.in_(crop_ids))
            ).all()
            crop_by_id = {c.id: c for c in crops}

            scan_ids = {c.scan_id for c in crops if c.scan_id}
            if scan_ids:
                from app.data.database.model.petition_scan import PetitionScan

                scans = self._session.exec(
                    select(PetitionScan).where(PetitionScan.id.in_(scan_ids))
                ).all()
                scan_by_id = {s.id: s for s in scans}

        results = []
        for ocr_id in paginated_ocr_ids:
            ocr_result = ocr_results_by_id.get(ocr_id)

            extracted_name = ""
            extracted_address = ""
            crop_id = 0
            if ocr_result:
                extracted_name, extracted_address = (
                    OcrTextParser.extract_name_and_address(ocr_result.extracted_text)
                )
                crop_id = ocr_result.crop_id

            predictions = truncate_predictions(predictions_by_ocr.get(ocr_id, []))
            job_id = job_ids_by_ocr.get(ocr_id, 0)

            thumbnail_url = f"/api/crops/{crop_id}/image" if crop_id else ""

            crop = crop_by_id.get(crop_id) if crop_id else None
            scan = scan_by_id.get(crop.scan_id) if crop and crop.scan_id else None
            crop_coords = crop.crop_coordinates if crop else None

            results.append(
                CampaignResultResponse(
                    ocr_result_id=ocr_id,
                    extracted_name=extracted_name,
                    extracted_address=extracted_address,
                    crop_id=crop_id,
                    job_id=job_id,
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
                MatchResult.matcher_job_id == latest_job_id,
                MatchResult.ocr_result_id > last_id,
            ]
            if confidence_filter:
                next_page_where.append(
                    MatchResult.confidence_level == confidence_filter
                )
            count_after = self._session.exec(
                select(func.count()).select_from(
                    select(func.distinct(MatchResult.ocr_result_id))
                    .where(*next_page_where)
                    .subquery()
                )
            ).one()
            if count_after:
                next_cursor = last_id

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
        from app.data.database.model.registered_voter import RegisteredVoter
        from app.services.prediction_builder import PredictionBuilder

        voter_ids = {r.voter_id for r in match_results if r.voter_id}
        voters_by_id: dict[int, RegisteredVoter] = {}

        if voter_ids:
            voters = self._session.exec(
                select(RegisteredVoter).where(RegisteredVoter.id.in_(voter_ids))
            ).all()
            voters_by_id = {v.id: v for v in voters}

        raw_predictions = PredictionBuilder.build(match_results, voters_by_id)

        predictions_by_ocr: dict[int, list[CampaignMatchPrediction]] = {}
        for ocr_id, preds in raw_predictions.items():
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
