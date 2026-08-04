"""Campaign management router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlmodel import Session

from app.api_models import ApiModel
from app.data.database.model.match_result import ConfidenceLevel
from app.dependencies import get_session
from app.responses.campaign import (
    CampaignListResponse,
    CampaignMatchPrediction,
    CampaignResponse,
    CampaignResultsListResponse,
    CampaignResultResponse,
    JobsStatus,
    PetitionScanListResponse,
    PetitionScanResponse,
    PetitionsStatus,
    SetupStatusResponse,
    VoterListStatus,
)

__all__ = [
    "CampaignListResponse",
    "CampaignMatchPrediction",
    "CampaignMetricsResponse",
    "CampaignResponse",
    "CampaignResultsListResponse",
    "CampaignResultResponse",
    "CreateCampaignRequest",
    "JobsStatus",
    "LastJobInfo",
    "PetitionScanListResponse",
    "PetitionScanResponse",
    "PetitionsStatus",
    "SetupStatusResponse",
    "VoterListStatus",
    "router",
]

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

SessionDep = Annotated[Session, Depends(get_session)]


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


@router.get("/{campaign_id}/results", response_model=CampaignResultsListResponse)
def get_campaign_results(
    campaign_id: uuid.UUID,
    session: SessionDep,
    confidence: ConfidenceLevel | None = None,
    cursor: int | None = None,
    page_size: int = 50,
) -> CampaignResultsListResponse:
    """Get match results for all jobs in a campaign."""
    from app.services.campaign_query_service import CampaignQueryService

    try:
        return CampaignQueryService(session).get_campaign_results(
            campaign_id,
            confidence=confidence,
            cursor=cursor,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


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
