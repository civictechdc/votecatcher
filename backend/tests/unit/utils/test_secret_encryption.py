"""Unit tests for at-rest secret encryption helpers."""

import pytest

from app.data.database.model.llm_provider_config import LlmProviderConfig
from app.services.providers import get_decrypted_api_key
from app.settings import get_settings
from app.utils.secret_encryption import decrypt_secret, encrypt_secret, generate_key


@pytest.fixture(autouse=True)
def _encryption_key(monkeypatch: pytest.MonkeyPatch):
    key = generate_key().decode()
    monkeypatch.setenv("PROVIDER_CONFIG_SECRET", key)  # pragma: allowlist secret
    get_settings.cache_clear()
    yield key
    get_settings.cache_clear()


class TestEncryptSecret:
    def test_roundtrip(self):
        encrypted = encrypt_secret("sk-test-value")
        assert encrypted.startswith("enc:v1:")
        assert "sk-test-value" not in encrypted
        assert decrypt_secret(encrypted) == "sk-test-value"

    def test_same_plaintext_produces_different_tokens(self):
        assert encrypt_secret("sk-test-value") != encrypt_secret("sk-test-value")

    def test_rejects_empty_secret(self):
        with pytest.raises(ValueError, match="empty"):
            encrypt_secret("")

    def test_requires_configured_key(self, monkeypatch):
        monkeypatch.delenv("PROVIDER_CONFIG_SECRET", raising=False)
        get_settings.cache_clear()
        with pytest.raises(RuntimeError, match="PROVIDER_CONFIG_SECRET"):
            encrypt_secret("sk-test-value")
        get_settings.cache_clear()


class TestDecryptSecret:
    def test_rejects_legacy_plaintext(self):
        with pytest.raises(ValueError, match="enc:v1:"):
            decrypt_secret("plaintext-key")

    def test_rejects_value_encrypted_with_wrong_key(self, monkeypatch):
        encrypted = encrypt_secret("sk-test-value")
        monkeypatch.setenv("PROVIDER_CONFIG_SECRET", generate_key().decode())
        get_settings.cache_clear()
        with pytest.raises(ValueError, match="wrong or rotated key"):
            decrypt_secret(encrypted)
        get_settings.cache_clear()

    def test_rejects_garbage_prefixed_value(self):
        with pytest.raises(ValueError):
            decrypt_secret("enc:v1:not-a-token")


class TestGetDecryptedApiKeyFailClosed:
    def test_unset_secret_with_encrypted_row_returns_none(self, monkeypatch):
        import structlog

        encrypted = encrypt_secret("sk-test-value")
        monkeypatch.delenv("PROVIDER_CONFIG_SECRET", raising=False)
        get_settings.cache_clear()
        config = LlmProviderConfig(
            provider="openai", api_key=encrypted, model="gpt-4o", is_configured=True
        )
        with structlog.testing.capture_logs() as cap_logs:
            assert get_decrypted_api_key(config) is None
        assert any("PROVIDER_CONFIG_SECRET" in entry["event"] for entry in cap_logs)
        get_settings.cache_clear()

    def test_legacy_plaintext_row_returns_none(self):
        config = LlmProviderConfig(
            provider="openai",
            api_key="plaintext-key",  # pragma: allowlist secret
            model="gpt-4o",
        )
        assert get_decrypted_api_key(config) is None

    def test_none_config_returns_none(self):
        assert get_decrypted_api_key(None) is None
