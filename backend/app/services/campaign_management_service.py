"""Campaign management service for CRUD operations on campaigns and petition scans."""

from __future__ import annotations

import uuid

import structlog
from sqlmodel import Session, select

from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.routers.campaign_router import (
    CampaignListResponse,
    CampaignResponse,
    PetitionScanListResponse,
    PetitionScanResponse,
)

logger = structlog.get_logger(__name__)

DEFAULT_REGION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class CampaignManagementService:
    """Service for managing campaigns and their petition scans."""

    def __init__(self, session: Session):
        self._session = session

    def _ensure_default_region(self) -> uuid.UUID:
        region = self._session.exec(
            select(Region).where(Region.region_key == "DC")
        ).first()
        if region:
            return region.id
        region = Region(
            id=DEFAULT_REGION_ID,
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        self._session.add(region)
        self._session.commit()
        return region.id

    def _get_region_key(self, region_id: uuid.UUID | None) -> str | None:
        if not region_id:
            return None
        region = self._session.get(Region, region_id)
        return region.region_key if region else None

    def _build_campaign_response(self, campaign: Campaign) -> CampaignResponse:
        return CampaignResponse(
            id=campaign.id,
            unique_name=campaign.unique_name,
            title=campaign.title,
            year=campaign.year,
            region=self._get_region_key(campaign.region_id),
            region_id=campaign.region_id,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )

    def create_campaign(
        self, name: str, year: int, region: str = "DC"
    ) -> CampaignResponse:
        """Create a new campaign.

        Args:
            name: Campaign name (unique_name and title)
            year: Election year
            region: Region key (defaults to DC)

        Returns:
            Created campaign response
        """
        region_id = self._ensure_default_region()
        campaign = Campaign(
            unique_name=name,
            title=name,
            year=str(year),
            region_id=region_id,
        )
        self._session.add(campaign)
        self._session.commit()
        self._session.refresh(campaign)

        logger.info(
            "Campaign created",
            campaign_id=campaign.id,
            unique_name=campaign.unique_name,
            year=campaign.year,
        )

        return self._build_campaign_response(campaign)

    def list_campaigns(self, offset: int = 0, limit: int = 100) -> CampaignListResponse:
        """List all campaigns with pagination.

        Args:
            offset: Number of campaigns to skip
            limit: Maximum number of campaigns to return

        Returns:
            Paginated list of campaigns with total count
        """
        statement = select(Campaign).offset(offset).limit(limit)
        campaigns = self._session.exec(statement).all()

        count_statement = select(Campaign)
        total = len(self._session.exec(count_statement).all())

        return CampaignListResponse(
            campaigns=[self._build_campaign_response(c) for c in campaigns],
            total=total,
        )

    def get_campaign(self, campaign_id: uuid.UUID) -> CampaignResponse:
        """Get campaign details.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Campaign response

        Raises:
            ValueError: If campaign not found
        """
        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        return self._build_campaign_response(campaign)

    def delete_campaign(self, campaign_id: uuid.UUID) -> None:
        """Delete a campaign.

        Args:
            campaign_id: Campaign UUID

        Raises:
            ValueError: If campaign not found
        """
        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        self._session.delete(campaign)
        self._session.commit()
        logger.info("Campaign deleted", campaign_id=campaign_id)

    def list_campaign_scans(self, campaign_id: uuid.UUID) -> PetitionScanListResponse:
        """List all petition scans for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            List of petition scans with total count

        Raises:
            ValueError: If campaign not found
        """
        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        statement = select(PetitionScan).where(PetitionScan.campaign_id == campaign_id)
        scans = self._session.exec(statement).all()

        return PetitionScanListResponse(
            scans=[
                PetitionScanResponse(
                    id=s.id,
                    original_filename=s.original_filename,
                    file_size=s.file_size,
                    page_count=s.page_count,
                    uploaded_at=s.uploaded_at,
                )
                for s in scans
            ],
            total=len(scans),
        )

    def delete_campaign_scan(self, campaign_id: uuid.UUID, scan_id: int) -> None:
        """Delete a petition scan from a campaign.

        Args:
            campaign_id: Campaign UUID
            scan_id: Petition scan ID

        Raises:
            ValueError: If campaign or scan not found
        """
        campaign = self._session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        scan = self._session.exec(
            select(PetitionScan).where(
                PetitionScan.id == scan_id,
                PetitionScan.campaign_id == campaign_id,
            )
        ).first()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found for campaign {campaign_id}")

        self._session.delete(scan)
        self._session.commit()
        logger.info("Petition scan deleted", scan_id=scan_id, campaign_id=campaign_id)
