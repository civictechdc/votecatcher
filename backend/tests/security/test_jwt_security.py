"""JWT security tests.

NOTE: Current codebase does not use JWT authentication.
The oauth2_scheme is defined in dependencies.py but never used in any router.
This test documents the current state and should be updated when auth is added.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.schema import Campaign, Region


class TestJWTSecurity:
    """Tests for JWT authentication security."""

    @pytest.fixture
    def test_region(self, session: Session):
        """Create test region."""
        region = Region(
            region_key=f"TEST_{uuid.uuid4().hex[:8]}",
            region_name="Test Region",
            country_code="US",
        )
        session.add(region)
        session.commit()
        session.refresh(region)
        return region

    @pytest.fixture
    def test_campaign(self, session: Session, test_region: Region):
        """Create test campaign."""
        campaign = Campaign(
            unique_name=f"test_{uuid.uuid4().hex[:8]}",
            title="Test Campaign",
            year="2024",
            region_id=test_region.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
        return campaign

    def test_no_jwt_required_for_campaign_list(self, client: TestClient):
        """Should list campaigns without JWT token.

        NOTE: Currently no auth is required. This test documents current behavior.
        """
        response = client.get("/api/campaigns")

        assert response.status_code == 200

    def test_no_jwt_required_for_campaign_detail(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should get campaign details without JWT token.

        NOTE: Currently no auth is required. This test documents current behavior.
        """
        response = client.get(f"/api/campaigns/{test_campaign.id}")

        assert response.status_code == 200

    def test_no_jwt_required_for_session_list(self, client: TestClient):
        """Should list sessions without JWT token.

        NOTE: Currently no auth is required. This test documents current behavior.
        """
        response = client.get("/api/sessions")

        assert response.status_code == 200

    def test_expired_token_not_tested(self):
        """Expired token rejection not applicable - no JWT auth implemented.

        NOTE: When JWT auth is added, add test for expired token rejection.
        """
        pass

    def test_tampered_token_not_tested(self):
        """Tampered token rejection not applicable - no JWT auth implemented.

        NOTE: When JWT auth is added, add test for tampered token rejection.
        """
        pass

    def test_missing_token_not_tested(self):
        """Missing token 401 not applicable - no JWT auth implemented.

        NOTE: When JWT auth is added, add test for missing token returns 401.
        """
        pass
