"""Unit tests for RegionQueryService.

BDD-style tests describing expected behaviour of the region query
service. Written using vertical-slice TDD: one test → implement → verify → next.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session

from app.data.database.model.schema import Region
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload


def _seed_region(session: Session) -> Region:
    region = Region(
        id=uuid4(), region_key="TR", region_name="Test Region", country_code="US"
    )
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


def _seed_upload(
    session: Session, region_id, status=UploadStatus.ACTIVE, filename="voters.csv"
) -> VoterListUpload:
    upload = VoterListUpload(
        region_id=region_id,
        original_filename=filename,
        file_size=1024,
        row_count=50,
        status=status,
        uploaded_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)
    return upload


class TestGetVoterListStatus:
    """Feature: Voter list status lookup.

    As an API consumer
    I want to check if a region has an active voter list upload
    So that I can show the user the current upload status.
    """

    def test_returns_not_exists_when_no_active_upload(self, session):
        """Scenario: Region has no active voter list upload."""
        from app.services.region_query_service import RegionQueryService

        service = RegionQueryService(session=session)
        region_id = uuid4()

        result = service.get_voter_list_status(region_id)

        assert result.exists is False
        assert result.upload is None

    def test_returns_upload_detail_when_active_upload_exists(self, session):
        """Scenario: Region has an active voter list upload."""
        from app.services.region_query_service import RegionQueryService

        region = _seed_region(session)
        upload = _seed_upload(session, region.id)

        service = RegionQueryService(session=session)
        result = service.get_voter_list_status(region.id)

        assert result.exists is True
        assert result.upload is not None
        assert result.upload.id == str(upload.id)
        assert result.upload.original_filename == "voters.csv"
        assert result.upload.file_size == 1024
        assert result.upload.row_count == 50
        assert result.upload.status == "active"
        assert "2024-01-15" in result.upload.uploaded_at

    def test_returns_not_exists_when_upload_is_superseded(self, session):
        """Scenario: Region only has superseded uploads."""
        from app.services.region_query_service import RegionQueryService

        region = _seed_region(session)
        _seed_upload(session, region.id, status=UploadStatus.SUPERSEDED)

        service = RegionQueryService(session=session)
        result = service.get_voter_list_status(region.id)

        assert result.exists is False
        assert result.upload is None


class TestDeleteVoterList:
    """Feature: Voter list deletion with upload supersession.

    As an API consumer
    I want to delete all voters for a region and supersede active uploads
    So that the region's voter data is fully cleared.
    """

    def test_deletes_voters_and_returns_count(self, session):
        """Scenario: Region has voters, all are deleted."""
        from app.services.region_query_service import RegionQueryService

        region = _seed_region(session)
        service = RegionQueryService(session=session)

        result = service.delete_voter_list(region.id)

        assert result.success is True
        assert result.deleted_count == 0

    def test_supersedes_active_uploads_on_deletion(self, session):
        """Scenario: Active uploads are marked superseded after deletion."""
        from app.services.region_query_service import RegionQueryService

        region = _seed_region(session)
        _seed_upload(session, region.id, status=UploadStatus.ACTIVE)

        service = RegionQueryService(session=session)
        result = service.delete_voter_list(region.id)

        assert result.success is True

        remaining_active = list(
            session.exec(
                __import__("sqlmodel")
                .select(VoterListUpload)
                .where(
                    VoterListUpload.region_id == region.id,
                    VoterListUpload.status == UploadStatus.ACTIVE,
                )
            )
        )
        assert len(remaining_active) == 0

    def test_handles_region_with_no_uploads(self, session):
        """Scenario: Deleting voter list for region with no uploads."""
        from app.services.region_query_service import RegionQueryService

        region = _seed_region(session)
        service = RegionQueryService(session=session)

        result = service.delete_voter_list(region.id)

        assert result.success is True
        assert result.deleted_count == 0
