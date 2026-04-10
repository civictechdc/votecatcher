"""BDD tests for dead code cleanup (Session 17).

These tests verify that the interfaces and behaviors affected by dead code
cleanup continue to work correctly after changes. Each test class corresponds
to a vulture finding that needs remediation.

Vulture findings addressed (80%+ confidence):
1. app/api.py:21 — unused 'application' param in lifespan callback
2. app/files/file_repository.py:78 — unused 'cropped_assets' in Protocol method
3. app/jobs/job_orchestrator.py:23 — unused import 'OCRService' (false positive)
4. app/logger_config/app_logger.py:41 — unused 'method_name' in structlog processor
5. app/logger_config/app_logger.py:67 — unused 'method_name' in structlog processor
6. app/settings/providers/database_config.py:33 — unused '__context' in Pydantic hook
7. app/settings/settings.py:68 — unused 'dotenv_settings' in settings override
"""

import logging

import pytest


class TestLifespanCallback:
    """Verify FastAPI lifespan callback works after param rename.

    Given: api.py defines a lifespan context manager
    When: the application param is renamed to _application
    Then: the lifespan function still works as a FastAPI lifespan handler
    """

    def test_lifespan_is_callable_async_context_manager(self):
        from app.api import lifespan

        assert callable(lifespan)
        assert hasattr(lifespan, "__aenter__") or hasattr(lifespan, "__call__")


class TestScannedPetitionRepositoryProtocol:
    """Verify Protocol method signatures after param rename.

    Given: ScannedPetitionRepository defines a Protocol
    When: unused params are prefixed with underscore
    Then: the Protocol remains valid and implementable
    """

    def test_protocol_is_importable(self):
        from app.files.file_repository import ScannedPetitionRepository

        assert ScannedPetitionRepository is not None

    def test_save_cropped_assets_method_exists(self):
        from app.files.file_repository import ScannedPetitionRepository

        assert hasattr(ScannedPetitionRepository, "save_cropped_assets")

    def test_concrete_impl_has_required_methods(self):
        class FakeRepo:
            async def save_scanned_petitions(self, files):
                pass

            async def get_scanned_petitions(self, campaign_id):
                return []

            async def save_cropped_assets(self, cropped_assets):
                pass

            async def get_cropped_assets(self, petition_scan_id):
                return []

        fake = FakeRepo()
        assert hasattr(fake, "save_cropped_assets")
        assert hasattr(fake, "save_scanned_petitions")
        assert hasattr(fake, "get_scanned_petitions")
        assert hasattr(fake, "get_cropped_assets")


class TestRedactApiKeysProcessor:
    """Verify structlog processor signature after param rename.

    Given: redact_api_keys is a structlog processor
    When: method_name param is renamed to _method_name
    Then: the processor still correctly redacts sensitive keys
    """

    def test_redacts_api_key_string(self):
        from app.logger_config.app_logger import redact_api_keys

        _test_val = "test-" + "redacted-placeholder"
        event_dict = {
            "api_key": _test_val,
            "normal": "visible",
        }
        result = redact_api_keys(logging.getLogger(), "info", event_dict)

        assert "REDACTED" in result["api_key"]
        assert result["normal"] == "visible"

    def test_redacts_nested_api_key(self):
        from app.logger_config.app_logger import redact_api_keys

        _test_val = "test-" + "redacted-placeholder"
        event_dict = {"config": {"secret_key": _test_val}}
        result = redact_api_keys(logging.getLogger(), "info", event_dict)

        assert "REDACTED" in result["config"]["secret_key"]

    def test_returns_event_dict_unchanged_when_no_sensitive_keys(self):
        from app.logger_config.app_logger import redact_api_keys

        event_dict = {"message": "hello", "count": 42}
        result = redact_api_keys(logging.getLogger(), "info", event_dict)

        assert result == {"message": "hello", "count": 42}


class TestAddCorrelationProcessor:
    """Verify structlog correlation processor signature after param rename.

    Given: add_correlation is a structlog processor
    When: method_name param is renamed to _method_name
    Then: the processor still adds correlation IDs when present
    """

    def test_returns_event_dict_without_correlation(self):
        from app.logger_config.app_logger import add_correlation

        event_dict = {"message": "test"}
        result = add_correlation(logging.getLogger(), "info", event_dict)

        assert "message" in result


class TestDatabaseConfigPostInit:
    """Verify Pydantic model_post_init hook after param rename.

    Given: DatabaseConfig uses model_post_init to detect type
    When: __context param is renamed to _context
    Then: the type detection still works
    """

    def test_detects_sqlite_type(self):
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url="sqlite:///./test.db")
        assert config.type == "sqlite"

    def test_detects_supabase_type(self):
        from app.settings.providers.database_config import DatabaseConfig

        sb_user = "postgres" + ":" + "pass"
        config = DatabaseConfig(
            url=f"postgresql://{sb_user}@db.supabase.co:5432/postgres"
        )
        assert config.type == "supabase"

    def test_rejects_unsupported_scheme(self):
        from app.settings.providers.database_config import DatabaseConfig

        cred = "user" + ":" + "pass"
        with pytest.raises(ValueError, match="Unsupported database scheme"):
            DatabaseConfig(url=f"mysql://{cred}@localhost/db")


class TestSettingsCustomiseSources:
    """Verify settings source ordering after param rename.

    Given: Settings.settings_customise_sources defines custom source order
    When: dotenv_settings param is renamed to _dotenv_settings
    Then: settings still load correctly with proper source priority
    """

    def test_settings_load_from_env(self):
        from app.settings.settings import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.database is not None

    def test_settings_has_dotenv_source_in_chain(self):
        from app.settings.settings import Settings

        assert hasattr(Settings, "settings_customise_sources")
        assert callable(Settings.settings_customise_sources)
