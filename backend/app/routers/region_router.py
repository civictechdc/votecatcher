"""Region router for voter list status, management, and region listing."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_field_spec_service, get_session
from app.services.field_spec_service import FieldSpecService
from app.services.region_query_service import RegionQueryService
from app.settings.settings import get_settings

router = APIRouter(prefix="/regions", tags=["regions"])

SessionDep = Annotated[Session, Depends(get_session)]
FieldSpecServiceDep = Annotated[FieldSpecService, Depends(get_field_spec_service)]


class RegionSummary(ApiModel):
    """Summary of a region with field spec."""

    key: str
    name: str
    id: UUID


class RegionListResponse(ApiModel):
    """Response schema for listing regions."""

    regions: list[RegionSummary]


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


@router.get("", response_model=RegionListResponse)
async def list_regions(
    service: FieldSpecServiceDep,
) -> RegionListResponse:
    """List available regions with loaded field specs."""
    settings = get_settings()
    if not settings.features.fieldspec.api.enabled:
        return RegionListResponse(regions=[])

    rows = service.list_regions()

    return RegionListResponse(
        regions=[
            RegionSummary(key=key, name=name, id=region_id)
            for key, name, region_id in rows
        ]
    )


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
