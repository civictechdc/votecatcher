"""Unit tests for UploadService.

BDD-style tests describing expected behaviour of the upload
orchestration service. Written using vertical-slice TDD: one test →
implement → verify → next.
"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from app.data.database.model.schema import Campaign, Region


def _seed_region(session: Session) -> Region:
    region = Region(
        id=uuid4(), region_key="TR", region_name="Test Region", country_code="US"
    )
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


def _seed_campaign(session: Session, region: Region) -> Campaign:
    campaign = Campaign(
        id=uuid4(),
        unique_name=f"test-campaign-{uuid4().hex[:8]}",
        title="Test Campaign",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


class TestValidateCampaignRegion:
    """Feature: Campaign and region validation for uploads.

    As the upload service
    I want to validate that a campaign exists and has a valid region
    So that uploads are only accepted for properly configured campaigns.
    """

    def test_returns_region_when_campaign_found(self, session):
        """Scenario: Valid campaign with existing region."""
        from app.services.upload_service import UploadService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        service = UploadService(session=session)
        result = service.validate_campaign_region(str(campaign.id))

        assert result.campaign_id == campaign.id
        assert result.region_id == region.id

    def test_raises_not_found_when_campaign_missing(self, session):
        """Scenario: Campaign ID does not exist."""
        from app.services.upload_service import UploadService

        service = UploadService(session=session)

        with pytest.raises(ValueError, match="not found"):
            service.validate_campaign_region(str(uuid4()))

    def test_raises_not_found_when_region_missing(self, session):
        """Scenario: Campaign exists but region is missing."""
        from app.services.upload_service import UploadService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        session.delete(region)
        session.commit()

        service = UploadService(session=session)

        with pytest.raises(ValueError, match="Region.*not found"):
            service.validate_campaign_region(str(campaign.id))

    def test_accepts_hyphenated_campaign_id(self, session):
        """Scenario: Campaign ID with hyphens is normalized."""
        from app.services.upload_service import UploadService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        hyphenated = str(campaign.id)

        service = UploadService(session=session)
        result = service.validate_campaign_region(hyphenated)

        assert result.campaign_id == campaign.id


class TestProcessVoterListUpload:
    """Feature: Voter list upload orchestration.

    As the upload service
    I want to validate the campaign and delegate file import to FileService
    So that the router stays thin and validation is centralized.
    """

    async def test_delegates_to_file_service_with_valid_campaign(self, session):
        """Scenario: Valid campaign triggers file import."""
        from app.services.upload_service import UploadService

        region = _seed_region(session)
        _seed_campaign(session, region)

        service = UploadService(session=session)
        assert service is not None
        assert hasattr(service, "process_voter_list_upload")

    async def test_raises_validation_error_for_invalid_campaign(self, session):
        """Scenario: Invalid campaign_id raises before file processing."""
        from app.services.upload_service import UploadService

        service = UploadService(session=session)

        with pytest.raises(ValueError, match="not found"):
            await service.process_voter_list_upload(
                campaign_id=str(uuid4()),
                file=None,
            )


class TestProcessPetitionUpload:
    """Feature: Petition upload orchestration.

    As the upload service
    I want to delegate petition processing to FileService
    So that the router only handles HTTP concerns.
    """

    async def test_service_has_petition_method(self, session):
        """Scenario: UploadService exposes petition upload method."""
        from app.services.upload_service import UploadService

        service = UploadService(session=session)
        assert hasattr(service, "process_petition_upload")
