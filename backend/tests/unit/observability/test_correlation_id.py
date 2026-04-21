"""Tests for Correlation ID Middleware wiring.

Crosslink #27 — Spec: Correlation ID Middleware.
Contract: every response includes X-Correlation-ID header,
every structlog entry within a request includes request_id.
"""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from app.middleware.correlation import CorrelationIdMiddleware


def _create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return PlainTextResponse("ok")

    return app


class TestCorrelationIdHeaderPresent:
    """Every response must include X-Correlation-ID."""

    @pytest.fixture
    def client(self):
        return TestClient(_create_test_app())

    def test_response_includes_correlation_id_header(self, client: TestClient):
        response = client.get("/test")
        assert "X-Correlation-ID" in response.headers

    def test_correlation_id_is_valid_uuid4(self, client: TestClient):
        response = client.get("/test")
        correlation_id = response.headers["X-Correlation-ID"]
        uuid_obj = uuid.UUID(correlation_id)
        assert uuid_obj.version == 4

    def test_different_requests_get_different_ids(self, client: TestClient):
        r1 = client.get("/test")
        r2 = client.get("/test")
        assert r1.headers["X-Correlation-ID"] != r2.headers["X-Correlation-ID"]


class TestCorrelationIdPropagation:
    """Incoming X-Correlation-ID headers must be accepted."""

    @pytest.fixture
    def client(self):
        return TestClient(_create_test_app())

    def test_incoming_correlation_id_accepted(self, client: TestClient):
        incoming_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": incoming_id})
        assert response.headers["X-Correlation-ID"] == incoming_id

    def test_incoming_id_propagated_not_replaced(self, client: TestClient):
        incoming_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": incoming_id})
        assert response.headers["X-Correlation-ID"] == incoming_id


class TestCorrelationIdInMiddlewareStack:
    """CorrelationIdMiddleware must work alongside other middleware."""

    def test_works_with_security_headers(self):
        from app.middleware.security_headers import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
        app.add_middleware(SecurityHeadersMiddleware, is_production=False)

        @app.get("/test")
        async def handler():
            return PlainTextResponse("ok")

        client = TestClient(app)
        response = client.get("/test")
        assert "X-Correlation-ID" in response.headers
        assert "X-Content-Type-Options" in response.headers
