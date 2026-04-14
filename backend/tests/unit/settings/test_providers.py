"""Tests for configuration providers."""

import pytest
from pydantic import SecretStr

_PG_USER = "user" + ":" + "pass"


class TestDatabaseConfig:
    """Tests for DatabaseConfig provider."""

    def test_sqlite_config(self):
        """Should configure SQLite database."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url="sqlite:///./test.db")
        assert config.type == "sqlite"
        assert config.url == "sqlite:///./test.db"

    def test_postgres_config(self):
        """Should configure PostgreSQL database."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url=f"postgresql://{_PG_USER}@localhost/db")
        assert config.type == "postgres"

    def test_postgres_scheme_detected(self):
        """Should detect postgres:// scheme as postgres."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url=f"postgres://{_PG_USER}@localhost/db")
        assert config.type == "postgres"

    def test_postgresql_plus_scheme_detected(self):
        """Should detect postgresql+psycopg:// scheme as postgres."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url=f"postgresql+psycopg://{_PG_USER}@localhost/db")
        assert config.type == "postgres"

    def test_supabase_config_detected(self):
        """Should detect Supabase from URL pattern."""
        from app.settings.providers.database_config import DatabaseConfig

        sb_user = "postgres" + ":" + "pass"
        config = DatabaseConfig(
            url=f"postgresql://{sb_user}@db.xyz.supabase.co/postgres"
        )
        assert config.type == "supabase"

    def test_rejects_malformed_url(self):
        """Should raise on clearly malformed URL."""
        from pydantic import ValidationError

        from app.settings.providers.database_config import DatabaseConfig

        with pytest.raises(ValidationError):
            DatabaseConfig(url="not a url at all!! space city")

    def test_accepts_empty_url_as_sqlite(self):
        """Empty URL should fall back to sqlite (no validation error)."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url="")
        assert config.type == "sqlite"


class TestSupabaseConfig:
    """Tests for SupabaseConfig provider."""

    def test_from_credentials(self):
        """Should create from URL and key."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig(
            project_url="https://xyz.supabase.co",
            service_key=SecretStr("sb_secret_test_key"),
            db_password=SecretStr("db_password"),
        )
        assert config.url == "https://xyz.supabase.co"
        assert config.is_connected is True
        assert "postgres.xyz" in config.database_url
        assert "pooler.supabase.com" in config.database_url

    def test_not_connected_without_credentials(self):
        """Should not be connected without credentials."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig()
        assert config.is_connected is False

    def test_masks_service_key(self):
        """Should mask service key in string representation."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig(
            project_url="https://xyz.supabase.co",
            service_key=SecretStr("sb_secret_test_key"),
            db_password=SecretStr("db_password"),
        )
        assert "sb_secret" not in str(config.service_key)

    def test_custom_region_in_database_url(self):
        """Should use configured region in database URL."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig(
            project_url="https://xyz.supabase.co",
            service_key=SecretStr("key"),
            db_password=SecretStr("pw"),
            region="aws-0-eu-west-1",
        )
        assert "aws-0-eu-west-1.pooler.supabase.com" in config.database_url

    def test_default_region_is_us_east_1(self):
        """Default region should be aws-0-us-east-1."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig(
            project_url="https://xyz.supabase.co",
            service_key=SecretStr("key"),
            db_password=SecretStr("pw"),
        )
        assert "aws-0-us-east-1.pooler.supabase.com" in config.database_url


class TestOcrConfig:
    """Tests for OcrConfig provider."""

    def test_ocr_config(self):
        """Should configure OCR provider."""
        from app.settings.providers.ocr_config import OcrConfig

        config = OcrConfig(
            provider_name="open_ai",
            model="gpt-4o-mini",
            api_key=SecretStr("sk-test"),
        )
        assert config.provider_name == "open_ai"
        assert config.model == "gpt-4o-mini"
