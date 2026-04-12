"""Region query service for voter list status and deletion."""

import structlog
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload
from app.services.voter_list_service import VoterListService

logger = structlog.get_logger(__name__)


@dataclass
class UploadDetail:
    id: str
    original_filename: str
    file_size: int | None
    row_count: int | None
    uploaded_at: str
    status: str


@dataclass
class VoterListStatusResponse:
    exists: bool
    upload: UploadDetail | None = None


@dataclass
class DeleteVoterListResponse:
    deleted_count: int
    success: bool


class RegionQueryService:
    """Service for querying and managing voter list status per region."""

    def __init__(self, session: Session):
        self.session = session
        self._voter_list_service = VoterListService(session)

    def get_voter_list_status(self, region_id: UUID) -> VoterListStatusResponse:
        upload = self._voter_list_service.get_active_upload(region_id)

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

    def delete_voter_list(self, region_id: UUID) -> DeleteVoterListResponse:
        deleted_count = self._voter_list_service.delete_voters_for_region(region_id)

        uploads = self.session.exec(
            select(VoterListUpload).where(VoterListUpload.region_id == region_id)
        ).all()
        for upload in uploads:
            upload.status = UploadStatus.SUPERSEDED

        self.session.commit()

        logger.info(
            "Voter list deleted",
            region_id=str(region_id),
            deleted_count=deleted_count,
        )

        return DeleteVoterListResponse(deleted_count=deleted_count, success=True)
