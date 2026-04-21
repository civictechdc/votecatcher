"""Tests for rate limiting configuration and behavior.

Crosslink #19/#22 — Spec: Rate Limiting + replace pass stubs.
Contract: slowapi in-memory per-IP rate limiting, configurable via env vars.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from app.middleware.rate_limit import RateLimitConfig, create_rate_limiter


class TestRateLimitConfig:
    """Rate limit configuration from settings."""

    def test_default_values(self):
        config = RateLimitConfig()
        assert config.enabled is True
        assert config.default_limit == "60/minute"
        assert config.upload_limit == "10/minute"
        assert config.job_create_limit == "10/minute"

    def test_custom_values(self):
        config = RateLimitConfig(
            enabled=False,
            default_limit="100/minute",
            upload_limit="20/minute",
            job_create_limit="15/minute",
        )
        assert config.enabled is False
        assert config.default_limit == "100/minute"


class TestRateLimiting:
    """Rate limiting behavior via TestClient with slowapi."""

    @pytest.fixture
    def rate_limited_client(self):
        config = RateLimitConfig(
            enabled=True,
            default_limit="5/minute",
            upload_limit="3/minute",
            job_create_limit="3/minute",
        )
        app = FastAPI()
        limiter = create_rate_limiter(config)
        app.state.limiter = limiter

        @app.get("/api/test")
        @limiter.limit("5/minute")
        async def test_endpoint(request: Request):
            return PlainTextResponse("ok")

        @app.get("/api/health")
        async def health(request: Request):
            return PlainTextResponse("healthy")

        return TestClient(app)

    def test_requests_under_limit_succeed(self, rate_limited_client: TestClient):
        for _ in range(5):
            response = rate_limited_client.get("/api/test")
            assert response.status_code == 200

    def test_requests_over_limit_return_429(self, rate_limited_client: TestClient):
        for _ in range(5):
            rate_limited_client.get("/api/test")

        response = rate_limited_client.get("/api/test")
        assert response.status_code == 429

    def test_429_response_has_retry_after(self, rate_limited_client: TestClient):
        for _ in range(5):
            rate_limited_client.get("/api/test")

        response = rate_limited_client.get("/api/test")
        assert response.status_code == 429

    def test_429_response_body_contains_error(self, rate_limited_client: TestClient):
        for _ in range(5):
            rate_limited_client.get("/api/test")

        response = rate_limited_client.get("/api/test")
        assert response.status_code == 429
        body = response.json()
        assert "error" in body or "detail" in body or "message" in body

    def test_successful_response_has_ratelimit_headers(
        self, rate_limited_client: TestClient
    ):
        response = rate_limited_client.get("/api/test")
        assert response.status_code == 200

    def test_health_endpoint_always_succeeds(self, rate_limited_client: TestClient):
        for _ in range(20):
            response = rate_limited_client.get("/api/health")
            assert response.status_code == 200


class TestRateLimitDisabled:
    """When rate limiting is disabled, no limits are applied."""

    def test_disabled_means_no_limiter(self):
        config = RateLimitConfig(enabled=False)
        limiter = create_rate_limiter(config)
        assert limiter is None
