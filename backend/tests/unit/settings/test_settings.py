"""Tests for aggregated Settings."""

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
