"""Integration tests for the security middleware stack.

Verifies that SecurityHeadersMiddleware, CORS config, and rate limiter
are wired correctly into the FastAPI app via TestClient.
"""

import pytest
from fastapi.testclient import TestClient


class TestSecurityHeadersIntegration:
    """Security headers injected on every response."""

    def test_nosniff_header(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_frame_guard(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers["x-frame-options"] == "DENY"

    def test_referrer_policy(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client: TestClient):
        response = client.get("/api/health")
        assert "camera=()" in response.headers["permissions-policy"]

    def test_request_id_present(self, client: TestClient):
        response = client.get("/api/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 36

    def test_request_id_unique_per_request(self, client: TestClient):
        r1 = client.get("/api/health")
        r2 = client.get("/api/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    def test_hsts_not_set_in_dev(self, client: TestClient):
        response = client.get("/api/health")
        assert "strict-transport-security" not in response.headers

    def test_csp_report_only_in_dev(self, client: TestClient):
        response = client.get("/api/health")
        assert "content-security-policy-report-only" in response.headers
        assert "content-security-policy" not in response.headers


class TestCORSIntegration:
    """CORS middleware configured via build_cors_config."""

    def test_cors_preflight_allowed(self, client: TestClient):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "http://localhost:5173" in response.headers.get("access-control-allow-origin", "")

    def test_cors_actual_request(self, client: TestClient):
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestRateLimiterIntegration:
    """Rate limiter attached to app but not yet enforcing on routes."""

    def test_limiter_in_app_state(self, client: TestClient):
        assert hasattr(client.app.state, "limiter")

    def test_endpoints_unthrottled_without_decorators(self, client: TestClient):
        for _ in range(20):
            response = client.get("/api/health")
            assert response.status_code == 200
