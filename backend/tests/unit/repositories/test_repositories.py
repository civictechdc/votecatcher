"""Tests for repository implementations."""

from pathlib import Path
from uuid import UUID

import pytest


class TestSqliteCampaignRepository:
    """Tests for Campaign repository with SQLite."""

    @pytest.fixture
    def engine(self, tmp_path: Path):
        """Create SQLite engine with initialized schema."""
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        engine.initialize()
        return engine

    @pytest.fixture
    def region_id(self, engine):
        """Create a region and return its ID."""

        from app.data.database.model.schema import Region

        with engine.create_session() as session:
            region = Region(
                region_key="dc",
                region_name="Washington DC",
                country_code="US",
            )
            session.add(region)
            session.commit()
            session.refresh(region)
            return region.id

    @pytest.fixture
    def repo(self, engine):
        """Create campaign repository."""
        from app.repositories.campaign_repo import CampaignRepository

        return CampaignRepository(engine)

    def test_save_campaign(self, repo, region_id):
        """Should save and retrieve campaign."""
        from app.domain.campaign import Campaign

        campaign = Campaign(
            unique_name="test-campaign-2026",
            title="Test Campaign",
            year="2026",
            region_id=region_id,
        )
        saved = repo.save(campaign)
        assert saved.unique_name == "test-campaign-2026"
        assert saved.title == "Test Campaign"

    def test_find_by_id(self, repo, region_id):
        """Should find campaign by ID."""
        from app.domain.campaign import Campaign

        campaign = Campaign(
            unique_name="test",
            title="Test",
            year="2026",
            region_id=region_id,
        )
        repo.save(campaign)
        found = repo.find_by_id(campaign.id)
        assert found is not None
        assert found.title == "Test"

    def test_find_by_id_returns_none_for_missing(self, repo):
        """Should return None for missing campaign."""
        result = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000999"))
        assert result is None

    def test_list_all(self, repo, region_id):
        """Should list all campaigns."""
        from app.domain.campaign import Campaign

        campaign = Campaign(
            unique_name="listed",
            title="Listed",
            year="2026",
            region_id=region_id,
        )
        repo.save(campaign)
        campaigns = repo.list_all()
        assert len(campaigns) >= 1

    def test_list_active_filters_by_year(self, repo, region_id):
        """list_active should only return current year campaigns."""
        from datetime import date

        from app.domain.campaign import Campaign

        current_year = str(date.today().year)
        active = Campaign(
            unique_name="active-campaign",
            title="Active",
            year=current_year,
            region_id=region_id,
        )
        old = Campaign(
            unique_name="old-campaign",
            title="Old",
            year="2020",
            region_id=region_id,
        )
        repo.save(active)
        repo.save(old)
        result = repo.list_active()
        assert all(c.year == current_year for c in result)
        assert any(c.unique_name == "active-campaign" for c in result)


class TestSqlitePetitionRepository:
    """Tests for Petition repository with SQLite."""

    @pytest.fixture
    def engine(self, tmp_path: Path):
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        engine.initialize()
        return engine

    @pytest.fixture
    def campaign_id(self, engine):
        from app.data.database.model.schema import Campaign, Region

        with engine.create_session() as session:
            region = Region(region_key="dc", region_name="DC", country_code="US")
            session.add(region)
            session.commit()
            session.refresh(region)
            campaign = Campaign(
                unique_name="test-pet-camp",
                title="Test",
                year="2026",
                region_id=region.id,
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)
            return campaign.id

    @pytest.fixture
    def repo(self, engine):
        from app.repositories.petition_repo import PetitionRepository

        return PetitionRepository(engine)

    def test_save_petition(self, repo, campaign_id):
        from app.domain.petition import Petition

        petition = Petition(
            campaign_id=campaign_id,
            original_filename="test.pdf",
            stored_path="/uploads/test.pdf",
            file_hash="abc123",
        )
        saved = repo.save(petition)
        assert saved.original_filename == "test.pdf"
        assert saved.file_hash == "abc123"
        assert saved.id is not None

    def test_find_by_id(self, repo, campaign_id):
        from app.domain.petition import Petition

        petition = Petition(
            campaign_id=campaign_id,
            original_filename="find.pdf",
            stored_path="/uploads/find.pdf",
            file_hash="def456",
        )
        saved = repo.save(petition)
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.original_filename == "find.pdf"

    def test_find_by_id_returns_none_for_missing(self, repo):
        result = repo.find_by_id(999999)
        assert result is None

    def test_find_by_campaign(self, repo, campaign_id):
        from app.domain.petition import Petition

        p1 = Petition(
            campaign_id=campaign_id,
            original_filename="a.pdf",
            stored_path="/a.pdf",
            file_hash="hash1",
        )
        p2 = Petition(
            campaign_id=campaign_id,
            original_filename="b.pdf",
            stored_path="/b.pdf",
            file_hash="hash2",
        )
        repo.save(p1)
        repo.save(p2)
        results = repo.find_by_campaign(campaign_id)
        assert len(results) == 2


class TestSqliteVoterRepository:
    """Tests for Voter repository with SQLite."""

    @pytest.fixture
    def engine(self, tmp_path: Path):
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        engine.initialize()
        return engine

    @pytest.fixture
    def region_id(self, engine):
        from app.data.database.model.schema import Region

        with engine.create_session() as session:
            region = Region(region_key="dc", region_name="DC", country_code="US")
            session.add(region)
            session.commit()
            session.refresh(region)
            return region.id

    @pytest.fixture
    def repo(self, engine):
        from app.repositories.voter_repo import VoterRepository

        return VoterRepository(engine)

    def test_save_voter(self, repo, region_id):
        from app.domain.voter import RegisteredVoter

        voter = RegisteredVoter(
            region_id=region_id,
            name_data={"first_name": "Jane", "last_name": "Smith"},
            address_data={"city": "Washington"},
        )
        saved = repo.save(voter)
        assert saved.name_data["first_name"] == "Jane"
        assert saved.id is not None

    def test_find_by_id(self, repo, region_id):
        from app.domain.voter import RegisteredVoter

        voter = RegisteredVoter(
            region_id=region_id,
            name_data={"first_name": "John", "last_name": "Doe"},
        )
        saved = repo.save(voter)
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.full_name == "John Doe"

    def test_find_by_id_returns_none_for_missing(self, repo):
        result = repo.find_by_id(999999)
        assert result is None

    def test_find_by_region(self, repo, region_id):
        from app.domain.voter import RegisteredVoter

        v1 = RegisteredVoter(
            region_id=region_id,
            name_data={"first_name": "A", "last_name": "B"},
        )
        v2 = RegisteredVoter(
            region_id=region_id,
            name_data={"first_name": "C", "last_name": "D"},
        )
        repo.save(v1)
        repo.save(v2)
        results = repo.find_by_region(region_id)
        assert len(results) == 2
