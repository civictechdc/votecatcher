"""File upload router for voter lists and petitions."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
from app.files.file_service import FileValidationError
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["upload"])


SessionDep = Annotated[Session, Depends(get_session)]


class VoterListUploadResponse(ApiModel):
    """Response schema for voter list upload."""

    message: str
    file_path: str
    row_count: int
    imported_count: int | None = None


class PetitionUploadResponse(ApiModel):
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
        service = UploadService(session)
        result = await service.process_voter_list_upload(
            campaign_id=campaign_id,
            file=file,
        )

        return VoterListUploadResponse(
            message="Voter list uploaded and imported successfully",
            file_path=result.file_path,
            row_count=result.imported_count,
            imported_count=result.imported_count,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except FileValidationError as e:
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
        service = UploadService(session)
        result = await service.process_petition_upload(
            campaign_id=campaign_id,
            file=file,
            region=region,
        )

        return PetitionUploadResponse(
            message="Petition uploaded and cropped successfully",
            scan_id=result.scan_id,
            crop_count=result.crop_count,
        )

    except (ValueError, FileValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
