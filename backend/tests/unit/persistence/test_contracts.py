"""Tests for persistence contracts."""


class TestProvidesEngine:
    """Tests for ProvidesEngine protocol."""

    def test_protocol_has_required_methods(self):
        """Protocol must define all required methods."""
        from app.persistence.contracts import ProvidesEngine

        attrs = ProvidesEngine.__protocol_attrs__
        assert "name" in attrs
        assert "connection_url" in attrs
        assert "create_session" in attrs
        assert "initialize" in attrs
        assert "health_check" in attrs


class TestProvidesRepositoryContracts:
    """Tests for repository protocol contracts."""

    def test_petition_repository_contract(self):
        """PetitionRepository must define required methods."""
        from app.persistence.contracts import PetitionRepository

        attrs = PetitionRepository.__protocol_attrs__
        assert "save" in attrs
        assert "find_by_id" in attrs

    def test_campaign_repository_contract(self):
        """CampaignRepository must define required methods."""
        from app.persistence.contracts import CampaignRepository

        attrs = CampaignRepository.__protocol_attrs__
        assert "save" in attrs
        assert "find_by_id" in attrs
        assert "list_active" in attrs

    def test_voter_repository_contract(self):
        """VoterRepository must define required methods."""
        from app.persistence.contracts import VoterRepository

        attrs = VoterRepository.__protocol_attrs__
        assert "save" in attrs
        assert "find_by_id" in attrs
        assert "find_by_region" in attrs
