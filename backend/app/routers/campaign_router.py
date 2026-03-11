"""Campaign management router."""

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.data.database.model.schema import Campaign, Region
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


SessionDep = Annotated[Session, Depends(get_session)]

DEFAULT_REGION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _ensure_default_region(session: Session) -> uuid.UUID:
	region = session.exec(select(Region).where(Region.region_key == "DC")).first()
	if region:
		return region.id
	region = Region(
		id=DEFAULT_REGION_ID,
		region_key="DC",
		region_name="Washington, DC",
		country_code="US",
	)
	session.add(region)
	session.commit()
	return region.id


class CampaignResponse(BaseModel):
	"""Response schema for campaign."""

	id: uuid.UUID | None
	unique_name: str
	title: str
	year: str
	region: str | None
	region_id: uuid.UUID | None
	created_at: datetime | None
	updated_at: datetime | None


def _get_region_key(session: Session, region_id: uuid.UUID | None) -> str | None:
	if not region_id:
		return None
	region = session.get(Region, region_id)
	return region.region_key if region else None


class CampaignListResponse(BaseModel):
	"""Response schema for campaign list."""

	campaigns: list[CampaignResponse]
	total: int


class CreateCampaignRequest(BaseModel):
	"""Request schema for creating campaign."""

	name: str
	year: int
	region: str = "DC"


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
	request: CreateCampaignRequest,
	session: SessionDep,
) -> CampaignResponse:
	"""Create a new campaign."""
	region_id = _ensure_default_region(session)
	campaign = Campaign(
		unique_name=request.name,
		title=request.name,
		year=str(request.year),
		region_id=region_id,
	)
	session.add(campaign)
	session.commit()
	session.refresh(campaign)

	logger.info(
		"Campaign created",
		campaign_id=campaign.id,
		unique_name=campaign.unique_name,
		year=campaign.year,
	)

	return CampaignResponse(
		id=campaign.id,
		unique_name=campaign.unique_name,
		title=campaign.title,
		year=campaign.year,
		region=_get_region_key(session, campaign.region_id),
		region_id=campaign.region_id,
		created_at=campaign.created_at,
		updated_at=campaign.updated_at,
	)


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
	session: SessionDep,
	offset: int = 0,
	limit: int = 100,
) -> CampaignListResponse:
	"""List all campaigns."""
	statement = select(Campaign).offset(offset).limit(limit)
	campaigns = session.exec(statement).all()

	count_statement = select(Campaign)
	total = len(session.exec(count_statement).all())

	return CampaignListResponse(
		campaigns=[
			CampaignResponse(
				id=c.id,
				unique_name=c.unique_name,
				title=c.title,
				year=c.year,
				region=_get_region_key(session, c.region_id),
				region_id=c.region_id,
				created_at=c.created_at,
				updated_at=c.updated_at,
			)
			for c in campaigns
		],
		total=total,
	)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
	campaign_id: uuid.UUID,
	session: SessionDep,
) -> CampaignResponse:
	"""Get campaign details."""
	campaign = session.get(Campaign, campaign_id)
	if not campaign:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Campaign {campaign_id} not found",
		)

	return CampaignResponse(
		id=campaign.id,
		unique_name=campaign.unique_name,
		title=campaign.title,
		year=campaign.year,
		region=_get_region_key(session, campaign.region_id),
		region_id=campaign.region_id,
		created_at=campaign.created_at,
		updated_at=campaign.updated_at,
	)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
	campaign_id: uuid.UUID,
	session: SessionDep,
) -> None:
	"""Delete a campaign."""
	campaign = session.get(Campaign, campaign_id)
	if not campaign:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Campaign {campaign_id} not found",
		)
	session.delete(campaign)
	session.commit()
	logger.info("Campaign deleted", campaign_id=campaign_id)


class CampaignMetricsResponse(BaseModel):
	"""Response schema for campaign metrics."""

	total_signatures: int
	processed: int
	high_confidence: int
	medium_confidence: int
	low_confidence: int
	progress_percentage: float
	last_job: dict | None


@router.get("/{campaign_id}/metrics", response_model=CampaignMetricsResponse)
def get_campaign_metrics(
	campaign_id: uuid.UUID,
	session: SessionDep,
) -> CampaignMetricsResponse:
	"""Get campaign metrics including signature counts and confidence breakdown.

	Args:
		campaign_id: Campaign UUID
		session: Database session

	Returns:
		Metrics including total signatures, processed count, confidence
		breakdown, progress percentage, and last job information.

	Raises:
		HTTPException: 404 if campaign not found
	"""
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
