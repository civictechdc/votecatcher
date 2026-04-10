"""Region router for voter list status and management."""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from app.api_models import ApiModel
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload
from app.dependencies import get_session
from app.services.voter_list_service import VoterListService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/regions", tags=["regions"])

SessionDep = Annotated[Session, Depends(get_session)]


class UploadDetail(ApiModel):
    """Typed upload details for voter list status."""

    id: str
    original_filename: str
    file_size: int | None
    row_count: int | None
    uploaded_at: str
    status: str


class VoterListStatusResponse(ApiModel):
    """Response schema for voter list status."""

    exists: bool
    upload: UploadDetail | None = None


class DeleteVoterListResponse(ApiModel):
    """Response schema for deleting voter list."""

    deleted_count: int
    success: bool


@router.get("/{region_id}/voter-list", response_model=VoterListStatusResponse)
async def get_voter_list_status(  # nosemgrep: fastapi-unauthenticated-route
    region_id: UUID,
    session: SessionDep,
) -> VoterListStatusResponse:
    """Get the current voter list status for a region.

    Args:
            region_id: Region UUID
            session: Database session

    Returns:
            Voter list status with upload info if exists
    """
    service = VoterListService(session)
    upload = service.get_active_upload(region_id)

    if not upload:
        return VoterListStatusResponse(exists=False, upload=None)

    return VoterListStatusResponse(
        exists=True,
        upload=UploadDetail(
            id=str(upload.id),
            original_filename=upload.original_filename,
            file_size=upload.file_size,
            row_count=upload.row_count,
            uploaded_at=upload.uploaded_at.isoformat(),
            status=upload.status.value,
        ),
    )


@router.delete(
    "/{region_id}/voter-list",
    response_model=DeleteVoterListResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_voter_list(  # nosemgrep: fastapi-unauthenticated-route
    region_id: UUID,
    session: SessionDep,
) -> DeleteVoterListResponse:
    """Delete all voters for a region and mark uploads as superseded.

    Args:
            region_id: Region UUID
            session: Database session

    Returns:
            Count of deleted voters
    """
    service = VoterListService(session)

    deleted_count = service.delete_voters_for_region(region_id)

    uploads = session.exec(
        select(VoterListUpload).where(VoterListUpload.region_id == region_id)
    ).all()
    for upload in uploads:
        upload.status = UploadStatus.SUPERSEDED

    session.commit()

    logger.info(
        "Voter list deleted",
        region_id=str(region_id),
        deleted_count=deleted_count,
    )

    return DeleteVoterListResponse(deleted_count=deleted_count, success=True)
