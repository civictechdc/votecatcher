"""Tests for ProviderConfig, resolve_provider_config, and provider extractors."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ocr.ocr_client_factory import (
    ProviderConfig,
    _extract_gemini,
    _extract_mistral,
    _extract_openai,
    resolve_provider_config,
)
from app.settings import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


FAKE_BASE64 = "iVBORw0KGgo="

MOCK_OCR_RESPONSE = {
    "data": [
        {"Name": "John", "Address": "123 Main St", "Date": "2024-01-01", "Ward": "1"}
    ]
}


class TestProviderConfig:
    def test_fields(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="openai",
            api_key="sk-test",  # pragma: allowlist secret
            model="gpt-4o",  # pragma: allowlist secret
        )
        assert config.provider == "openai"
        assert config.api_key == "sk-test"  # pragma: allowlist secret
        assert config.model == "gpt-4o"

    def test_repr_hides_api_key(self):
        config = ProviderConfig(
            provider="openai",
            api_key="sk-secret-key",  # pragma: allowlist secret
            model="gpt-4o",  # pragma: allowlist secret
        )
        r = repr(config)
        assert "sk-secret-key" not in r
        assert "gpt-4o" in r
        assert "openai" in r


class TestResolveProviderConfigFromDB:
    def test_returns_db_config_when_available(self):
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_config.api_key = "db-key"  # pragma: allowlist secret
        mock_config.model = "db-model"
        mock_config.provider = "openai"
        mock_session.exec.return_value.first.return_value = mock_config

        result = resolve_provider_config(session=mock_session)

        assert result.api_key == "db-key"  # pragma: allowlist secret
        assert result.model == "db-model"
        assert result.provider == "openai"

    def test_returns_specific_provider_from_db(self):
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_config.api_key = "gemini-key"  # pragma: allowlist secret
        mock_config.model = "gemini-model"
        mock_config.provider = "gemini"
        mock_session.exec.return_value.first.return_value = mock_config

        result = resolve_provider_config(provider="gemini", session=mock_session)

        assert result.provider == "gemini"
        assert result.api_key == "gemini-key"  # pragma: allowlist secret

    def test_skips_db_config_with_missing_api_key(self):
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_config.api_key = None
        mock_config.model = "model"
        mock_session.exec.return_value.first.return_value = mock_config

        with patch.dict(
            os.environ,
            {
                "OCR_PROVIDER_NAME": "openai",
                "OCR_PROVIDER_MODEL": "gpt-4o",
                "OCR_PROVIDER_API_KEY": "env-key",  # pragma: allowlist secret
            },
            clear=False,
        ):
            result = resolve_provider_config(session=mock_session)
            assert result.api_key == "env-key"  # pragma: allowlist secret

    def test_skips_db_config_with_missing_model(self):
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_config.api_key = "key"  # pragma: allowlist secret
        mock_config.model = None
        mock_session.exec.return_value.first.return_value = mock_config

        with patch.dict(
            os.environ,
            {
                "OCR_PROVIDER_NAME": "openai",
                "OCR_PROVIDER_MODEL": "gpt-4o",
                "OCR_PROVIDER_API_KEY": "env-key",  # pragma: allowlist secret
            },
            clear=False,
        ):
            result = resolve_provider_config(session=mock_session)
            assert result.api_key == "env-key"  # pragma: allowlist secret


class TestResolveProviderConfigFromEnv:
    def test_falls_back_to_env_vars(self):
        with patch.dict(
            os.environ,
            {
                "OCR_PROVIDER_NAME": "openai",
                "OCR_PROVIDER_MODEL": "gpt-4o-mini",
                "OCR_PROVIDER_API_KEY": "sk-env-key",  # pragma: allowlist secret
            },
            clear=False,
        ):
            result = resolve_provider_config()
            assert result.provider == "openai"
            assert result.model == "gpt-4o-mini"
            assert result.api_key == "sk-env-key"  # pragma: allowlist secret

    def test_env_vars_work_without_session(self):
        with patch.dict(
            os.environ,
            {
                "OCR_PROVIDER_NAME": "mistral",
                "OCR_PROVIDER_MODEL": "mistral-large",
                "OCR_PROVIDER_API_KEY": "mistral-key",  # pragma: allowlist secret
            },
            clear=False,
        ):
            result = resolve_provider_config()
            assert result.provider == "mistral"

    def test_env_incomplete_does_not_resolve(self):
        with (
            patch.dict(
                os.environ,
                {
                    "OCR_PROVIDER_NAME": "openai",
                },
                clear=False,
            ),
            pytest.raises(ValueError, match="No OCR provider configured"),
        ):
            resolve_provider_config()


class TestResolveProviderConfigError:
    def test_raises_when_no_db_and_no_env(self):
        with (
            patch.dict(os.environ, {}, clear=False),
            pytest.raises(ValueError, match="No OCR provider configured"),
        ):
            resolve_provider_config()

    def test_raises_with_partial_env_vars(self):
        with (
            patch.dict(
                os.environ,
                {
                    "OCR_PROVIDER_NAME": "openai",
                    "OCR_PROVIDER_API_KEY": "key",  # pragma: allowlist secret
                },
                clear=False,
            ),
            pytest.raises(ValueError, match="No OCR provider configured"),
        ):
            resolve_provider_config()


class TestDBPreferredOverEnv:
    def test_db_takes_priority_over_env(self):
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_config.api_key = "db-key"  # pragma: allowlist secret
        mock_config.model = "db-model"
        mock_config.provider = "openai"
        mock_session.exec.return_value.first.return_value = mock_config

        with patch.dict(
            os.environ,
            {
                "OCR_PROVIDER_NAME": "mistral",
                "OCR_PROVIDER_MODEL": "mistral-large",
                "OCR_PROVIDER_API_KEY": "env-key",  # pragma: allowlist secret
            },
            clear=False,
        ):
            result = resolve_provider_config(session=mock_session)
            assert result.api_key == "db-key"  # pragma: allowlist secret
            assert result.provider == "openai"


class TestExtractOpenAI:
    @pytest.mark.asyncio
    async def test_returns_parsed_data(self):
        config = ProviderConfig(
            provider="openai",
            api_key="sk-test",  # pragma: allowlist secret
            model="gpt-4o",
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_OCR_RESPONSE)

        with patch("openai.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await _extract_openai(config, FAKE_BASE64)

        assert result == MOCK_OCR_RESPONSE["data"]

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_content(self):
        _key = "openai-placeholder"
        config = ProviderConfig(
            provider="openai",
            api_key=_key,
            model="gpt-4o",
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("openai.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await _extract_openai(config, FAKE_BASE64)

        assert result == []


class TestExtractGemini:
    @pytest.mark.asyncio
    async def test_returns_parsed_data(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="gemini",
            api_key="gem-key",  # pragma: allowlist secret
            model="gemini-2.0-flash",  # pragma: allowlist secret
        )
        mock_response = MagicMock()
        mock_response.text = json.dumps(MOCK_OCR_RESPONSE)

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )
            mock_client_cls.return_value = mock_client

            result = await _extract_gemini(config, FAKE_BASE64)

        assert result == MOCK_OCR_RESPONSE["data"]

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_text(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="gemini",
            api_key="gem-key",  # pragma: allowlist secret
            model="gemini-2.0-flash",  # pragma: allowlist secret
        )
        mock_response = MagicMock()
        mock_response.text = None

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )
            mock_client_cls.return_value = mock_client

            result = await _extract_gemini(config, FAKE_BASE64)

        assert result == []


class TestExtractMistral:
    @pytest.mark.asyncio
    async def test_returns_parsed_data(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="mistral",
            api_key="mist-key",  # pragma: allowlist secret
            model="mistral-large",  # pragma: allowlist secret
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(MOCK_OCR_RESPONSE)

        with patch("mistralai.client.Mistral") as mock_mistral_cls:
            mock_client = MagicMock()
            mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
            mock_mistral_cls.return_value = mock_client

            result = await _extract_mistral(config, FAKE_BASE64)

        assert result == MOCK_OCR_RESPONSE["data"]

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_content(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="mistral",
            api_key="mist-key",  # pragma: allowlist secret
            model="mistral-large",  # pragma: allowlist secret
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("mistralai.client.Mistral") as mock_mistral_cls:
            mock_client = MagicMock()
            mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
            mock_mistral_cls.return_value = mock_client

            result = await _extract_mistral(config, FAKE_BASE64)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_list_content(self):
        config = ProviderConfig(  # pragma: allowlist secret
            provider="mistral",
            api_key="mist-key",  # pragma: allowlist secret
            model="mistral-large",  # pragma: allowlist secret
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ["not", "a", "string"]

        with patch("mistralai.client.Mistral") as mock_mistral_cls:
            mock_client = MagicMock()
            mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
            mock_mistral_cls.return_value = mock_client

            result = await _extract_mistral(config, FAKE_BASE64)

        assert result == []
