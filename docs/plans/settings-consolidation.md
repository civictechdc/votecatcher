# R13: Settings Consolidation

> **Goal:** Merge `AppSettings` (env_settings.py) into `Settings` (settings.py), eliminating the dual settings system.

## Problem

Two pydantic-settings classes with overlapping fields:
- `AppSettings` (`env_settings.py`) — used by routers, worker, api, batch_ocr_manager
- `Settings` (`settings.py`) — used by persistence, supabase, database router

~15 consumer files import from `env_settings`. Feature flags have different names.

## Fields to Add to Settings

| Field | Alias | Default | Source |
|-------|-------|---------|--------|
| `app_name` | APP_NAME | "Votecatcher Backend" | AppSettings |
| `version` | APP_VERSION | "" | AppSettings |
| `clear_runtime_on_launch` | DEV_CLEAR_RUNTIME_ON_LAUNCH | False | AppSettings |
| `demo_reset` | FEATURE_DEMO_RESET | False | AppSettings |
| `always_batch_ocr` | FEATURE_ALWAYS_BATCH_OCR | True | AppSettings |

## Method to Add

- `local_campaign_base_dir()` — from AppSettings, returns `Path`

## Name Mapping (consumer changes)

| AppSettings field | Settings field | Action |
|---|---|---|
| `enable_simulation` | `feature_simulation` | Update consumer |
| `enable_beta_features` | `feature_beta` | Update consumer |
| `enable_debug_mode` | `feature_debug` | Update consumer |
| `demo_mode` | `feature_demo` | Update consumer |
| `ocr_api_key` (str) | `ocr_api_key` (SecretStr) | Consumer calls `.get_secret_value()` |

## Phases

### Phase 1: RED — Write failing tests
Write tests that `Settings` has all fields from `AppSettings`.

### Phase 2: GREEN — Add missing fields
Add 5 fields + `local_campaign_base_dir()` to `Settings`.

### Phase 3: REFACTOR — Migrate consumers
Update imports and field names in each consumer file.

### Phase 4: Remove env_settings.py
Delete `env_settings.py`, update `__init__.py`.

### Phase 5: Exit gate
```bash
cd backend && uv run pytest tests/ -v
cd backend && uv run basedpyright app/
cd backend && uv run ruff check app/
```

## Consumer Files

**App code (5 files):**
1. `app/api.py` — `get_settings` import
2. `app/routers/config_router.py` — `AppSettings`, `get_settings`, field names
3. `app/routers/demo_router.py` — `AppSettings`, `get_settings`, field names
4. `app/jobs/worker.py` — `get_settings`, `AppSettings` (TYPE_CHECKING)
5. `app/ocr/clients/batch_ocr_manager.py` — `AppSettings`, `get_settings`, field names, `local_campaign_base_dir()`

**Test files (3 files):**
6. `tests/test_config.py` — heavy `AppSettings`/`get_settings` usage
7. `tests/unit/jobs/test_batch_threshold.py` — `AppSettings`, `get_settings`
8. `tests/integration/api/test_demo.py` — `get_settings`
