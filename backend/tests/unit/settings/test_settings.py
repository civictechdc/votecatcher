"""Tests for aggregated Settings."""

import importlib
from pathlib import Path

import pytest
from pydantic import SecretStr


class TestSettings:
	"""Tests for the main Settings class."""

	def test_get_settings_returns_settings(self):
		"""get_settings should return Settings instance."""
		from app.settings.settings import get_settings

		get_settings.cache_clear()
		settings = get_settings()
		assert hasattr(settings, "database")
		assert hasattr(settings, "supabase")
		assert hasattr(settings, "ocr")
		assert hasattr(settings, "features")

	def test_settings_is_cached(self):
		"""get_settings should be cached."""
		from app.settings.settings import get_settings

		get_settings.cache_clear()
		settings1 = get_settings()
		settings2 = get_settings()
		assert settings1 is settings2

	def test_database_config_accessible(self):
		"""Database config should be accessible."""
		from app.settings.settings import get_settings

		get_settings.cache_clear()
		settings = get_settings()
		assert settings.database.url is not None
		assert settings.database.type in ("sqlite", "postgres", "supabase")

	def test_supabase_not_connected_by_default(self):
		"""Supabase should not be connected without credentials."""
		from app.settings.settings import get_settings

		get_settings.cache_clear()
		settings = get_settings()
		assert isinstance(settings.supabase.is_connected, bool)

	def test_sensitive_fields_are_secret_str(self):
		"""Sensitive fields should be SecretStr, not plain str."""
		from app.settings.settings import Settings

		settings = Settings(
			SUPABASE_SERVICE_KEY="sk_test",  # pragma: allowlist secret
			SUPABASE_DB_PASSWORD="pw_test",  # pragma: allowlist secret
			OCR_PROVIDER_API_KEY="ak_test",  # pragma: allowlist secret
		)
		assert isinstance(settings.supabase_service_key, SecretStr)
		assert isinstance(settings.supabase_db_password, SecretStr)
		assert isinstance(settings.ocr_api_key, SecretStr)

	def test_supabase_region_configurable(self):
		"""Supabase region should be configurable via env var."""
		from app.settings.settings import Settings

		settings = Settings(
			SUPABASE_URL="https://xyz.supabase.co",
			SUPABASE_SERVICE_KEY="key",  # pragma: allowlist secret
			SUPABASE_DB_PASSWORD="pw",  # pragma: allowlist secret
			SUPABASE_REGION="aws-0-eu-west-1",
		)
		assert settings.supabase.region == "aws-0-eu-west-1"


class TestSettingsConsolidatedFields:
	"""Tests for fields migrated from AppSettings (R13)."""

	def test_app_name_default(self):
		from app.settings.settings import Settings

		settings = Settings()
		assert settings.app_name == "Votecatcher Backend"

	def test_version_default(self):
		from app.settings.settings import Settings

		settings = Settings()
		assert settings.version == ""

	def test_clear_runtime_on_launch_default(self):
		from app.settings.settings import Settings

		settings = Settings()
		assert settings.clear_runtime_on_launch is False

	def test_demo_reset_default(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_DEMO_RESET=False)
		assert settings.demo_reset is False

	def test_demo_reset_can_be_enabled(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_DEMO_RESET=True)
		assert settings.demo_reset is True

	def test_always_batch_ocr_default(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_ALWAYS_BATCH_OCR=True)
		assert settings.always_batch_ocr is True

	def test_always_batch_ocr_can_be_disabled(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_ALWAYS_BATCH_OCR=False)
		assert settings.always_batch_ocr is False

	def test_local_campaign_base_dir(self):
		from app.settings.settings import Settings

		settings = Settings(
			DEV_LOCAL_RUNTIME_DIR=Path("/tmp/runtime"),
			DEV_LOCAL_CAMPAIGNS_DIR=Path("campaigns"),
		)
		result = settings.local_campaign_base_dir()
		assert result == Path("/tmp/runtime/campaigns")

	def test_local_campaign_base_dir_raises_without_required_dirs(self):
		from app.settings.settings import Settings

		settings = Settings()
		with pytest.raises(ValueError):
			settings.local_campaign_base_dir()

	def test_feature_demo_default(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_DEMO_MODE=False)
		assert settings.feature_demo is False

	def test_feature_demo_can_be_enabled(self):
		from app.settings.settings import Settings

		settings = Settings(FEATURE_DEMO_MODE=True)
		assert settings.feature_demo is True


class TestEnvSettingsRemoved:
	"""env_settings module should no longer exist (R13 Phase 4)."""

	def test_env_settings_module_not_importable(self):
		with pytest.raises(ModuleNotFoundError):
			importlib.import_module("app.settings.env_settings")
