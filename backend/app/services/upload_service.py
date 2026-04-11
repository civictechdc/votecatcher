"""Upload orchestration service for voter lists and petitions."""

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from app.data.database.model.schema import Campaign, Region
from app.files.file_service import FileService

if TYPE_CHECKING:
    from fastapi import UploadFile
    from sqlmodel import Session

logger = structlog.get_logger(__name__)


@dataclass
class CampaignValidationResult:
    campaign_id: uuid.UUID
    region_id: uuid.UUID


@dataclass
class VoterListUploadResult:
    file_path: str
    imported_count: int


@dataclass
class PetitionUploadResult:
    scan_id: int
    crop_count: int


class UploadService:
    """Service for validating campaigns and orchestrating file uploads."""

    def __init__(self, session: "Session"):
        self.session = session
        self._file_service = FileService(session)

    def validate_campaign_region(self, campaign_id: str) -> CampaignValidationResult:
        campaign_uuid = uuid.UUID(campaign_id.replace("-", ""))
        campaign = self.session.get(Campaign, campaign_uuid)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        region = self.session.get(Region, campaign.region_id)
        if not region:
            raise ValueError("Region for campaign not found")

        return CampaignValidationResult(
            campaign_id=campaign.id,
            region_id=region.id,
        )

    async def process_voter_list_upload(
        self, campaign_id: str, file: "UploadFile"
    ) -> VoterListUploadResult:
        validation = self.validate_campaign_region(campaign_id)

        file_path, imported_count = await self._file_service.import_voter_list(
            file=file,
            region_id=validation.region_id,
        )

        logger.info(
            "Voter list uploaded and imported",
            file_name=file.filename if file else None,
            file_path=file_path,
            region_id=str(validation.region_id),
            imported_count=imported_count,
        )

        return VoterListUploadResult(
            file_path=file_path,
            imported_count=imported_count,
        )

    async def process_petition_upload(
        self, campaign_id: str, file: "UploadFile", region: str = "DC"
    ) -> PetitionUploadResult:
        scan_id, crop_count = await self._file_service.process_petition_upload(
            file=file,
            campaign_id=campaign_id,
            region=region,
        )

        logger.info(
            "Petition uploaded and cropped",
            file_name=file.filename if file else None,
            campaign_id=campaign_id,
            scan_id=scan_id,
            crop_count=crop_count,
        )

        return PetitionUploadResult(scan_id=scan_id, crop_count=crop_count)
