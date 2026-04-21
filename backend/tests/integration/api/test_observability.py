"""Integration tests for the observability stack.

Crosslink #37 — Tests that observability components are wired correctly
into the FastAPI app: health check, correlation IDs, and Sentry init.

Uses TestClient against the real app with dependency overrides.
"""

import uuid

from fastapi.testclient import TestClient


class TestHealthCheckIntegration:
    """Health endpoint returns structured check data from HealthChecker."""

    def test_health_returns_status_field(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert body["status"] in ("ok", "degraded", "unhealthy")

    def test_health_returns_checks_dict(self, client: TestClient):
        response = client.get("/api/health")
        body = response.json()
        assert "checks" in body
        assert isinstance(body["checks"], dict)

    def test_health_returns_version(self, client: TestClient):
        response = client.get("/api/health")
        body = response.json()
        assert "version" in body

    def test_health_returns_uptime(self, client: TestClient):
        response = client.get("/api/health")
        body = response.json()
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], (int, float))

    def test_health_database_check_present(self, client: TestClient):
        response = client.get("/api/health")
        body = response.json()
        assert "database" in body["checks"]

    def test_health_database_ok_when_db_available(self, client: TestClient):
        response = client.get("/api/health")
        body = response.json()
        db_check = body["checks"]["database"]
        assert db_check["status"] == "ok"

    def test_health_returns_cache_control_no_cache(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers.get("cache-control") == "no-cache"


class TestCorrelationIdIntegration:
    """CorrelationIdMiddleware wired as outermost middleware."""

    def test_correlation_id_on_health(self, client: TestClient):
        response = client.get("/api/health")
        assert "x-correlation-id" in response.headers

    def test_correlation_id_propagated_from_client(self, client: TestClient):
        cid = uuid.uuid4().hex
        response = client.get(
            "/api/health",
            headers={"X-Correlation-ID": cid},
        )
        assert response.headers["x-correlation-id"] == cid

    def test_correlation_id_unique_when_not_provided(self, client: TestClient):
        r1 = client.get("/api/health")
        r2 = client.get("/api/health")
        assert r1.headers["x-correlation-id"] != r2.headers["x-correlation-id"]


class TestSentryIntegration:
    """Sentry init called during lifespan without error."""

    def test_app_starts_without_sentry_dsn(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
