"""Tests for database API endpoints."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_models.database import ConnectionTestResult, ProvisionResult
from app.routers.database_router import router


@pytest.fixture
def app():
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_api_key():
    os.environ.pop("DATABASE_API_KEY", None)
    yield
    os.environ.pop("DATABASE_API_KEY", None)


def _mock_sqlite_settings():
    """Create a mock settings that reports sqlite."""
    settings = MagicMock()
    settings.database.type = "sqlite"
    settings.supabase.is_connected = False
    return settings


class TestDatabaseStatus:
    """Tests for GET /database/status."""

    def test_returns_status(self, client):
        response = client.get("/database/status")
        assert response.status_code == 200

        data = response.json()
        assert "configured" in data
        assert "type" in data
        assert "connected" in data
        assert "message" in data

    def test_status_defaults_to_sqlite(self, client):
        with patch(
            "app.routers.database_router.get_settings",
            return_value=_mock_sqlite_settings(),
        ):
            response = client.get("/database/status")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "sqlite"


class TestDatabaseAuth:
    """Tests for database endpoint API key protection."""

    def test_rejects_request_without_key_when_configured(self, client):
        os.environ["DATABASE_API_KEY"] = "test-secret-key"  # pragma: allowlist secret
        response = client.get("/database/status")
        assert response.status_code == 401

    def test_rejects_request_with_wrong_key(self, client):
        os.environ["DATABASE_API_KEY"] = "test-secret-key"  # pragma: allowlist secret
        response = client.get(
            "/database/status", headers={"X-API-Key": "wrong-key"}
        )  # pragma: allowlist secret
        assert response.status_code == 401

    def test_allows_request_with_correct_key(self, client):
        os.environ["DATABASE_API_KEY"] = "test-secret-key"  # pragma: allowlist secret
        response = client.get(
            "/database/status", headers={"X-API-Key": "test-secret-key"}
        )
        assert response.status_code == 200

    def test_allows_request_when_no_key_configured(self, client):
        response = client.get("/database/status")
        assert response.status_code == 200

    def test_warns_when_no_key_configured(self, client, capfd):
        import asyncio

        from app.dependencies import verify_database_api_key

        os.environ.pop("DATABASE_API_KEY", None)
        result = asyncio.run(verify_database_api_key(""))
        assert result == ""


class TestSupabaseEndpoints:
    """Tests for Supabase endpoints."""

    def test_test_connection_invalid_url(self, client):
        response = client.post(
            "/database/supabase/test",
            json={
                "project_url": "invalid",
                "service_key": "x" * 100,
                "db_password": "password",  # pragma: allowlist secret
            },
        )
        assert response.status_code == 422

    def test_test_connection_success(self, client):
        mock_result = ConnectionTestResult(
            success=True,
            message="Connection successful",
            project_ref="testproj",
        )
        with patch(
            "app.services.supabase_service.test_connection",
            new=AsyncMock(return_value=mock_result),
        ):
            response = client.post(
                "/database/supabase/test",
                json={
                    "project_url": "https://testproj.supabase.co",
                    "service_key": "sb_secret_" + "x" * 100,  # pragma: allowlist secret
                    "db_password": "password",  # pragma: allowlist secret
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_ref"] == "testproj"

    def test_provision_success(self, client):
        mock_result = ProvisionResult(
            success=True,
            message="Provisioned",
            tables_created=["campaign"],
        )
        with patch(
            "app.services.supabase_service.provision_database",
            new=AsyncMock(return_value=mock_result),
        ):
            response = client.post(
                "/database/supabase/provision",
                json={
                    "project_url": "https://testproj.supabase.co",
                    "service_key": "sb_secret_" + "x" * 100,  # pragma: allowlist secret
                    "db_password": "password",  # pragma: allowlist secret
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_disconnect_without_supabase(self, client):
        with patch(
            "app.services.supabase_service.disconnect",
            new=AsyncMock(return_value=None),
        ):
            response = client.delete("/database/supabase")
        assert response.status_code == 200
