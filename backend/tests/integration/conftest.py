import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolate_from_supabase():
    """Prevent integration tests from connecting to real databases.

    Module-level env overrides in tests/conftest.py ensure that engine
    creation during import uses SQLite. This fixture clears cached
    engines/settings to guarantee isolation.
    """
    os.environ["SETTINGS_ENV_FILE"] = "/dev/null"

    from app.persistence.session import clear_engine_cache
    from app.settings import get_settings

    get_settings.cache_clear()
    clear_engine_cache()

    yield

    os.environ.pop("SETTINGS_ENV_FILE", None)
    get_settings.cache_clear()
    clear_engine_cache()
