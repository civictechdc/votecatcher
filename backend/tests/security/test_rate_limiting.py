"""Rate limiting tests.

Middleware stack is wired into api.py (SecurityHeadersMiddleware, CORS, slowapi Limiter).
The Limiter is attached to app.state.limiter but rate limit decorators are NOT yet applied
to individual routes. Until decorators are added, all endpoints are unthrottled.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.schema import Campaign, Region


class TestRateLimiting:
    """Tests for API rate limiting protection."""

    @pytest.fixture
    def test_region(self, session: Session):
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

    def test_limiter_attached_to_app_state(self, client: TestClient):
        """Slowapi Limiter should be attached to app.state.limiter."""
        assert hasattr(client.app.state, "limiter")

    def test_no_rate_limit_on_campaign_list(self, client: TestClient):
        """Endpoints without @limiter.limit() decorator are unthrottled."""
        for _ in range(100):
            response = client.get("/api/campaigns")
            assert response.status_code == 200

    def test_no_rate_limit_on_campaign_detail(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Endpoints without @limiter.limit() decorator are unthrottled."""
        for _ in range(100):
            response = client.get(f"/api/campaigns/{test_campaign.id}")
            assert response.status_code == 200

    def test_no_rate_limit_on_session_list(self, client: TestClient):
        """Endpoints without @limiter.limit() decorator are unthrottled."""
        for _ in range(100):
            response = client.get("/api/sessions")
            assert response.status_code == 200

    def test_no_rate_limit_on_job_creation(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Job creation endpoint is unthrottled until decorated."""
        for _i in range(10):
            response = client.post(
                "/api/jobs",
                json={
                    "campaign_id": str(test_campaign.id),
                    "provider_name": "openai",
                    "provider_model": "gpt-4",
                    "scan_ids": [],
                },
            )
            assert response.status_code in [201, 400, 422]

    def test_no_rate_limit_on_upload(self, client: TestClient, test_campaign: Campaign):
        """Upload endpoint is unthrottled until decorated."""
        for _i in range(10):
            response = client.post(
                "/api/upload/voter-list",
                data={"campaign_id": str(test_campaign.id)},
                files={"file": ("test.csv", "id,name\n1,Test", "text/csv")},
            )
            assert response.status_code in [201, 400, 404, 422]

    def test_rate_limit_429_not_returned(self, client: TestClient):
        """Undecorated endpoints never return 429."""
        for _ in range(100):
            response = client.get("/api/campaigns")
            assert response.status_code != 429

    def test_ip_based_rate_limit_per_ip(self, client: TestClient):
        """When rate limiting decorators are added, limits should be per-IP.

        TODO: Add test with different client IPs when route decorators are applied.
        """
        pass

    def test_user_based_rate_limit_not_implemented(self):
        """When auth is added, test that rate limits are per-user, not per-IP."""
        pass

    def test_endpoint_specific_rate_limits_not_implemented(self, client: TestClient):
        """When route decorators are added, test different limits per endpoint."""
        pass

    def test_rate_limit_burst_capacity_not_implemented(self, client: TestClient):
        """When rate limiting decorators are added, test burst capacity for spikes."""
        pass
