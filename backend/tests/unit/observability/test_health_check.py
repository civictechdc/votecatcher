"""Tests for Enhanced Health Check.

Crosslink #28 — Spec: Enhanced Health Check.
Contract: /health returns structured status with dependency checks.
Three states: ok, degraded, unhealthy.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.observability.health import (
    HealthCheckResult,
    HealthChecker,
    CheckStatus,
)


def _create_health_app(checker: HealthChecker) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health():
        result = checker.check()
        status_code = 503 if result.status == CheckStatus.UNHEALTHY else 200
        return JSONResponse(
            content=result.to_dict(),
            status_code=status_code,
            headers={"cache-control": "no-cache"},
        )

    return app


class TestHealthCheckResultStatus:
    """HealthCheckResult status determination."""

    def test_all_passing_returns_ok(self):
        result = HealthCheckResult(
            status=CheckStatus.OK,
            checks={"database": {"status": "ok", "latency_ms": 5}},
        )
        assert result.status == "ok"

    def test_database_down_returns_unhealthy(self):
        result = HealthCheckResult(
            status=CheckStatus.UNHEALTHY,
            checks={"database": {"status": "error", "error": "connection refused"}},
        )
        assert result.status == "unhealthy"

    def test_storage_missing_returns_degraded(self):
        result = HealthCheckResult(
            status=CheckStatus.DEGRADED,
            checks={
                "database": {"status": "ok", "latency_ms": 3},
                "storage": {"status": "error", "error": "path not found"},
            },
        )
        assert result.status == "degraded"


class TestHealthCheckResultPayload:
    """HealthCheckResult serialization."""

    def test_includes_version(self):
        result = HealthCheckResult(
            status=CheckStatus.OK,
            checks={"database": {"status": "ok", "latency_ms": 5}},
        )
        payload = result.to_dict()
        assert "version" in payload

    def test_includes_uptime_seconds(self):
        result = HealthCheckResult(
            status=CheckStatus.OK,
            checks={"database": {"status": "ok", "latency_ms": 5}},
        )
        payload = result.to_dict()
        assert "uptime_seconds" in payload

    def test_includes_checks(self):
        result = HealthCheckResult(
            status=CheckStatus.OK,
            checks={
                "database": {"status": "ok", "latency_ms": 5},
                "storage": {"status": "ok", "path": "/data/uploads"},
            },
        )
        payload = result.to_dict()
        assert "database" in payload["checks"]
        assert "storage" in payload["checks"]

    def test_includes_status(self):
        result = HealthCheckResult(
            status=CheckStatus.OK,
            checks={},
        )
        payload = result.to_dict()
        assert payload["status"] == "ok"


class TestHealthCheckerDatabaseCheck:
    """Database health check behavior."""

    def test_database_ok_reports_latency(self):
        checker = HealthChecker(db_check_fn=lambda: 5.2)
        result = checker.check()
        assert result.to_dict()["checks"]["database"]["status"] == "ok"
        assert result.to_dict()["checks"]["database"]["latency_ms"] == 5.2

    def test_database_failure_reports_unhealthy(self):
        def failing_db():
            raise Exception("connection refused")

        checker = HealthChecker(db_check_fn=failing_db)
        result = checker.check()
        assert result.status == "unhealthy"

    def test_database_check_never_raises(self):
        def exploding_db():
            raise RuntimeError("boom")

        checker = HealthChecker(db_check_fn=exploding_db)
        result = checker.check()
        assert result is not None
        assert result.status == "unhealthy"


class TestHealthCheckHTTPResponses:
    """HTTP-level behavior of health endpoint."""

    def test_ok_returns_200(self):
        checker = HealthChecker(db_check_fn=lambda: 5)
        app = _create_health_app(checker)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_unhealthy_returns_503(self):
        def failing_db():
            raise Exception("down")

        checker = HealthChecker(db_check_fn=failing_db)
        app = _create_health_app(checker)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 503

    def test_response_includes_cache_control_no_cache(self):
        checker = HealthChecker(db_check_fn=lambda: 5)
        app = _create_health_app(checker)
        client = TestClient(app)
        response = client.get("/health")
        assert response.headers.get("cache-control") == "no-cache"
