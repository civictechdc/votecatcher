"""File upload router for voter lists and petitions."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.dependencies import get_session
from app.files.file_service import FileService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


SessionDep = Annotated[Session, Depends(get_session)]


class VoterListUploadResponse(BaseModel):
	"""Response schema for voter list upload."""

	message: str
	file_path: str
	row_count: int


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
	file: UploadFile = File(...),  # noqa: B008
	session: SessionDep = None,  # pyright: ignore[reportArgumentType]
) -> VoterListUploadResponse:
	"""Upload voter list CSV/Excel file.

	Args:
		file: Uploaded file (CSV or Excel)
		session: Database session

	Returns:
		Upload confirmation with file path and row count

	Raises:
		HTTPException: 400 if file validation fails
	"""
	try:
		file_service = FileService(session)
		file_path, row_count = await file_service.save_voter_list_file(file)

		logger.info(
			"Voter list uploaded",
			file_name=file.filename,
			file_path=file_path,
			row_count=row_count,
		)

		return VoterListUploadResponse(
			message="Voter list uploaded successfully",
			file_path=file_path,
			row_count=row_count,
		)

	except ValueError as e:
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

	except ValueError as e:
		logger.error("Petition upload failed", error=str(e))
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(e),
		) from None
