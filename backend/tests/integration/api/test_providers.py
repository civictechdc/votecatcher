"""Integration tests for provider settings endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet
from sqlmodel import delete, select

from app.data.database.model.llm_provider_config import LlmProviderConfig

_FAKE_KEY = "test-placeholder-not-a-real-key"

_PROVIDER_SECRET = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _provider_secret(monkeypatch: pytest.MonkeyPatch):
    """Give provider tests a valid encryption key for stored credentials."""
    monkeypatch.setenv("PROVIDER_CONFIG_SECRET", _PROVIDER_SECRET)
    from app.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestProviderAuth:
    """Mirrors the database endpoint API key protection."""

    def test_rejects_request_without_key_when_configured(self, client, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_API_KEY", "test-secret-key"
        )  # pragma: allowlist secret
        response = client.get("/api/settings/providers")
        assert response.status_code == 401

    def test_rejects_request_with_wrong_key(self, client, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_API_KEY", "test-secret-key"
        )  # pragma: allowlist secret
        response = client.get(
            "/api/settings/providers", headers={"X-API-Key": "wrong-key"}
        )  # pragma: allowlist secret
        assert response.status_code == 401

    def test_allows_request_with_correct_key(self, client, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_API_KEY", "test-secret-key"
        )  # pragma: allowlist secret
        response = client.get(
            "/api/settings/providers", headers={"X-API-Key": "test-secret-key"}
        )
        assert response.status_code == 200

    def test_allows_request_when_no_key_configured(self, client, monkeypatch):
        monkeypatch.delenv("DATABASE_API_KEY", raising=False)
        response = client.get("/api/settings/providers")
        assert response.status_code == 200


class TestListProviders:
    def test_list_providers_returns_all_supported(self, client, session):
        response = client.get("/api/settings/providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        provider_names = [p["provider"] for p in data]
        assert "openai" in provider_names
        assert "gemini" in provider_names
        assert "mistral" in provider_names

    def test_list_providers_shows_unconfigured_state(self, client, session):
        session.exec(delete(LlmProviderConfig))
        session.commit()
        response = client.get("/api/settings/providers")
        data = response.json()
        for provider in data:
            assert provider["is_configured"] is False
            assert provider["last_validated"] is None


class TestConfigureProvider:
    def test_configure_provider_success(self, client, session):
        response = client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"
        assert data["is_configured"] is True

    def test_configure_unsupported_provider_fails(self, client):
        response = client.post(
            "/api/settings/providers/unknown",
            json={"api_key": _FAKE_KEY, "model": "test-model"},
        )
        assert response.status_code == 400

    def test_configure_provider_updates_existing(self, client, session):
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        response = client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o-mini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o-mini"

    def test_list_providers_shows_configured(self, client, session):
        client.post(
            "/api/settings/providers/gemini",
            json={"api_key": _FAKE_KEY, "model": "gemini-1.5-pro"},
        )
        response = client.get("/api/settings/providers")
        data = response.json()
        gemini = next(p for p in data if p["provider"] == "gemini")
        assert gemini["is_configured"] is True
        assert gemini["model"] == "gemini-1.5-pro"


class TestDeleteProvider:
    def test_delete_provider_success(self, client, session):
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        response = client.delete("/api/settings/providers/openai")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        response = client.get("/api/settings/providers")
        data = response.json()
        openai = next(p for p in data if p["provider"] == "openai")
        assert openai["is_configured"] is False

    def test_delete_nonexistent_provider(self, client):
        response = client.delete("/api/settings/providers/openai")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestTestProvider:
    @patch("app.services.providers.AsyncOpenAI")
    def test_test_provider_invalid_key(self, mock_openai_cls, client):
        mock_openai_cls.return_value.models.list = AsyncMock(
            side_effect=Exception("Error code: 401 - Invalid API key provided")
        )
        response = client.post(
            "/api/settings/providers/openai/test",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None

    def test_test_unsupported_provider(self, client):
        response = client.post(
            "/api/settings/providers/unknown/test",
            json={"api_key": _FAKE_KEY, "model": "test-model"},
        )
        assert response.status_code == 400


class TestProviderSecretEncryption:
    def test_save_with_unset_secret_returns_4xx(self, client, monkeypatch):
        monkeypatch.delenv("PROVIDER_CONFIG_SECRET", raising=False)
        from app.settings import get_settings

        get_settings.cache_clear()
        response = client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        assert response.status_code == 400
        assert "PROVIDER_CONFIG_SECRET" in response.json()["detail"]
        get_settings.cache_clear()

    def test_save_stores_encrypted_value(self, client, session):
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        stored = session.exec(select(LlmProviderConfig)).all()
        openai_rows = [c for c in stored if c.provider == "openai"]
        assert len(openai_rows) == 1
        assert openai_rows[0].api_key.startswith("enc:v1:")
        assert _FAKE_KEY not in (openai_rows[0].api_key or "")

    def test_configured_provider_still_functions_through_service(self, client, session):
        from app.services.providers import (
            get_all_providers,
            get_decrypted_api_key,
            get_provider_config,
        )

        session.exec(delete(LlmProviderConfig))
        session.commit()
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": _FAKE_KEY, "model": "gpt-4o"},
        )
        config = get_provider_config(session, "openai")
        assert config is not None
        assert get_decrypted_api_key(config) == _FAKE_KEY
        configured = [p for p in get_all_providers(session) if p.is_configured]
        assert [p.provider for p in configured] == ["openai"]

    def test_legacy_plaintext_value_is_treated_as_unconfigured(self, session):
        from app.services.providers import get_decrypted_api_key

        session.exec(delete(LlmProviderConfig))
        session.commit()
        session.add(
            LlmProviderConfig(
                provider="openai", api_key=_FAKE_KEY, model="gpt-4o", is_configured=True
            )
        )
        session.commit()
        config = session.exec(select(LlmProviderConfig)).first()
        assert config is not None
        assert get_decrypted_api_key(config) is None
        # Do not leak the legacy plaintext row into other tests sharing this
        # database.
        session.exec(delete(LlmProviderConfig))
        session.commit()

    def test_wrong_key_fails_closed(self, monkeypatch):
        from app.services.providers import get_decrypted_api_key
        from app.utils.secret_encryption import encrypt_secret

        monkeypatch.setenv("PROVIDER_CONFIG_SECRET", Fernet.generate_key().decode())
        from app.settings import get_settings

        get_settings.cache_clear()
        encrypted = encrypt_secret(_FAKE_KEY)
        monkeypatch.setenv("PROVIDER_CONFIG_SECRET", Fernet.generate_key().decode())
        get_settings.cache_clear()

        config = LlmProviderConfig(
            provider="openai", api_key=encrypted, model="gpt-4o", is_configured=True
        )
        assert get_decrypted_api_key(config) is None
