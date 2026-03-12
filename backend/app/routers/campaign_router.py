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


class CampaignMatchPrediction(BaseModel):
	"""Schema for a single match prediction."""

	rank: int
	voter_name: str
	voter_address: str
	similarity_score: float
	confidence: str


class CampaignResultResponse(BaseModel):
	"""Response schema for a single result."""

	ocr_result_id: int
	extracted_name: str
	extracted_address: str
	crop_id: int
	job_id: int
	predictions: list[CampaignMatchPrediction]


class CampaignResultsListResponse(BaseModel):
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
	"""Get match results for all jobs in a campaign.

	Args:
		campaign_id: Campaign UUID
		session: Database session
		confidence: Filter by confidence level (HIGH/MEDIUM/LOW, optional)
		page: Page number (1-indexed)
		page_size: Items per page

	Returns:
		Paginated match results for the campaign

	Raises:
		HTTPException: 404 if campaign not found
	"""
	from app.data.database.model.jobs import MatcherJob
	from app.data.database.model.match_result import ConfidenceLevel, MatchResult
	from app.data.database.model.ocr_result import OcrResult
	from app.data.database.model.registered_voter import RegisteredVoter

	campaign = session.get(Campaign, campaign_id)
	if not campaign:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Campaign {campaign_id} not found",
		)

	job_ids_statement = select(MatcherJob.id).where(
		MatcherJob.campaign_id == campaign_id
	)
	job_ids: list[int] = list(session.exec(job_ids_statement).all())

	if not job_ids:
		return CampaignResultsListResponse(
			results=[],
			total=0,
			page=page,
			page_size=page_size,
		)

	confidence_filter = None
	if confidence:
		try:
			confidence_filter = ConfidenceLevel(confidence.upper())
		except ValueError:
			confidence_filter = None

	total_statement = select(MatchResult).where(MatchResult.matcher_job_id.in_(job_ids))
	if confidence_filter:
		total_statement = total_statement.where(
			MatchResult.confidence_level == confidence_filter
		)

	all_match_results = session.exec(total_statement).all()
	total = len({r.ocr_result_id for r in all_match_results})

	if total == 0:
		return CampaignResultsListResponse(
			results=[],
			total=0,
			page=page,
			page_size=page_size,
		)

	ocr_result_ids = sorted({r.ocr_result_id for r in all_match_results})
	offset = (page - 1) * page_size
	paginated_ocr_ids = ocr_result_ids[offset : offset + page_size]

	page_match_results = [
		r for r in all_match_results if r.ocr_result_id in paginated_ocr_ids
	]

	voter_ids = {r.voter_id for r in page_match_results if r.voter_id}
	voters_by_id: dict[int, RegisteredVoter] = {}

	if voter_ids:
		voters = session.exec(
			select(RegisteredVoter).where(RegisteredVoter.id.in_(voter_ids))
		).all()
		voters_by_id = {v.id: v for v in voters}

	predictions_by_ocr: dict[int, list[CampaignMatchPrediction]] = {}
	job_ids_by_ocr: dict[int, int] = {}

	for result in page_match_results:
		ocr_id = result.ocr_result_id
		if ocr_id not in predictions_by_ocr:
			predictions_by_ocr[ocr_id] = []
		if ocr_id not in job_ids_by_ocr:
			job_ids_by_ocr[ocr_id] = result.matcher_job_id

		voter = voters_by_id.get(result.voter_id) if result.voter_id else None

		voter_name = ""
		voter_address = ""
		if voter:
			name_parts = []
			if voter.name_data:
				first = voter.name_data.get("first_name", "")
				last = voter.name_data.get("last_name", "")
				if first:
					name_parts.append(first)
				if last:
					name_parts.append(last)
			voter_name = " ".join(name_parts)

			if voter.address_data:
				addr_parts = []
				street = voter.address_data.get("street", "")
				city = voter.address_data.get("city", "")
				state = voter.address_data.get("state", "")
				zip_code = voter.address_data.get("zip", "")
				if street:
					addr_parts.append(street)
				if city:
					addr_parts.append(city)
				if state:
					addr_parts.append(state)
				if zip_code:
					addr_parts.append(zip_code)
				voter_address = ", ".join(addr_parts)

		predictions_by_ocr[ocr_id].append(
			CampaignMatchPrediction(
				rank=result.rank,
				voter_name=voter_name,
				voter_address=voter_address,
				similarity_score=result.similarity_score,
				confidence=result.confidence_level.value
				if result.confidence_level
				else "LOW",
			)
		)

	for ocr_id in predictions_by_ocr:
		predictions_by_ocr[ocr_id].sort(key=lambda p: p.rank)

	ocr_ids_to_fetch = set(paginated_ocr_ids)
	ocr_results_by_id: dict[int, OcrResult] = {}

	if ocr_ids_to_fetch:
		ocr_results = session.exec(
			select(OcrResult).where(OcrResult.id.in_(ocr_ids_to_fetch))
		).all()
		ocr_results_by_id = {o.id: o for o in ocr_results}

	results = []
	for ocr_id in paginated_ocr_ids:
		ocr_result = ocr_results_by_id.get(ocr_id)

		extracted_name = ""
		extracted_address = ""
		crop_id = 0
		if ocr_result:
			if isinstance(ocr_result.extracted_text, dict):
				extracted_name = ocr_result.extracted_text.get("name") or ""
				extracted_address = ocr_result.extracted_text.get("address") or ""
			elif ocr_result.extracted_text:
				extracted_name = str(ocr_result.extracted_text)
			crop_id = ocr_result.crop_id

		predictions = predictions_by_ocr.get(ocr_id, [])[:5]
		job_id = job_ids_by_ocr.get(ocr_id, 0)

		results.append(
			CampaignResultResponse(
				ocr_result_id=ocr_id,
				extracted_name=extracted_name,
				extracted_address=extracted_address,
				crop_id=crop_id,
				job_id=job_id,
				predictions=predictions,
			)
		)

	return CampaignResultsListResponse(
		results=results,
		total=total,
		page=page,
		page_size=page_size,
	)
