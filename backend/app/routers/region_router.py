"""Region router for voter list status and management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
from app.services.region_query_service import RegionQueryService

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
async def get_voter_list_status(
    region_id: UUID,
    session: SessionDep,
) -> VoterListStatusResponse:
    """Get the current voter list status for a region."""
    service = RegionQueryService(session)
    result = service.get_voter_list_status(region_id)

    if not result.exists:
        return VoterListStatusResponse(exists=False, upload=None)

    return VoterListStatusResponse(
        exists=True,
        upload=UploadDetail(
            id=result.upload.id,
            original_filename=result.upload.original_filename,
            file_size=result.upload.file_size,
            row_count=result.upload.row_count,
            uploaded_at=result.upload.uploaded_at,
            status=result.upload.status,
        ),
    )


@router.delete(
    "/{region_id}/voter-list",
    response_model=DeleteVoterListResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_voter_list(
    region_id: UUID,
    session: SessionDep,
) -> DeleteVoterListResponse:
    """Delete all voters for a region and mark uploads as superseded."""
    service = RegionQueryService(session)
    result = service.delete_voter_list(region_id)

    return DeleteVoterListResponse(
        deleted_count=result.deleted_count,
        success=result.success,
    )
