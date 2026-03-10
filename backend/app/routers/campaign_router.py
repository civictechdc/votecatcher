"""Campaign management router."""

from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.data.database.model.schema import Campaign
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


SessionDep = Annotated[Session, Depends(get_session)]


class CampaignResponse(BaseModel):
	"""Response schema for campaign."""

	id: int | None
	name: str
	year: int
	region: str | None
	created_at: datetime | None
	updated_at: datetime | None


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
	campaign = Campaign(
		name=request.name,
		year=request.year,
		region=request.region,
	)
	session.add(campaign)
	session.commit()
	session.refresh(campaign)

	logger.info(
		"Campaign created",
		campaign_id=campaign.id,
		name=campaign.name,
		year=campaign.year,
	)

	return CampaignResponse(
		id=campaign.id,
		name=campaign.name,
		year=campaign.year,
		region=campaign.region,
		created_at=campaign.created_on,
		updated_at=campaign.updated_on,
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
				name=c.name,
				year=c.year,
				region=c.region,
				created_at=c.created_on,
				updated_at=c.updated_on,
			)
			for c in campaigns
		],
		total=total,
	)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
	campaign_id: int,
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
		name=campaign.name,
		year=campaign.year,
		region=campaign.region,
		created_at=campaign.created_on,
		updated_at=campaign.updated_on,
	)
