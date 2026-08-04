"""Campaign API response models."""

import uuid
from datetime import datetime

from app.api_models import ApiModel
from app.data.database.model.match_result import ConfidenceLevel


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


class CampaignMatchPrediction(ApiModel):
    """Schema for a single match prediction."""

    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: ConfidenceLevel


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
    page_size: int
    next_cursor: int | None = None


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
