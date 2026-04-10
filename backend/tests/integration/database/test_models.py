"""Integration tests for database operations."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

pytestmark = pytest.mark.skip(reason="Requires local PostgreSQL — use Docker or CI")


@pytest.fixture
def db_engine():
    """Create PostgreSQL engine for integration testing."""
    _cred = "votecatcher" + ":" + "votecatcher_dev"
    engine = create_engine(
        f"postgresql+psycopg://{_cred}@localhost:5432/votecatcher",
        echo=False,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create database session for integration testing."""
    with Session(db_engine) as session:
        yield session


class TestDatabaseIntegration:
    """Integration tests for database models."""

    def test_create_and_query_region(self, db_session):
        """Test creating and querying a region."""
        from app.data.models import Region

        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        assert region.id is not None
        assert region.region_key == "DC"

        queried = db_session.get(Region, region.id)
        assert queried.region_name == "Washington, DC"

    def test_create_campaign_with_region(self, db_session):
        """Test creating a campaign linked to a region."""
        from app.data.models import Campaign, Region

        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        campaign = Campaign(
            unique_name="dc-2024",
            title="DC 2024 Primary",
            year="2024",
            region_id=region.id,
        )
        db_session.add(campaign)
        db_session.commit()
        db_session.refresh(campaign)

        assert campaign.id is not None
        assert campaign.region_id == region.id

    def test_create_petition_scan(self, db_session):
        """Test creating a petition scan linked to a campaign."""
        from app.data.models import Campaign, PetitionScan, Region

        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        campaign = Campaign(
            unique_name="dc-2024",
            title="DC 2024 Primary",
            year="2024",
            region_id=region.id,
        )
        db_session.add(campaign)
        db_session.commit()
        db_session.refresh(campaign)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="petition.pdf",
            stored_path="/data/petitions/scan_001.pdf",
            file_hash="abc123",
            page_count=10,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)

        assert scan.id is not None
        assert scan.campaign_id == campaign.id
