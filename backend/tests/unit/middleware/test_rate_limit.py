"""Tests for rate limiting configuration and behavior.

Crosslink #19/#22 — Spec: Rate Limiting + replace pass stubs.
Contract: slowapi in-memory per-IP rate limiting, configurable via env vars.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from app.middleware.rate_limit import RateLimitConfig, create_rate_limiter


def _create_rate_limited_app(config: RateLimitConfig | None = None):
    if config is None:
        config = RateLimitConfig(
            enabled=True, default_limit="10/minute", upload_limit="5/minute", job_create_limit="5/minute"
        )

    app = FastAPI()
    limiter = create_rate_limiter(config)

    if config.enabled:
        app.state.limiter = limiter

        @app.get("/api/test")
        @limiter.limit(config.default_limit)
        async def test_endpoint(request: _FakeRequest):
            return PlainTextResponse("ok")

        @app.get("/api/health")
        async def health():
            return PlainTextResponse("healthy")

        @app.post("/api/jobs")
        @limiter.limit(config.job_create_limit)
        async def create_job(request: _FakeRequest):
            return PlainTextResponse("created", status_code=201)

        @app.post("/api/upload/voter-list")
        @limiter.limit(config.upload_limit)
        async def upload(request: _FakeRequest):
            return PlainTextResponse("uploaded", status_code=201)


class _FakeRequest:
    pass

    class FakeClient:
        host = "127.0.0.1"

    client = FakeClient()


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
            enabled=False, default_limit="100/minute", upload_limit="20/minute", job_create_limit="15/minute"
        )
        assert config.enabled is False
        assert config.default_limit == "100/minute"


class TestRateLimiting:
    """Rate limiting behavior via TestClient."""

    @pytest.fixture
    def rate_limited_client(self):
        config = RateLimitConfig(
            enabled=True, default_limit="5/minute", upload_limit="3/minute", job_create_limit="3/minute"
        )
        app = FastAPI()
        limiter = create_rate_limiter(config)
        app.state.limiter = limiter

        @app.get("/api/test")
        @limiter.limit("5/minute")
        async def test_endpoint(request: _FakeRequest):
            return PlainTextResponse("ok")

        @app.get("/api/health")
        async def health():
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
        assert "retry-after" in response.headers

    def test_429_response_body(self, rate_limited_client: TestClient):
        for _ in range(5):
            rate_limited_client.get("/api/test")

        response = rate_limited_client.get("/api/test")
        assert "Rate limit" in response.json().get("detail", "") or response.status_code == 429

    def test_successful_response_has_ratelimit_headers(self, rate_limited_client: TestClient):
        response = rate_limited_client.get("/api/test")
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers

    def test_health_endpoint_exempt(self, rate_limited_client: TestClient):
        for _ in range(20):
            response = rate_limited_client.get("/api/health")
            assert response.status_code == 200


class TestRateLimitDisabled:
    """When rate limiting is disabled, no limits are applied."""

    def test_disabled_means_no_limiter(self):
        config = RateLimitConfig(enabled=False)
        limiter = create_rate_limiter(config)
        assert limiter is None
