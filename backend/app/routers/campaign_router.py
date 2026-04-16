"""Campaign management router."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

SessionDep = Annotated[Session, Depends(get_session)]


class CampaignResponse(ApiModel):
    """Response schema for campaign."""

    id: uuid.UUID | None
    unique_name: str
    title: str
    year: str
    region: str | None
    region_id: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class CampaignListResponse(ApiModel):
    """Response schema for campaign list."""

    campaigns: list[CampaignResponse]
    total: int


class CreateCampaignRequest(ApiModel):
    """Request schema for creating campaign."""

    name: str = Field(min_length=1, max_length=255, pattern=r"^[^<>\"';&]+$")
    year: int = Field(ge=1900, le=2100)
    region: str = Field(default="DC", max_length=10)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    request: CreateCampaignRequest,
    session: SessionDep,
) -> CampaignResponse:
    """Create a new campaign."""
    from app.services.campaign_management_service import CampaignManagementService

    try:
        return CampaignManagementService(session).create_campaign(
            name=request.name, year=request.year, region=request.region
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> CampaignListResponse:
    """List all campaigns."""
    from app.services.campaign_management_service import CampaignManagementService

    return CampaignManagementService(session).list_campaigns(offset=offset, limit=limit)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> CampaignResponse:
    """Get campaign details."""
    from app.services.campaign_management_service import CampaignManagementService

    try:
        return CampaignManagementService(session).get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> None:
    """Delete a campaign."""
    from app.services.campaign_management_service import CampaignManagementService

    try:
        CampaignManagementService(session).delete_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


class LastJobInfo(ApiModel):
    """Typed sub-model for last job info in metrics."""

    id: int
    status: str
    completed_at: str | None


class CampaignMetricsResponse(ApiModel):
    """Response schema for campaign metrics."""

    total_signatures: int
    processed: int
    high_confidence: int
    medium_confidence: int
    low_confidence: int
    progress_percentage: float
    last_job: LastJobInfo | None
    voter_list_count: int | None


class PetitionScanResponse(ApiModel):
    """Response schema for a petition scan."""

    id: int
    original_filename: str
    file_size: int | None
    page_count: int | None
    uploaded_at: datetime


class PetitionScanListResponse(ApiModel):
    """Response schema for listing petition scans."""

    scans: list[PetitionScanResponse]
    total: int


@router.get("/{campaign_id}/metrics", response_model=CampaignMetricsResponse)
def get_campaign_metrics(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> CampaignMetricsResponse:
    """Get campaign metrics including signature counts and confidence breakdown."""
    from app.data.database.model.schema import Campaign
    from app.services.metrics import MetricsService

    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    service = MetricsService(session)
    metrics = service.compute_campaign_metrics(campaign_id)

    return CampaignMetricsResponse(**metrics)


@router.get("/{campaign_id}/scans", response_model=PetitionScanListResponse)
def list_campaign_scans(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> PetitionScanListResponse:
    """List all petition scans for a campaign."""
    from app.services.campaign_management_service import CampaignManagementService

    try:
        return CampaignManagementService(session).list_campaign_scans(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{campaign_id}/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_scan(
    campaign_id: uuid.UUID,
    scan_id: int,
    session: SessionDep,
) -> None:
    """Delete a petition scan."""
    from app.services.campaign_management_service import CampaignManagementService

    try:
        CampaignManagementService(session).delete_campaign_scan(campaign_id, scan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


class CampaignMatchPrediction(ApiModel):
    """Schema for a single match prediction."""

    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: str


class CampaignResultResponse(ApiModel):
    """Response schema for a single result."""

    ocr_result_id: int
    extracted_name: str
    extracted_address: str
    crop_id: int
    job_id: int
    thumbnail_url: str
    predictions: list[CampaignMatchPrediction]
    crop_coordinates: dict[str, float] | None = None
    entry_coordinates: dict[str, float] | None = None
    page_number: int | None = None
    document_name: str = ""
    scan_id: int | None = None


class CampaignResultsListResponse(ApiModel):
    """Response schema for paginated campaign results."""

    results: list[CampaignResultResponse]
    total: int
    page: int
    page_size: int


@router.get("/{campaign_id}/results", response_model=CampaignResultsListResponse)
def get_campaign_results(
    campaign_id: uuid.UUID,
    session: SessionDep,
    confidence: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CampaignResultsListResponse:
    """Get match results for all jobs in a campaign."""
    from app.services.campaign_query_service import CampaignQueryService

    try:
        return CampaignQueryService(session).get_campaign_results(
            campaign_id, confidence=confidence, page=page, page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


class VoterListStatus(ApiModel):
    """Voter list status sub-object."""

    exists: bool
    row_count: int | None
    uploaded_at: str | None
    region_name: str | None


class PetitionsStatus(ApiModel):
    """Petitions status sub-object."""

    exists: bool
    file_count: int
    signature_count: int


class JobsStatus(ApiModel):
    """Jobs status sub-object."""

    total: int
    active: int


class SetupStatusResponse(ApiModel):
    """Response schema for campaign setup status."""

    voter_list: VoterListStatus
    petitions: PetitionsStatus
    jobs: JobsStatus
    state: str


@router.get("/{campaign_id}/setup-status", response_model=SetupStatusResponse)
def get_setup_status(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> SetupStatusResponse:
    """Get campaign setup status for progress stepper."""
    from app.services.campaign_query_service import CampaignQueryService

    try:
        return CampaignQueryService(session).get_setup_status(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
