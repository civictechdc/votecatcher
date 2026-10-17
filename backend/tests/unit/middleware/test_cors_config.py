"""Tests for CORS configuration builder.

Contract: environment-aware CORS with explicit methods, production origin
validation, and fail-closed behavior when production origins are missing.
"""

import pytest

from app.middleware.cors import build_cors_config


class TestCORSDevelopmentDefaults:
    """CORS config when ENVIRONMENT is development or unset."""

    def test_default_origins_include_localhost(self):
        config = build_cors_config(environment="development", cors_origins="")
        assert "http://localhost" in config["allow_origins"]
        assert "http://localhost:5173" in config["allow_origins"]

    def test_explicit_methods_not_wildcard(self):
        config = build_cors_config(environment="development", cors_origins="")
        methods = config["allow_methods"]
        assert "*" not in methods
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods
        assert "OPTIONS" in methods
        assert "PATCH" in methods

    def test_allow_credentials_true(self):
        config = build_cors_config(environment="development", cors_origins="")
        assert config["allow_credentials"] is True

    def test_allow_headers_wildcard_in_dev(self):
        config = build_cors_config(environment="development", cors_origins="")
        assert config["allow_headers"] == ["*"]


class TestCORSProduction:
    """CORS config when ENVIRONMENT is production."""

    def test_origins_from_env_var(self):
        config = build_cors_config(
            environment="production",
            cors_origins="https://app.example.com,https://admin.example.com",
        )
        assert config["allow_origins"] == [
            "https://app.example.com",
            "https://admin.example.com",
        ]

    def test_origins_trims_whitespace(self):
        config = build_cors_config(
            environment="production", cors_origins=" https://a.com , https://b.com "
        )
        assert config["allow_origins"] == ["https://a.com", "https://b.com"]

    def test_origins_strips_trailing_slashes(self):
        config = build_cors_config(
            environment="production", cors_origins="https://a.com/,https://b.com"
        )
        assert config["allow_origins"] == ["https://a.com", "https://b.com"]

    def test_explicit_methods_not_wildcard(self):
        config = build_cors_config(
            environment="production", cors_origins="https://app.example.com"
        )
        methods = config["allow_methods"]
        assert "*" not in methods

    def test_explicit_headers_not_wildcard(self):
        config = build_cors_config(
            environment="production", cors_origins="https://app.example.com"
        )
        headers = config["allow_headers"]
        assert "*" not in headers
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert "X-API-Key" in headers

    def test_missing_origins_raises_in_production(self):
        with pytest.raises(ValueError, match="CORS_ORIGINS"):
            build_cors_config(environment="production", cors_origins="")

    def test_whitespace_only_origins_raises_in_production(self):
        with pytest.raises(ValueError, match="CORS_ORIGINS"):
            build_cors_config(environment="production", cors_origins="   ")

    def test_comma_only_origins_raises_in_production(self):
        with pytest.raises(ValueError, match="CORS_ORIGINS"):
            build_cors_config(environment="production", cors_origins=",,,,")

    def test_wildcard_origins_raises_in_production(self):
        with pytest.raises(ValueError, match=r"\*"):
            build_cors_config(environment="production", cors_origins="*")

    def test_wildcard_mixed_with_explicit_origins_raises_in_production(self):
        with pytest.raises(ValueError, match="wildcard"):
            build_cors_config(
                environment="production",
                cors_origins="https://app.example.com,*",
            )

    def test_error_message_names_expected_format(self):
        with pytest.raises(ValueError) as excinfo:
            build_cors_config(environment="production", cors_origins="")
        message = str(excinfo.value)
        assert "CORS_ORIGINS" in message
        assert "comma-separated" in message


class TestCORSConfigurationValidation:
    """Edge cases and validation."""

    def test_single_origin_no_comma(self):
        config = build_cors_config(
            environment="production", cors_origins="https://single.example.com"
        )
        assert config["allow_origins"] == ["https://single.example.com"]
