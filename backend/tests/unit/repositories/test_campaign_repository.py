"""Unit tests for CampaignRepository.

Tests cover CRUD operations for campaign management following TDD approach.
Uses the existing DemoCampaignRepository implementation.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.campaign.campaign_repository import CreateCampaign
from app.data.database.local.demo_campaign_repo import DemoCampaignRepository
from app.data.database.model.schema import Region


class TestCampaignRepository:
    """Test suite for CampaignRepository CRUD operations."""

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def session(self, engine):
        """Create database session for each test."""
        with Session(engine) as session:
            yield session

    @pytest.fixture
    def sample_region(self, session):
        """Create a sample region for testing."""
        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        session.add(region)
        session.commit()
        session.refresh(region)
        return region

    @pytest.mark.asyncio
    async def test_create_campaign_with_required_fields(self, session, sample_region):
        """Test creating a campaign with only required fields."""
        repo = DemoCampaignRepository(session)
        campaign_data = CreateCampaign(
            unique_name="dc-2024-primary",
            title="DC 2024 Primary Election",
            description="",
            year_active="2024",
            region_key=sample_region.region_key,
        )

        campaign_id = await repo.save_campaign(campaign_data)

        assert campaign_id is not None
        assert isinstance(campaign_id, type(sample_region.id))

    @pytest.mark.asyncio
    async def test_create_campaign_with_optional_description(
        self, session, sample_region
    ):
        """Test creating a campaign with optional description field."""
        repo = DemoCampaignRepository(session)
        campaign_data = CreateCampaign(
            unique_name="dc-2024-general",
            title="DC 2024 General Election",
            description="Petition verification for November 2024 election",
            year_active="2024",
            region_key=sample_region.region_key,
        )

        await repo.save_campaign(campaign_data)

        retrieved = await repo.fetch_campaign("dc-2024-general")
        assert (
            retrieved.description == "Petition verification for November 2024 election"
        )

    @pytest.mark.asyncio
    async def test_fetch_campaign_by_name(self, session, sample_region):
        """Test retrieving a campaign by unique_name."""
        repo = DemoCampaignRepository(session)
        campaign_data = CreateCampaign(
            unique_name="dc-2024",
            title="DC 2024",
            description="",
            year_active="2024",
            region_key=sample_region.region_key,
        )

        await repo.save_campaign(campaign_data)
        retrieved = await repo.fetch_campaign("dc-2024")

        assert retrieved is not None
        assert retrieved.unique_name == "dc-2024"
        assert retrieved.title == "DC 2024"
        assert retrieved.year_active == "2024"
        assert retrieved.region_key == sample_region.region_key

    @pytest.mark.asyncio
    async def test_fetch_campaign_includes_region_info(self, session, sample_region):
        """Test that fetched campaign includes region information."""
        repo = DemoCampaignRepository(session)
        campaign_data = CreateCampaign(
            unique_name="dc-2024",
            title="DC 2024",
            description="",
            year_active="2024",
            region_key=sample_region.region_key,
        )

        await repo.save_campaign(campaign_data)
        retrieved = await repo.fetch_campaign("dc-2024")

        assert retrieved.region_id is not None
        assert retrieved.region_key == "DC"
