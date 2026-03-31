"""File upload router for voter lists and petitions."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.data.database.model.schema import Region
from app.dependencies import get_session
from app.files.file_service import FileService, FileValidationError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


SessionDep = Annotated[Session, Depends(get_session)]


class VoterListUploadResponse(BaseModel):
	"""Response schema for voter list upload."""

	message: str
	file_path: str
	row_count: int
	imported_count: int | None = None


class PetitionUploadResponse(BaseModel):
	"""Response schema for petition upload."""

	message: str
	scan_id: int
	crop_count: int


@router.post(
	"/voter-list",
	response_model=VoterListUploadResponse,
	status_code=status.HTTP_201_CREATED,
)
async def upload_voter_list(
	campaign_id: str = Form(...),
	file: UploadFile = File(...),  # noqa: B008
	session: SessionDep = None,  # pyright: ignore[reportArgumentType]
) -> VoterListUploadResponse:
	"""Upload and import voter list CSV file.

	Args:
		campaign_id: Campaign ID to get region from
		file: Uploaded file (CSV)
		session: Database session

	Returns:
		Upload confirmation with file path and imported count

	Raises:
		HTTPException: 400 if file validation fails
		HTTPException: 404 if campaign/region not found
	"""
	try:
		from app.data.database.model.schema import Campaign

		campaign_uuid = uuid.UUID(campaign_id.replace("-", ""))
		campaign = session.get(Campaign, campaign_uuid)
		if not campaign:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail=f"Campaign {campaign_id} not found",
			)

		region = session.get(Region, campaign.region_id)
		if not region:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Region for campaign not found",
			)

		file_service = FileService(session)
		file_path, imported_count = await file_service.import_voter_list(
			file=file,
			region_id=region.id,
		)

		logger.info(
			"Voter list uploaded and imported",
			file_name=file.filename,
			file_path=file_path,
			region_id=str(region.id),
			imported_count=imported_count,
		)

		return VoterListUploadResponse(
			message="Voter list uploaded and imported successfully",
			file_path=file_path,
			row_count=imported_count,
			imported_count=imported_count,
		)

	except (ValueError, FileValidationError) as e:
		logger.error("Voter list upload failed", error=str(e))
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(e),
		) from None


@router.post(
	"/petition",
	response_model=PetitionUploadResponse,
	status_code=status.HTTP_201_CREATED,
)
async def upload_petition(
	campaign_id: str = Form(...),
	file: UploadFile = File(...),  # noqa: B008
	region: str = Form("DC"),
	session: SessionDep = None,  # pyright: ignore[reportArgumentType]
) -> PetitionUploadResponse:
	"""Upload petition PDF with pre-cropping.

	Args:
		campaign_id: Campaign ID to associate with
		file: Uploaded PDF file
		region: Region for crop coordinates (default: DC)
		session: Database session

	Returns:
		Upload confirmation with scan ID and crop count

	Raises:
		HTTPException: 400 if file validation fails
		HTTPException: 404 if campaign not found
	"""
	try:
		file_service = FileService(session)
		scan_id, crop_count = await file_service.process_petition_upload(
			file=file,
			campaign_id=campaign_id,
			region=region,
		)

		logger.info(
			"Petition uploaded and cropped",
			file_name=file.filename,
			campaign_id=campaign_id,
			scan_id=scan_id,
			crop_count=crop_count,
		)

		return PetitionUploadResponse(
			message="Petition uploaded and cropped successfully",
			scan_id=scan_id,
			crop_count=crop_count,
		)

	except (ValueError, FileValidationError) as e:
		logger.error("Petition upload failed", error=str(e))
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(e),
		) from None
