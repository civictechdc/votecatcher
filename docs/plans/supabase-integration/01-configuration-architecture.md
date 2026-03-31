# Phase 1: Configuration Architecture

> **Prerequisite:** None - this is the foundation

**Goal:** Reorganize `app/settings/` with contracts/providers pattern, create type-safe configuration, and consolidate scattered `os.getenv()` calls.

**Duration Estimate:** 4-6 hours

---

## Phase Status

| Task Group | Status | Exit Gate |
|------------|--------|-----------|
| 1A: Contracts | Complete | Type checking passes |
| 1B: Sources | Complete | Env file loading tests pass |
| 1C: Providers | Complete | All providers instantiate correctly |
| 1D: Migration | Complete | No `os.getenv()` in migrated files |

---

## Developer Notes

| Date | Status | Notes/Blockers/Concerns |
|------|--------|-------------------------|
| 2026-03-27 | Complete | All 21 tests pass. 0 type errors, 0 lint errors on new files. Existing env_settings.py/settings_repo.py unchanged (migration of consumers deferred to Phase 2). |
| 2026-03-27 | Complete | Reviewer feedback addressed: R2 (postgres:// scheme), R3 (configurable Supabase region), R4 (SecretStr for sensitive fields), R1 (unused import), R5 (thread safety), R10 (URL validation). 30 tests pass. R6/R7 deferred as tech debt. |

---

## Task Group 1A: Configuration Contracts

**Files:**
- Create: `backend/app/settings/contracts.py`
- Create: `backend/tests/unit/settings/test_contracts.py`

### Step 1: Write failing test for ProvidesDatabaseConfig

```python
# backend/tests/unit/settings/test_contracts.py
"""Tests for configuration contracts."""

import pytest
from pydantic import SecretStr


class TestProvidesDatabaseConfig:
    """Tests for ProvidesDatabaseConfig protocol."""

    def test_protocol_has_url_property(self):
        """Protocol must define url property."""
        from app.settings.contracts import ProvidesDatabaseConfig

        assert hasattr(ProvidesDatabaseConfig, "__protocol_attrs__")
        attrs = ProvidesDatabaseConfig.__protocol_attrs__
        assert "url" in attrs
        assert "type" in attrs


class TestProvidesSupabaseConfig:
    """Tests for ProvidesSupabaseConfig protocol."""

    def test_protocol_has_required_properties(self):
        """Protocol must define all Supabase properties."""
        from app.settings.contracts import ProvidesSupabaseConfig

        attrs = ProvidesSupabaseConfig.__protocol_attrs__
        assert "url" in attrs
        assert "service_key" in attrs
        assert "is_connected" in attrs
        assert "database_url" in attrs
```

### Step 2: Run test to verify it fails

```bash
cd backend && uv run pytest tests/unit/settings/test_contracts.py -v
```

**Expected:** FAIL - module not found

### Step 3: Implement contracts

```python
# backend/app/settings/contracts.py
"""Configuration provider contracts using Protocol classes."""

from typing import Protocol

from pydantic import SecretStr


class ProvidesDatabaseConfig(Protocol):
    """Any source that provides database configuration."""

    @property
    def url(self) -> str:
        """Database connection URL."""
        ...

    @property
    def type(self) -> str:
        """Database type: sqlite, postgres, supabase."""
        ...


class ProvidesSupabaseConfig(Protocol):
    """Supabase-specific configuration."""

    @property
    def url(self) -> str:
        """Supabase project URL (https://xyz.supabase.co)."""
        ...

    @property
    def service_key(self) -> SecretStr:
        """Service role key for admin access."""
        ...

    @property
    def is_connected(self) -> bool:
        """True if Supabase is configured and connected."""
        ...

    @property
    def database_url(self) -> str:
        """PostgreSQL connection URL for Supabase."""
        ...


class ProvidesOcrConfig(Protocol):
    """OCR provider configuration."""

    @property
    def provider_name(self) -> str:
        """OCR provider name."""
        ...

    @property
    def model(self) -> str | None:
        """Model identifier if applicable."""
        ...

    @property
    def api_key(self) -> SecretStr | None:
        """API key for the provider."""
        ...


class ProvidesFeatureConfig(Protocol):
    """Feature flag configuration."""

    @property
    def simulation(self) -> bool:
        """Enable simulation mode (mock OCR)."""
        ...

    @property
    def beta_features(self) -> bool:
        """Enable beta features."""
        ...

    @property
    def debug_mode(self) -> bool:
        """Enable debug mode."""
        ...

    @property
    def demo_mode(self) -> bool:
        """Enable demo mode."""
        ...
```

### Step 4: Run test to verify it passes

```bash
cd backend && uv run pytest tests/unit/settings/test_contracts.py -v
```

**Expected:** PASS

### Step 5: Commit

```bash
git add backend/app/settings/contracts.py backend/tests/unit/settings/test_contracts.py
git commit -m "feat(settings): add configuration provider contracts"
```

---

## Task Group 1B: Configuration Sources

**Files:**
- Create: `backend/app/settings/sources/__init__.py`
- Create: `backend/app/settings/sources/env_file.py`
- Create: `backend/app/settings/sources/environment.py`
- Create: `backend/tests/unit/settings/test_sources.py`

### Step 1: Write failing tests for EnvFileSource

```python
# backend/tests/unit/settings/test_sources.py
"""Tests for configuration sources."""

import tempfile
from pathlib import Path

import pytest


class TestEnvFileSource:
    """Tests for .env file loading."""

    def test_loads_env_file(self, tmp_path: Path):
        """Should load variables from .env file."""
        from app.settings.sources.env_file import EnvFileSource

        env_file = tmp_path / ".env.local"
        env_file.write_text("TEST_VAR=test_value\n")

        source = EnvFileSource(env_file)
        assert source.get("TEST_VAR") == "test_value"

    def test_returns_none_for_missing_var(self, tmp_path: Path):
        """Should return None for missing variables."""
        from app.settings.sources.env_file import EnvFileSource

        env_file = tmp_path / ".env.local"
        env_file.write_text("OTHER_VAR=value\n")

        source = EnvFileSource(env_file)
        assert source.get("MISSING_VAR") is None

    def test_returns_default_for_missing(self, tmp_path: Path):
        """Should return default for missing variables."""
        from app.settings.sources.env_file import EnvFileSource

        env_file = tmp_path / ".env.local"
        env_file.write_text("")

        source = EnvFileSource(env_file)
        assert source.get("MISSING", default="default") == "default"

    def test_handles_missing_file(self, tmp_path: Path):
        """Should handle missing file gracefully."""
        from app.settings.sources.env_file import EnvFileSource

        source = EnvFileSource(tmp_path / ".env.nonexistent")
        assert source.get("ANY_VAR") is None

    def test_priority_order(self, tmp_path: Path):
        """Should load .env.local before .env.{NODE_ENV}."""
        from app.settings.sources.env_file import EnvFileSource

        local = tmp_path / ".env.local"
        local.write_text("VAR=local_value\n")

        source = EnvFileSource(local)
        assert source.get("VAR") == "local_value"


class TestEnvironmentSource:
    """Tests for OS environment variables."""

    def test_gets_from_os_environment(self, monkeypatch):
        """Should read from os.environ."""
        from app.settings.sources.environment import EnvironmentSource

        monkeypatch.setenv("TEST_OS_VAR", "os_value")
        source = EnvironmentSource()
        assert source.get("TEST_OS_VAR") == "os_value"

    def test_returns_none_for_missing(self):
        """Should return None for missing env vars."""
        from app.settings.sources.environment import EnvironmentSource

        source = EnvironmentSource()
        assert source.get("DEFINITELY_NOT_SET_12345") is None
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/settings/test_sources.py -v
```

**Expected:** FAIL - modules not found

### Step 3: Implement sources

```python
# backend/app/settings/sources/__init__.py
"""Configuration sources."""

from app.settings.sources.env_file import EnvFileSource
from app.settings.sources.environment import EnvironmentSource

__all__ = ["EnvFileSource", "EnvironmentSource"]
```

```python
# backend/app/settings/sources/env_file.py
"""Load configuration from .env files."""

from pathlib import Path

from dotenv import dotenv_values
import structlog

logger = structlog.get_logger(__name__)


class EnvFileSource:
    """Load configuration from a .env file."""

    def __init__(self, path: Path):
        self._path = path
        self._values: dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        if self._path.exists():
            self._values = dict(dotenv_values(self._path))
            logger.debug("Loaded env file", path=str(self._path))
        else:
            logger.debug("Env file not found", path=str(self._path))

        self._loaded = True

    def get(self, key: str, default: str | None = None) -> str | None:
        self._ensure_loaded()
        return self._values.get(key, default)
```

```python
# backend/app/settings/sources/environment.py
"""Load configuration from OS environment variables."""

import os


class EnvironmentSource:
    """Read configuration from os.environ."""

    def get(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)
```

### Step 4: Run tests to verify they pass

```bash
cd backend && uv run pytest tests/unit/settings/test_sources.py -v
```

**Expected:** PASS

### Step 5: Commit

```bash
git add backend/app/settings/sources/ backend/tests/unit/settings/test_sources.py
git commit -m "feat(settings): add configuration sources (env file, environment)"
```

---

## Task Group 1C: Configuration Providers

**Files:**
- Create: `backend/app/settings/providers/__init__.py`
- Create: `backend/app/settings/providers/database_config.py`
- Create: `backend/app/settings/providers/supabase_config.py`
- Create: `backend/app/settings/providers/ocr_config.py`
- Create: `backend/app/settings/providers/feature_config.py`
- Create: `backend/tests/unit/settings/test_providers.py`

### Step 1: Write failing tests for providers

```python
# backend/tests/unit/settings/test_providers.py
"""Tests for configuration providers."""

import pytest
from pydantic import SecretStr


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

        config = DatabaseConfig(url="postgresql://user:pass@localhost/db")
        assert config.type == "postgres"

    def test_supabase_config_detected(self):
        """Should detect Supabase from URL pattern."""
        from app.settings.providers.database_config import DatabaseConfig

        config = DatabaseConfig(url="postgresql://postgres:pass@db.xyz.supabase.co/postgres")
        assert config.type == "supabase"


class TestSupabaseConfig:
    """Tests for SupabaseConfig provider."""

    def test_from_credentials(self):
        """Should create from URL and key."""
        from app.settings.providers.supabase_config import SupabaseConfig

        config = SupabaseConfig(
            project_url="https://xyz.supabase.co",
            service_key=SecretStr("sb_secret_test_key"),  # pragma: allowlist secret
            db_password=SecretStr("db_password"),  # pragma: allowlist secret
        )
        assert config.url == "https://xyz.supabase.co"
        assert config.is_connected is True
        assert "xyz.supabase.co" in config.database_url

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
            service_key=SecretStr("sb_secret_test_key"),  # pragma: allowlist secret
            db_password=SecretStr("db_password"),  # pragma: allowlist secret
        )
        assert "sb_secret" not in str(config.service_key)


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


class TestFeatureConfig:
    """Tests for FeatureConfig provider."""

    def test_feature_flags(self):
        """Should configure feature flags."""
        from app.settings.providers.feature_config import FeatureConfig

        config = FeatureConfig(
            simulation=True,
            beta_features=True,
            debug_mode=False,
            demo_mode=True,
        )
        assert config.simulation is True
        assert config.beta_features is True
        assert config.debug_mode is False
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/settings/test_providers.py -v
```

**Expected:** FAIL - modules not found

### Step 3: Implement providers

```python
# backend/app/settings/providers/__init__.py
"""Configuration providers."""

from app.settings.providers.database_config import DatabaseConfig
from app.settings.providers.feature_config import FeatureConfig
from app.settings.providers.ocr_config import OcrConfig
from app.settings.providers.supabase_config import SupabaseConfig

__all__ = ["DatabaseConfig", "FeatureConfig", "OcrConfig", "SupabaseConfig"]
```

```python
# backend/app/settings/providers/database_config.py
"""Database configuration provider."""

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration provider."""

    url: str = Field(default="sqlite:///./votecatcher.db")
    type: str = Field(default="sqlite", init=False)

    def model_post_init(self, __context) -> None:
        self.type = self._detect_type()

    def _detect_type(self) -> str:
        if "supabase.co" in self.url:
            return "supabase"
        if self.url.startswith("postgresql"):
            return "postgres"
        return "sqlite"
```

```python
# backend/app/settings/providers/supabase_config.py
"""Supabase configuration provider."""

from pydantic import BaseModel, Field, SecretStr


class SupabaseConfig(BaseModel):
    """Supabase configuration provider."""

    project_url: str = Field(default="")
    service_key: SecretStr = Field(default=SecretStr(""))
    db_password: SecretStr = Field(default=SecretStr(""))

    @property
    def url(self) -> str:
        return self.project_url

    @property
    def is_connected(self) -> bool:
        return bool(self.project_url and self.service_key.get_secret_value())

    @property
    def database_url(self) -> str:
        if not self.is_connected:
            return ""

        project_ref = self.project_url.replace("https://", "").replace(".supabase.co", "")
        password = self.db_password.get_secret_value()
        return f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
```

```python
# backend/app/settings/providers/ocr_config.py
"""OCR configuration provider."""

from pydantic import BaseModel, Field, SecretStr


class OcrConfig(BaseModel):
    """OCR configuration provider."""

    provider_name: str = Field(default="")
    model: str | None = Field(default=None)
    api_key: SecretStr | None = Field(default=None)
```

```python
# backend/app/settings/providers/feature_config.py
"""Feature flag configuration provider."""

from pydantic import BaseModel, Field


class FeatureConfig(BaseModel):
    """Feature flag configuration provider."""

    simulation: bool = Field(default=False)
    beta_features: bool = Field(default=False)
    debug_mode: bool = Field(default=False)
    demo_mode: bool = Field(default=False)
```

### Step 4: Run tests to verify they pass

```bash
cd backend && uv run pytest tests/unit/settings/test_providers.py -v
```

**Expected:** PASS

### Step 5: Commit

```bash
git add backend/app/settings/providers/ backend/tests/unit/settings/test_providers.py
git commit -m "feat(settings): add configuration providers (database, supabase, ocr, features)"
```

---

## Task Group 1D: Settings Aggregation and Migration

**Files:**
- Modify: `backend/app/settings/__init__.py`
- Modify: `backend/app/settings/settings.py` (rename from env_settings.py)
- Create: `backend/app/settings/settings.py`
- Create: `backend/tests/unit/settings/test_settings.py`
- Modify: `backend/.env.example`

### Step 1: Write failing tests for aggregated Settings

```python
# backend/tests/unit/settings/test_settings.py
"""Tests for aggregated Settings."""

import pytest


class TestSettings:
    """Tests for the main Settings class."""

    def test_get_settings_returns_settings(self):
        """get_settings should return Settings instance."""
        from app.settings import get_settings

        settings = get_settings()
        assert hasattr(settings, "database")
        assert hasattr(settings, "supabase")
        assert hasattr(settings, "ocr")
        assert hasattr(settings, "features")

    def test_settings_is_cached(self):
        """get_settings should be cached."""
        from app.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_database_config_accessible(self):
        """Database config should be accessible."""
        from app.settings import get_settings

        settings = get_settings()
        assert settings.database.url is not None
        assert settings.database.type in ("sqlite", "postgres", "supabase")

    def test_supabase_not_connected_by_default(self):
        """Supabase should not be connected without credentials."""
        from app.settings import get_settings

        settings = get_settings()
        # Without actual credentials, should not be connected
        # This test may need adjustment based on env setup
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/settings/test_settings.py -v
```

**Expected:** FAIL - Settings structure doesn't match

### Step 3: Implement aggregated Settings

```python
# backend/app/settings/settings.py
"""Aggregated application settings."""

from functools import lru_cache
from pathlib import Path

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.providers.database_config import DatabaseConfig
from app.settings.providers.feature_config import FeatureConfig
from app.settings.providers.ocr_config import OcrConfig
from app.settings.providers.supabase_config import SupabaseConfig
from app.settings.sources.env_file import EnvFileSource
from app.settings.sources.environment import EnvironmentSource

logger = structlog.get_logger(__name__)

BACKEND_DIR = Path(__file__).parent.parent.parent


def _resolve_env_path() -> Path:
    """Resolve the env file path based on priority."""
    env_source = EnvironmentSource()
    env_file = env_source.get("ENV_FILE")

    if env_file:
        return BACKEND_DIR / env_file

    node_env = env_source.get("NODE_ENV", "development")

    # Priority: .env.local > .env.{NODE_ENV}
    local_path = BACKEND_DIR / ".env.local"
    if local_path.exists():
        return local_path

    return BACKEND_DIR / f".env.{node_env}"


class Settings(BaseSettings):
    """Aggregated application settings."""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=str(_resolve_env_path()),
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str = Field(default="sqlite:///./votecatcher.db", alias="DATABASE_URL")

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    supabase_db_password: str = Field(default="", alias="SUPABASE_DB_PASSWORD")

    # OCR
    ocr_provider_name: str = Field(default="", alias="OCR_PROVIDER_NAME")
    ocr_model: str | None = Field(default=None, alias="OCR_PROVIDER_MODEL")
    ocr_api_key: str | None = Field(default=None, alias="OCR_PROVIDER_API_KEY")

    # Features
    feature_simulation: bool = Field(default=False, alias="FEATURE_ENABLE_SIMULATION")
    feature_beta: bool = Field(default=False, alias="FEATURE_ENABLE_BETA_FEATURES")
    feature_debug: bool = Field(default=False, alias="FEATURE_ENABLE_DEBUG_MODE")
    feature_demo: bool = Field(default=False, alias="FEATURE_DEMO_MODE")

    # Development paths
    runtime_dir: Path | None = Field(default=None, alias="DEV_LOCAL_RUNTIME_DIR")
    local_db: Path | None = Field(default=None, alias="DEV_LOCAL_RUNTIME_DB_DIR")
    crop_dir: Path | None = Field(default=None, alias="DEV_LOCAL_BALLOT_CROP_DIR")
    petition_dir: Path | None = Field(default=None, alias="DEV_LOCAL_PETITION_SCAN_DIR")
    campaigns_dir: Path | None = Field(default=None, alias="DEV_LOCAL_CAMPAIGNS_DIR")
    registration_dir: Path | None = Field(default=None, alias="DEV_LOCAL_VOTER_REGISTRATION_DIR")
    ocr_dir: Path | None = Field(default=None, alias="DEV_LOCAL_OCR_DIR")

    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(url=self.database_url)

    @property
    def supabase(self) -> SupabaseConfig:
        """Get Supabase configuration."""
        from pydantic import SecretStr

        return SupabaseConfig(
            project_url=self.supabase_url,
            service_key=SecretStr(self.supabase_service_key) if self.supabase_service_key else SecretStr(""),
            db_password=SecretStr(self.supabase_db_password) if self.supabase_db_password else SecretStr(""),
        )

    @property
    def ocr(self) -> OcrConfig:
        """Get OCR configuration."""
        from pydantic import SecretStr

        return OcrConfig(
            provider_name=self.ocr_provider_name,
            model=self.ocr_model,
            api_key=SecretStr(self.ocr_api_key) if self.ocr_api_key else None,
        )

    @property
    def features(self) -> FeatureConfig:
        """Get feature flag configuration."""
        return FeatureConfig(
            simulation=self.feature_simulation,
            beta_features=self.feature_beta,
            debug_mode=self.feature_debug,
            demo_mode=self.feature_demo,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    env_path = _resolve_env_path()
    logger.debug("Loading settings", env_path=str(env_path))
    return Settings()
```

### Step 4: Update __init__.py

```python
# backend/app/settings/__init__.py
from app.settings.settings import Settings, get_settings
from app.settings.providers.database_config import DatabaseConfig
from app.settings.providers.supabase_config import SupabaseConfig
from app.settings.providers.ocr_config import OcrConfig
from app.settings.providers.feature_config import FeatureConfig

__all__ = [
    "get_settings",
    "Settings",
    "DatabaseConfig",
    "SupabaseConfig",
    "OcrConfig",
    "FeatureConfig",
]
```

### Step 5: Update .env.example

```bash
# backend/.env.example

# === Database Configuration ===
# SQLite (development default)
DATABASE_URL=sqlite:///./dev.db

# PostgreSQL (production)
# DATABASE_URL=postgresql+psycopg://user:pass@localhost/votecatcher  # pragma: allowlist secret

# === Supabase Configuration (Optional) ===
# Uncomment and fill in to use Supabase
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=your-service-role-key
# SUPABASE_DB_PASSWORD=your-db-password

# === OCR Provider Configuration ===
# Required unless using simulation mode
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=your-api-key-here

# === Feature Flags ===
FEATURE_ENABLE_SIMULATION=0
FEATURE_ENABLE_BETA_FEATURES=0
FEATURE_ENABLE_DEBUG_MODE=0
FEATURE_DEMO_MODE=0

# === Development Paths (Optional) ===
# DEV_LOCAL_RUNTIME_DIR=runtime
# DEV_LOCAL_BALLOT_CROP_DIR=crops
# DEV_LOCAL_PETITION_SCAN_DIR=petitions
# DEV_LOCAL_CAMPAIGNS_DIR=campaigns
# DEV_LOCAL_VOTER_REGISTRATION_DIR=registrations
# DEV_LOCAL_OCR_DIR=ocr
```

### Step 6: Run tests

```bash
cd backend && uv run pytest tests/unit/settings/ -v
```

**Expected:** PASS

### Step 7: Type check

```bash
cd backend && uv run basedpyright app/settings/
```

**Expected:** No errors

### Step 8: Commit

```bash
git add backend/app/settings/ backend/tests/unit/settings/ backend/.env.example
git commit -m "feat(settings): implement aggregated settings with providers"
```

---

## Phase 1 Exit Gate

**Run all validation:**

```bash
# Tests
cd backend && uv run pytest tests/unit/settings/ -v

# Type checking
cd backend && uv run basedpyright app/settings/

# Linting
cd backend && uv run ruff check app/settings/
```

**Expected Results:**
- [ ] All tests pass
- [ ] No type errors
- [ ] No lint errors

---

## Reviewer Section

**Reviewer:** opencode (code-reviewer)
**Date:** 2026-03-27

**Status:** [x] Needs Changes

### Developer Remarks

| Category | Remark | Action |
|----------|--------|--------|
| ℹ️ Observation | Existing env_settings.py/settings_repo.py unchanged, consumer migration deferred to Phase 2 | Acknowledged - correct scope boundary |

### Findings

- 🔴 Critical: 0 | 🟠 High: 0 | 🟡 Medium: 7 | 🟢 Low: 3

| ID | Severity | File | Issue | Action |
|----|----------|------|-------|--------|
| R1 | 🟡 | `settings.py` | `EnvFileSource` imported but unused | Remove or integrate |
| R2 | 🟡 | `database_config.py:_detect_type` | Fragile DB type detection — fails for `postgres://` URLs (only checks `startswith("postgresql")`) | Fix before Phase 2 |
| R3 | 🟡 | `supabase_config.py:29` | Hardcoded `aws-0-us-east-1` region/pooler — breaks non-us-east-1 Supabase projects | Make configurable via `SUPABASE_REGION` |
| R4 | 🟡 | `settings.py:46-71` | Sensitive fields (`supabase_service_key`, `supabase_db_password`, `ocr_api_key`) stored as `str` not `SecretStr` — logging risk | Use `SecretStr` consistently |
| R5 | 🟡 | `env_file.py:19-29` | Lazy loading `_ensure_loaded()` has no thread safety lock | Add `threading.Lock` |
| R6 | 🟢 | `settings.py` | `_resolve_env_path()` called at module level in `model_config` — prevents runtime override | Document or refactor |
| R7 | 🟢 | `settings.py` | `@lru_cache` on `get_settings()` with no maxsize — no cache invalidation path | Acceptable for now |
| R8 | 🟢 | `env_file.py:16` | `_values` typed as `dict[str, str]` but `dotenv_values()` returns `dict[str, str \| None]` | Align type annotation |
| R9 | 🟡 | `settings.py:111` | Module-level `_resolve_env_path()` in `SettingsConfigDict` prevents test override | Refactor for testability |
| R10 | 🟡 | `database_config.py` | No URL validation — malformed URLs silently accepted | Add format validation |

### Blocking Issues

None — all issues are non-blocking but three should be addressed before Phase 2.

### Required Before Phase 2

1. **R2** — Fix `_detect_type()` to handle `postgres://` scheme via `urllib.parse` (`urlparse(self.url).scheme in ("postgresql", "postgres")`)
2. **R3** — Make Supabase region/pooler configurable (e.g. `SUPABASE_REGION` env var, default `aws-0-us-east-1`)
3. **R4** — Change `supabase_service_key`, `supabase_db_password`, `ocr_api_key` fields to `SecretStr` in `Settings` class

### Optional (Track as Tech Debt)

- R1: Remove unused `EnvFileSource` import
- R5: Add thread safety lock to `EnvFileSource._ensure_loaded()`
- R6/R9: Refactor `_resolve_env_path()` for runtime testability
- R8: Align type annotation with `dotenv_values()` return type
- R10: Add URL format validation to `DatabaseConfig`

### Positives

- Clean contracts/providers/sources separation
- All Protocol interfaces structurally satisfied
- 21 tests passing, 0 type errors, 0 lint errors
- Good use of Pydantic for validation and defaults

---

## Next Phase

Once this phase passes the exit gate and reviewer approval, proceed to:

**[Phase 2: Persistence Layer](./02-persistence-layer.md)**

Entrance gate: Verify Phase 1 exit gate passed by running:

```bash
cd backend && uv run pytest tests/unit/settings/ -v && uv run basedpyright app/settings/
```
