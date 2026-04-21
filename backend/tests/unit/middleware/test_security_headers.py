"""Tests for SecurityHeadersMiddleware.

Crosslink #17 — Spec: Security Headers Middleware.
Contract: every response includes OWASP-recommended security headers.
Environment-conditional: HSTS (production only), CSP report-only (dev).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from app.middleware.security_headers import SecurityHeadersMiddleware


def _create_test_app(is_production: bool = False) -> FastAPI:
    app = FastAPI()

    app.add_middleware(SecurityHeadersMiddleware, is_production=is_production)

    @app.get("/test")
    async def test_endpoint():
        return PlainTextResponse("ok")

    @app.get("/health")
    async def health():
        return PlainTextResponse("healthy")

    @app.options("/preflight")
    async def preflight():
        return PlainTextResponse("")

    return app


class TestSecurityHeadersAlwaysPresent:
    """Headers that must appear on every response regardless of environment."""

    @pytest.fixture
    def client(self):
        return TestClient(_create_test_app(is_production=False))

    def test_x_content_type_options_nosniff(self, client: TestClient):
        response = client.get("/test")
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_x_frame_options_deny(self, client: TestClient):
        response = client.get("/test")
        assert response.headers["x-frame-options"] == "DENY"

    def test_referrer_policy(self, client: TestClient):
        response = client.get("/test")
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client: TestClient):
        response = client.get("/test")
        policy = response.headers["permissions-policy"]
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy

    def test_no_x_request_id_in_security_middleware(self, client: TestClient):
        response = client.get("/test")
        assert "x-request-id" not in response.headers

    def test_correlation_id_not_in_security_middleware(self, client: TestClient):
        response = client.get("/test")
        assert "x-correlation-id" not in response.headers

    def test_headers_on_health_endpoint(self, client: TestClient):
        response = client.get("/health")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"

    def test_headers_on_options_preflight(self, client: TestClient):
        response = client.options("/preflight")
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_does_not_overwrite_existing_header(self):
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, is_production=False)

        @app.get("/custom")
        async def custom():
            resp = PlainTextResponse("ok")
            resp.headers["X-Frame-Options"] = "SAMEORIGIN"
            return resp

        client = TestClient(app)
        response = client.get("/custom")
        assert response.headers["x-frame-options"] == "SAMEORIGIN"


class TestSecurityHeadersDevelopment:
    """Headers that behave differently in development mode."""

    @pytest.fixture
    def client(self):
        return TestClient(_create_test_app(is_production=False))

    def test_no_hsts_in_development(self, client: TestClient):
        response = client.get("/test")
        assert "strict-transport-security" not in response.headers

    def test_csp_report_only_in_development(self, client: TestClient):
        response = client.get("/test")
        assert "content-security-policy-report-only" in response.headers
        csp = response.headers["content-security-policy-report-only"]
        assert "default-src 'self'" in csp

    def test_no_enforcing_csp_in_development(self, client: TestClient):
        response = client.get("/test")
        assert "content-security-policy" not in response.headers


class TestSecurityHeadersProduction:
    """Headers that behave differently in production mode."""

    @pytest.fixture
    def client(self):
        return TestClient(_create_test_app(is_production=True))

    def test_hsts_in_production(self, client: TestClient):
        response = client.get("/test")
        hsts = response.headers["strict-transport-security"]
        assert "max-age=63072000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    def test_csp_enforcing_in_production(self, client: TestClient):
        response = client.get("/test")
        assert "content-security-policy" in response.headers
        csp = response.headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_no_csp_report_only_in_production(self, client: TestClient):
        response = client.get("/test")
        assert "content-security-policy-report-only" not in response.headers
