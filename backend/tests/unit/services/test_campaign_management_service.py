"""Unit tests for CampaignManagementService.

BDD-style tests describing expected behaviour of the campaign management service
before the implementation exists. Written using vertical-slice TDD: one test →
implement → verify → next.
"""

import uuid

import pytest
from sqlmodel import Session, select

from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


def _seed_region(session: Session) -> Region:
    region = Region(
        region_key="DC",
        region_name="Washington, DC",
        country_code="US",
    )
    session.add(region)
    session.flush()
    return region


def _seed_campaign(session: Session, region: Region | None = None) -> Campaign:
    if region is None:
        region = _seed_region(session)
    campaign = Campaign(
        unique_name="dc-2024",
        title="DC 2024",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.flush()
    return campaign


class TestCreateCampaign:
    """Feature: Campaign creation.

    As an API consumer
    I want to create a campaign with a name, year, and region
    So that I can organize petition scanning work by election cycle.
    """

    def test_creates_campaign_with_default_region(self, session: Session):
        """Scenario: First campaign creates the default DC region."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        result = service.create_campaign(name="Test Campaign", year=2024, region="DC")

        assert result.unique_name == "Test Campaign"
        assert result.title == "Test Campaign"
        assert result.year == "2024"
        assert result.region == "DC"
        assert result.id is not None

        regions = session.exec(select(Region)).all()
        assert len(regions) == 1
        assert regions[0].region_key == "DC"

    def test_reuses_existing_region(self, session: Session):
        """Scenario: Second campaign reuses existing DC region."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        service.create_campaign(name="First", year=2024, region="DC")
        result = service.create_campaign(name="Second", year=2024, region="DC")

        assert result.unique_name == "Second"

        regions = session.exec(select(Region)).all()
        assert len(regions) == 1


class TestListCampaigns:
    """Feature: Campaign listing.

    As an API consumer
    I want to list campaigns with pagination
    So that I can browse available campaigns.
    """

    def test_empty_database_returns_empty_list(self, session: Session):
        """Scenario: No campaigns exist."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        result = service.list_campaigns(offset=0, limit=100)

        assert result.campaigns == []
        assert result.total == 0

    def test_returns_campaigns_with_region_key(self, session: Session):
        """Scenario: Campaigns exist with associated region."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        c1 = Campaign(
            unique_name="first", title="First", year="2024", region_id=region.id
        )
        c2 = Campaign(
            unique_name="second", title="Second", year="2024", region_id=region.id
        )
        session.add(c1)
        session.add(c2)
        session.commit()

        service = CampaignManagementService(session)
        result = service.list_campaigns(offset=0, limit=100)

        assert result.total == 2
        assert len(result.campaigns) == 2
        assert result.campaigns[0].region == "DC"
        assert result.campaigns[0].region_id == region.id

    def test_pagination_limits_results(self, session: Session):
        """Scenario: 3 campaigns, limit=2 returns 2."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        for i in range(3):
            session.add(
                Campaign(
                    unique_name=f"c-{i}",
                    title=f"Campaign {i}",
                    year="2024",
                    region_id=region.id,
                )
            )
        session.commit()

        service = CampaignManagementService(session)
        result = service.list_campaigns(offset=0, limit=2)

        assert result.total == 3
        assert len(result.campaigns) == 2


class TestGetCampaign:
    """Feature: Campaign retrieval.

    As an API consumer
    I want to get details of a specific campaign
    So that I can view its configuration and status.
    """

    def test_returns_campaign_details(self, session: Session):
        """Scenario: Campaign exists."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        service = CampaignManagementService(session)
        result = service.get_campaign(campaign.id)

        assert result.id == campaign.id
        assert result.unique_name == "dc-2024"
        assert result.region == "DC"

    def test_nonexistent_campaign_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.get_campaign(uuid.uuid4())


class TestDeleteCampaign:
    """Feature: Campaign deletion.

    As an API consumer
    I want to delete a campaign
    So that I can remove campaigns that are no longer needed.
    """

    def test_deletes_existing_campaign(self, session: Session):
        """Scenario: Campaign exists and is deleted."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        service = CampaignManagementService(session)
        service.delete_campaign(campaign.id)

        assert session.get(Campaign, campaign.id) is None

    def test_nonexistent_campaign_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.delete_campaign(uuid.uuid4())


class TestListCampaignScans:
    """Feature: Petition scan listing.

    As an API consumer
    I want to list petition scans for a campaign
    So that I can see uploaded petition files.
    """

    def test_returns_scans_for_campaign(self, session: Session):
        """Scenario: Campaign has petition scans."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="test.pdf",
            stored_path="/tmp/test.pdf",
            file_hash="abc123",
            file_size=1024,
            page_count=5,
        )
        session.add(scan)
        session.commit()

        service = CampaignManagementService(session)
        result = service.list_campaign_scans(campaign.id)

        assert result.total == 1
        assert result.scans[0].original_filename == "test.pdf"
        assert result.scans[0].file_size == 1024
        assert result.scans[0].page_count == 5

    def test_empty_scans_returns_empty_list(self, session: Session):
        """Scenario: Campaign has no petition scans."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        service = CampaignManagementService(session)
        result = service.list_campaign_scans(campaign.id)

        assert result.total == 0
        assert result.scans == []

    def test_nonexistent_campaign_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.list_campaign_scans(uuid.uuid4())


class TestDeleteCampaignScan:
    """Feature: Petition scan deletion.

    As an API consumer
    I want to delete a petition scan from a campaign
    So that I can remove incorrectly uploaded files.
    """

    def test_deletes_existing_scan(self, session: Session):
        """Scenario: Scan exists and belongs to campaign."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="delete_me.pdf",
            stored_path="/tmp/delete.pdf",
            file_hash="del123",
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)

        service = CampaignManagementService(session)
        service.delete_campaign_scan(campaign.id, scan.id)

        assert session.get(PetitionScan, scan.id) is None

    def test_nonexistent_campaign_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_management_service import CampaignManagementService

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.delete_campaign_scan(uuid.uuid4(), 1)

    def test_nonexistent_scan_raises_value_error(self, session: Session):
        """Scenario: Scan does not exist for campaign."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.delete_campaign_scan(campaign.id, 99999)

    def test_scan_from_different_campaign_raises_value_error(self, session: Session):
        """Scenario: Scan exists but belongs to another campaign."""
        from app.services.campaign_management_service import CampaignManagementService

        region = _seed_region(session)
        campaign1 = _seed_campaign(session, region)
        campaign2 = Campaign(
            unique_name="other-campaign",
            title="Other",
            year="2024",
            region_id=region.id,
        )
        session.add(campaign2)
        session.flush()

        scan = PetitionScan(
            campaign_id=campaign2.id,
            original_filename="other.pdf",
            stored_path="/tmp/other.pdf",
            file_hash="other123",
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)

        service = CampaignManagementService(session)
        with pytest.raises(ValueError, match="not found"):
            service.delete_campaign_scan(campaign1.id, scan.id)
