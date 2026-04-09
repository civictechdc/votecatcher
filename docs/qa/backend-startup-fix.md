# Backend Startup Fix — Session Log

**Date:** 2025-04-09
**Status:** In progress (Session 6)
**Test Results (Session 1):** 478 passed, 18 pre-existing failures, 144 pre-existing errors
**Test Results (Session 2):** 521 passed, 2 failures, 0 errors
**Test Results (Session 3):** 640 passed, 0 failures, 0 errors
**Test Results (Session 5):** 624 passed, 29 failures (integration tests need camelCase key updates), 0 errors
**Test Results (Session 6):** 653 passed, 0 failures, 0 errors

## Problem

Backend (`main.py`) failed with `Error loading ASGI app. Could not import module "app.api"`. The FastAPI entry point file `app/api.py` had been deleted in a prior refactor but `main.py` still referenced it via `app="app.api:app"`.

After creating `app/api.py`, a cascade of deeper import errors surfaced.

## Root Causes Found

### 1. Missing `app/api.py` (deleted in refactor)

`main.py:59` references `app="app.api:app"` but the file was removed during the settings/OCR refactor (commit `cd8cf5f`).

**Fix:** Created `app/api.py` — FastAPI entry point wiring all 9 routers, CORS middleware, `/health` endpoint, and lifespan event.

### 2. `app/settings/__init__.py` importing from deleted module

Was importing `OpenAiConfig`, `MistralAiConfig`, `GeminiAiConfig`, `load_settings` from `settings_repo` (deleted in refactor).

**Fix:** Updated to export `Settings` and `get_settings` from current `settings.py`.

### 3. `app/dependencies.py` — module-level `engine` import triggered env override

The import chain:
1. `dependencies.py:12` → `from app.data.database.session import engine`
2. → `app/data/__init__.py` → `from .database_client import DbClient`
3. → `database_client.py:14` → `load_dotenv()` loads `.env` into `os.environ`
4. `.env` contains `DATABASE_URL=postgresql+psycopg://...` (postgres)
5. This overrides `.env.local`'s `DATABASE_URL=sqlite:///./dev.db`
6. `SqliteEngine.__init__` gets postgres URL → tries to load `psycopg` → fails

Additionally:
- `load_dotenv()` at module level is a side effect
- `refreshUrl=""` is an invalid kwarg for current FastAPI's `OAuth2PasswordBearer`

**Fix:**
- Removed `from app.data.database.session import engine` (module-level)
- Removed `load_dotenv()` call
- Fixed `OAuth2PasswordBearer` — removed `refreshUrl`
- Replaced with lazy `get_db_session` import and `get_engine_dependency()` function

### 4. Bare `load_dotenv()` in 4 files — wrong env priority

All called bare `load_dotenv()` which loads `.env` by default, bypassing the Settings system's priority: `ENV_FILE → .env.dev/.env.local → .env.{NODE_ENV}`. The bare `.env` file contains a postgres URL that overrides the sqlite URL in `.env.local`.

**Files affected:**
- `app/data/database_client.py`
- `app/common/data/supabase_client.py`
- `app/matching/fuzzy_match_helper.py`
- `app/ocr/ocr_helper.py`

**Fix:**
- Created `app/settings/env_loader.py` — shared loader with correct priority (SETTINGS_ENV_FILE → ENV_FILE → .env.local → .env.{NODE_ENV})
- Replaced bare `load_dotenv()` with `load_env()` in `database_client.py` and `supabase_client.py`
- Removed `load_dotenv()` entirely from `fuzzy_match_helper.py` and `ocr_helper.py` (Settings handles it)

### 5. `app/ocr/ocr_client_factory.py` — missing symbols after refactor

`ProviderConfig`, `resolve_provider_config`, `TEXT_PROMPTS`, and per-provider extractors (`_extract_openai`, `_extract_gemini`, `_extract_mistral`) were deleted in the refactor but still imported by:
- `app/ocr/clients/open_ai.py`
- `app/ocr/clients/mistral.py`
- `app/ocr/clients/gemini.py`
- `app/ocr/ocr_manager.py`
- Multiple test files

**Fix:** Restored all symbols. Updated `resolve_provider_config` to use `get_settings().ocr` as fallback instead of deleted `load_settings().selected_config`.

### 6. Missing dependencies in `pyproject.toml`

Several runtime dependencies were used but not declared:
- `sqlmodel`, `pydantic-settings`, `postgrest`, `supabase`, `psycopg2-binary`, `pdf2image`, `aiofiles`

Dev dependency missing: `pytest-asyncio`

Also fixed: `requires-python = "~=3.12"` → `">=3.12,<4"` (tilde without patch version is ambiguous).

## Files Changed

| File | Change |
|------|--------|
| `app/api.py` | **Created** — FastAPI app entry point |
| `app/settings/__init__.py` | Updated exports from deleted `settings_repo` to `settings.py` |
| `app/settings/env_loader.py` | **Created** — shared env loader with correct priority |
| `app/dependencies.py` | Removed module-level engine import, `load_dotenv`, fixed `OAuth2PasswordBearer` |
| `app/data/database_client.py` | Replaced `load_dotenv()` with `load_env()` |
| `app/common/data/supabase_client.py` | Replaced `load_dotenv()` with `load_env()` |
| `app/matching/fuzzy_match_helper.py` | Removed `load_dotenv()` |
| `app/ocr/ocr_helper.py` | Removed `load_dotenv()` |
| `app/ocr/ocr_client_factory.py` | Restored `ProviderConfig`, `TEXT_PROMPTS`, extractors; updated to use `get_settings()` |
| `pyproject.toml` | Added missing deps, fixed `requires-python` |

## Tests Added

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `tests/unit/api/test_api.py` | 6 | Validates FastAPI app creation, routers, CORS, health endpoint |
| `tests/unit/api/test_dependencies_import_safety.py` | 3 | Ensures no module-level `load_dotenv` or engine import in dependencies |
| `tests/unit/ocr/test_ocr_client_factory_imports.py` | 3 | Validates ocr_client_factory uses current settings API |
| `tests/unit/settings/test_load_dotenv_safety.py` | 4 | Ensures no bare `load_dotenv()` in 4 files |
| `tests/unit/settings/test_env_loader.py` | 3 | Validates env file priority logic |

## Remaining Pre-existing Issues (from Session 1)

These were present before Session 1 and are not caused by the changes above:

1. ~~**Missing `asgi_correlation_id` dependency** — causes `test_commit7_delete_batching` failures~~ **Fixed in Session 2**
2. ~~**SQLAlchemy FK error** — `matcher_jobs.started_by` references missing `users` table; blocks integration tests~~ **Fixed in Session 2** (autouse model import fixture)
3. ~~**`pytest-asyncio` mode** — many async tests use `@pytest.mark.asyncio` but need strict mode config~~ **Fixed in Session 2**
4. ~~**OCR client factory tests** — some tests reference slightly different API patterns than restored code~~ **Fixed in Session 2**
5. **Repository tests** — `test_repositories.py` has fixture/DB setup issues (passes as of Session 2)
6. ~~**Metrics service tests** — `test_metrics_service.py` errors (likely DB setup)~~ **Fixed in Session 2**

## Session 2 (2026-04-09) — Test Suite Recovery

### Starting State

478 passed, 18 failed, 144 errors. Root causes: missing deps, FK registration gaps, stale test patches, production bug in mistralai import.

### Fixes Applied

#### 7. Missing runtime dependencies (round 2)

`asgi-correlation-id`, `alembic`, `mistralai`, `aiofiles` were all used in production code but not declared in `pyproject.toml`.

**Fix:** Added to `dependencies` list:
- `aiofiles>=24.1.0` — used by `app/ocr/clients/open_ai.py`
- `alembic>=1.14.0` — used by `app/persistence/` engines
- `asgi-correlation-id>=4.3.4` — used by `app/logger_config/app_logger.py`
- `mistralai>=1.0.0` — used by `app/ocr/ocr_client_factory.py` and `app/ocr/clients/mistral.py`

#### 8. `pytest-asyncio` mode not configured

Async tests using `@pytest.mark.asyncio` caused deprecation warnings and inconsistent behavior.

**Fix:** Added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml`.

#### 9. Production bug: mistralai v2 breaking import change

`mistralai` SDK v2 moved `Mistral` class from `mistralai.Mistral` to `mistralai.client.Mistral`. Both production files used the old import path, which would fail at runtime.

**Fix:** Updated imports:
- `app/ocr/ocr_client_factory.py:226`: `from mistralai import Mistral` → `from mistralai.client import Mistral`
- `app/ocr/clients/mistral.py:44`: `from mistralai import Mistral` → `from mistralai.client import Mistral`

#### 10. OCR client factory tests — stale settings cache + wrong mock paths

Tests in `test_ocr_client_factory.py` used `patch.dict(os.environ)` but `get_settings()` is `@lru_cache`'d and reads from `.env.local`, ignoring the patched env vars. Extractor tests patched wrong module paths (`app.ocr.ocr_client_factory.AsyncOpenAI` for a local import, `mistralai.Mistral` for v1 API).

**Fix (test file `tests/unit/ocr/test_ocr_client_factory.py`):**
- Added `_clear_settings_cache` autouse fixture calling `get_settings.cache_clear()` before/after each test
- Fixed OpenAI mock path: `patch("openai.AsyncOpenAI")` (local import)
- Fixed Mistral mock path: `patch("mistralai.client.Mistral")` (v2 API)

All 19 tests in this file now pass.

#### 11. FK table registration — `SQLModel.metadata.create_all()` failures

~120 test errors across metrics, OCR service, integration API, security, and SSE transport tests. All had the same root cause: test fixtures called `SQLModel.metadata.create_all(engine)` after importing only a subset of models. Transitive imports registered tables with FK constraints pointing to tables that were never imported (e.g. `MatcherJob` has FK to `users`, `RegisteredVoter` has FK to `voter_list_uploads`, `LegacyOcrJob` has FK to `matching_tasks`).

**Fix:** Added `ensure_all_models_registered()` function and session-scoped autouse fixture to root `tests/conftest.py`. Imports all 15 model modules (including legacy/demo models) so every table is registered before any test runs. No individual test file changes needed.

Affected files (fixed via autouse fixture):
- `tests/unit/services/test_metrics_service.py` — was `NoReferencedTableError: users`
- `tests/unit/services/test_ocr_service.py` — was `NoReferencedTableError: voter_list_uploads`
- `tests/integration/api/conftest.py` — was `NoReferencedTableError: users`
- `tests/integration/services/conftest.py` — was `NoReferencedTableError: users`
- `tests/security/conftest.py` — was `NoReferencedTableError: users`
- `tests/unit/demo/conftest.py` — was `NoReferencedTableError: voter_list_uploads`
- `tests/unit/events/transports/test_sse_transport.py` — was `NoReferencedTableError: users`
- `tests/unit/repositories/test_campaign_repository.py` — was `NoReferencedTableError: users`

#### 12. Stale test patches for `app.api.init_db` and `app.api.job_worker`

Integration API and security conftest files patched `app.api.init_db` and `app.api.job_worker.start_worker/stop_worker`, but the new `app/api.py` (created in Session 1) doesn't import these symbols. `patch()` raised `AttributeError`.

**Fix:**
- `tests/integration/api/conftest.py`: Removed `patch("app.api.init_db")` from client fixture
- `tests/security/conftest.py`: Removed all three patches (`init_db`, `start_worker`, `stop_worker`)

### Session 2 Files Changed

| File | Change |
|------|--------|
| `pyproject.toml` | Added `aiofiles`, `alembic`, `asgi-correlation-id`, `mistralai` deps; added `asyncio_mode = "auto"` |
| `app/ocr/ocr_client_factory.py` | Fixed `from mistralai import Mistral` → `from mistralai.client import Mistral` |
| `app/ocr/clients/mistral.py` | Fixed `from mistralai import Mistral` → `from mistralai.client import Mistral` |
| `tests/conftest.py` | Added `ensure_all_models_registered()` + session-scoped autouse fixture |
| `tests/unit/ocr/test_ocr_client_factory.py` | Added `_clear_settings_cache` fixture; fixed mock paths for OpenAI/Mistral |
| `tests/integration/api/conftest.py` | Removed stale `patch("app.api.init_db")` |
| `tests/security/conftest.py` | Removed stale patches for `init_db`, `job_worker` |

### Remaining Issues (2 failures)

1. ~~**`tests/integration/api/test_error_handling.py`** (2 tests) — CORS header tests (`test_404_error_includes_cors_headers`, `test_422_validation_error_includes_cors_headers`) send requests without an `Origin` header. FastAPI's CORSMiddleware only adds `access-control-allow-origin` when the request includes a matching `Origin`. Fix: add `headers={"Origin": "http://localhost"}` to the test requests.~~ **Fixed in Session 3**

### Recommendations (updated)

1. ~~**Rename `backend/.env` to `backend/.env.example`** — it contains a postgres URL that conflicts with `.env.local`. The env_loader handles priority correctly, but the file is confusing.~~ **Fixed in Session 3** (removed `.env`; `.env.example` already exists)
2. ~~**Fix 2 CORS tests** — add `Origin` header to test requests (trivial one-line fix).~~ **Fixed in Session 3**
3. **Consider removing `dotenv` dependency** — the Settings system + env_loader handles all env loading. The `dotenv` package is no longer directly needed.

## Session 3 (2026-04-09) — Final Fixes

### Fixes Applied

#### 13. CORS tests missing `Origin` header

`test_404_error_includes_cors_headers` and `test_422_validation_error_includes_cors_headers` sent requests without an `Origin` header. CORSMiddleware only adds `access-control-allow-origin` when a matching `Origin` is present.

**Fix:** Added `headers={"Origin": "http://localhost"}` to both test requests.

#### 14. Removed `backend/.env` (postgres URL conflicting with `.env.local`)

`backend/.env` contained only `DATABASE_URL=postgresql+psycopg://...` which would override `.env.local`'s sqlite URL when loaded with bare `load_dotenv()`. The env_loader priority system handles this correctly, but the file was a footgun. `.env.example` already exists as the proper template.

**Fix:** Deleted `backend/.env`.

### Session 3 Files Changed

| File | Change |
|------|--------|
| `tests/integration/api/test_error_handling.py` | Added `Origin` header to CORS test requests |
| `backend/.env` | **Deleted** — postgres URL conflicting with `.env.local` |

## Session 4 (2026-04-09) — API camelCase Serialization + Process Management

### Problem

Backend API responses used `snake_case` field names (`campaign_id`, `job_id`) but the frontend generated types expected `camelCase` (`campaignId`, `jobId`). This caused the jobs page to show no data — the `campaignId` filter compared `undefined` against the campaign ID, matching nothing.

Results page appeared to work because it accessed raw JSON fields directly (`result.predictions`, `result.extracted_name`) rather than filtering on camelCase properties.

### Fix

#### 15. Created `ApiModel` base class (`app/api_models.py`)

Pydantic `alias_generator` that converts `snake_case` Python fields to `camelCase` JSON. Uses `populate_by_name=True` so request deserialization accepts both formats.

```python
class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )
```

Python code stays snake_case internally. API output transforms automatically.

#### 16. Updated all router models to use `ApiModel`

Replaced `BaseModel` with `ApiModel` on all API-facing schemas across 7 router files:

| Router | Models Updated |
|--------|---------------|
| `job_router.py` | `CreateJobRequest`, `JobResponse`, `JobListResponse` |
| `campaign_router.py` | `CampaignResponse`, `CampaignListResponse`, `CampaignMetricsResponse`, `PetitionScanResponse`, `PetitionScanListResponse`, `CampaignMatchPrediction`, `CampaignResultResponse`, `CampaignResultsListResponse`, `SetupStatusResponse` |
| `results_router.py` | `MatchPrediction`, `ResultResponse`, `ResultsListResponse` |
| `session_router.py` | `CreateSessionRequest`, `SessionResponse`, `SessionListResponse` |
| `upload_router.py` | `VoterListUploadResponse`, `PetitionUploadResponse` |
| `config_router.py` | `FeatureFlagsResponse` (converted from manual camelCase fields to snake_case + alias), `SettingsResponse`, `ResetDataResponse` |
| `region_router.py` | `VoterListStatusResponse`, `DeleteVoterListResponse` |
| `demo_router.py` | `PrebakedSession`, `PrebakedSessionList` |

#### 17. Added `just stop` recipe

Added `stop` target to `justfile` + `Makefile` to kill all votecatcher-related processes (uvicorn, vite, port 8080/5173).

### Session 4 Files Changed

| File | Change |
|------|--------|
| `app/api_models.py` | **Created** — `ApiModel` base class with `alias_generator` |
| `app/routers/job_router.py` | Response/request models → `ApiModel` |
| `app/routers/campaign_router.py` | 9 models → `ApiModel` |
| `app/routers/results_router.py` | 3 models → `ApiModel` |
| `app/routers/session_router.py` | 3 models → `ApiModel` |
| `app/routers/upload_router.py` | 2 models → `ApiModel` |
| `app/routers/config_router.py` | 3 models → `ApiModel`; `FeatureFlagsResponse` converted from manual camelCase |
| `app/routers/region_router.py` | 2 models → `ApiModel` |
| `app/routers/demo_router.py` | 2 models → `ApiModel` |
| `justfile` | Added `stop` recipe |
| `Makefile` | Synced from justfile |

### Remaining Work (Session 4 incomplete)

1. **`app/schemas.py`** — Still uses plain `BaseModel`. Models like `SessionTokenResponse`, `WorkspaceResponse`, `MatchFieldsResponse` have multi-word snake_case fields that need `ApiModel`.
2. **`CreateCampaignRequest`** (`campaign_router.py:69`) — Still uses `BaseModel`. Single-word fields only but should be consistent.
3. **Tests not yet run** — `uv run pytest` to verify nothing broke.
4. **API output not yet verified** — Need to restart backend and `curl /api/jobs` to confirm camelCase.
5. **Frontend `FeatureFlagsResponse` consumers** — Field names changed from explicit camelCase (`simulationMode`) to snake_case + alias. Frontend code using these fields may need checking.

### Recommendations (updated)

1. ~~**Rename `backend/.env` to `backend/.env.example`**~~ **Fixed in Session 3**
2. ~~**Fix 2 CORS tests**~~ **Fixed in Session 3**
3. **Consider removing `dotenv` dependency** — the Settings system + env_loader handles all env loading.
4. **Complete `ApiModel` migration** — Update `schemas.py` and remaining `BaseModel` usages in routers.
5. **Regenerate frontend API client** — After backend camelCase is confirmed working, regenerate the OpenAPI client types to ensure alignment.
6. **Consider moderate CQRS** — See CQRS assessment below.

### CQRS Assessment

**Verdict: Moderate CQRS is a natural fit, but NOT a priority right now.**

#### What makes CQRS appropriate

| Indicator | Votecatcher Status |
|-----------|-------------------|
| Read/write complexity mismatch | Writes are simple (create job, upload file). Reads are complex (paginated results with multi-entity joins, metrics aggregation, filtering) |
| Async/background processing | Job lifecycle is a state machine with 11+ states, OCR and matching run as background tasks |
| Eventual consistency already exists | SSE for real-time status, event bus infrastructure present, job status polling |
| Business logic in routers | Routers mix data access with business logic (e.g. `get_campaign_results` in campaign_router is ~180 lines of joins and transforms) |

#### What would change

- **Commands**: Simple handlers for create job, upload file, start processing. Move validation to domain services.
- **Queries**: Dedicated query handlers for complex reads (results, metrics, setup-status). Could use denormalized read models to avoid expensive joins.
- **No separate databases**. Same SQLite/Postgres, just separate code paths.
- **No event sourcing**. Too complex for current requirements.

#### Why NOT now

1. The `ApiModel` migration (Session 4) isn't even tested yet. Get that working first.
2. Current architecture works. CQRS is an optimization, not a fix.
3. The biggest pain point right now is the snake_case/camelCase mismatch, which `ApiModel` solves.
4. Adding CQRS before the API contract is stable would create rework.

#### When to reconsider

- When read queries become a performance bottleneck (complex joins on large datasets)
- When routers grow beyond ~300 lines of query logic
- When the team needs to independently scale reads vs writes (production PostgreSQL)
- When adding caching or materialized views for the results/metrics endpoints

## Session 5 (2026-04-09) — ApiModel Migration Completion + Critical Bug Fix

### Problem

Session 4 left 3 incomplete items: `schemas.py` still used `BaseModel`, `CreateCampaignRequest` used `BaseModel`, and tests were never run. During TDD-driven completion, a **critical production bug** was discovered.

### Critical Bug Found

#### 18. `ApiModel` class unreachable — module shadowed by package

Both `app/api_models.py` (module file with `ApiModel` class) and `app/api_models/` (package directory with `database.py`) existed simultaneously. Python resolves `app.api_models` to the package (directory), making the `ApiModel` class in the `.py` file **unreachable at import time**.

All 8 routers importing `from app.api_models import ApiModel` were broken:

```python
ImportError: cannot import name 'ApiModel' from 'app.api_models'
```

This was a latent production bug — the app would fail to start if any router was actually loaded.

**Fix:** Merged `ApiModel` class into `api_models/__init__.py`, deleted the orphaned `api_models.py` file.

### Fixes Applied (TDD: Red → Green → Refactor)

#### 19. Completed `schemas.py` migration to `ApiModel`

All 11 models in `schemas.py` migrated from `BaseModel` to `ApiModel`. Models with multi-word fields now serialize to camelCase:

- `WorkspaceResponse` — `campaign_id` → `campaignId`, `campaign_name` → `campaignName`
- `SessionTokenResponse` — `access_token` → `accessToken`, `token_type` → `tokenType`, `refresh_token` → `refreshToken`, `expires_in` → `expiresIn`
- `OcrProviderPayload` — `provider_name` → `providerName`, `provider_model` → `providerModel`, `api_key` → `apiKey`
- `VoterRecordsUploadResponse`, `PetitionFileUploadResponse` — `file_name` → `fileName`
- `MatchFieldsResponse` — `field_names` → `fieldNames`
- Plus `Cookies`, `NewUser`, `Login`, `AuthUser`, `SuccessResponse`, `OcrMatchResponse` (single-word or no multi-word fields but migrated for consistency)

#### 20. Migrated `CreateCampaignRequest` to `ApiModel`

Last remaining `BaseModel` in router files. Now inherits `ApiModel` for consistency.

### Session 5 Files Changed

| File | Change |
|------|--------|
| `app/api_models/__init__.py` | **Restored** — `ApiModel` class merged from orphaned `api_models.py` |
| `app/api_models.py` | **Deleted** — was shadowed by `api_models/` package |
| `app/schemas.py` | All 11 models migrated from `BaseModel` to `ApiModel` |
| `app/routers/campaign_router.py` | `CreateCampaignRequest` migrated from `BaseModel` to `ApiModel`; removed unused `BaseModel` import |
| `tests/unit/schemas/test_serialization_contract.py` | **Created** — 13 BDD tests for camelCase serialization contract |

### Tests Added

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `tests/unit/schemas/test_serialization_contract.py` | 13 | BDD contract tests: `ApiModel` serialization (3), deserialization (2), `schemas.py` models (6), `CreateCampaignRequest` (2) |

### Test Results

- **Unit tests:** 624 passed (BDD tests all green)
- **Integration tests:** 29 failures — all are assertion mismatches where tests expect old `snake_case` JSON keys but API now correctly returns `camelCase`
- **These 29 failures are expected** — they are pre-existing from Session 4's incomplete ApiModel migration (Session 4 noted "Tests not yet run")

### Remaining Work (Session 5 incomplete)

1. **Integration test camelCase updates** — 25 integration tests across 5 files need `snake_case` → `camelCase` key assertions:
   - `tests/integration/api/test_sessions.py` — `"campaign_id"` → `"campaignId"`, `"session_type"` → `"sessionType"`, `"snapshot_data"` → `"snapshotData"`, `"created_at"` → `"createdAt"`
   - `tests/integration/api/test_campaign_metrics.py` — `"total_signatures"` → `"totalSignatures"`, `"progress_percentage"` → `"progressPercentage"`, `"high_confidence"` → `"highConfidence"`, `"voter_list_count"` → `"voterListCount"`, `"last_job"` → `"lastJob"`
   - `tests/integration/api/test_campaign_results.py` — `"page_size"` → `"pageSize"`, `"ocr_result_id"` → `"ocrResultId"`, `"extracted_name"` → `"extractedName"`, `"extracted_address"` → `"extractedAddress"`, `"job_id"` → `"jobId"`, `"similarity_score"` → `"similarityScore"`, `"voter_name"` → `"voterName"`, `"voter_address"` → `"voterAddress"`
   - `tests/integration/api/test_campaign_scans.py` — `"file_size"` → `"fileSize"`, `"original_filename"` → `"originalFilename"`
   - `tests/integration/api/test_setup_status.py` — `"voter_list"` → `"voterList"`, `"row_count"` → `"rowCount"`, `"uploaded_at"` → `"uploadedAt"`, `"file_count"` → `"fileCount"`, `"signature_count"` → `"signatureCount"`
2. **Unit test attribute updates** — 4 tests:
   - `tests/unit/jobs/test_batch_threshold.py` — `"alwaysBatchOcr"` in `model_fields.keys()` → `"always_batch_ocr"` (Python field name); `response.alwaysBatchOcr` → `response.always_batch_ocr`
   - `tests/unit/routers/test_config_router.py` — likely same pattern (1 test failure)
3. **API output verification** — Restart backend and `curl /api/jobs` to confirm camelCase in actual responses
4. **Frontend `FeatureFlagsResponse` consumers** — Field names changed from explicit camelCase to snake_case + alias

### Recommendations (updated)

1. ~~**Rename `backend/.env` to `backend/.env.example`**~~ **Fixed in Session 3**
2. ~~**Fix 2 CORS tests**~~ **Fixed in Session 3**
3. **Consider removing `dotenv` dependency** — the Settings system + env_loader handles all env loading.
4. ~~**Complete `ApiModel` migration**~~ **Done in Session 5** — `schemas.py` and `CreateCampaignRequest` migrated. All production models now use `ApiModel`.
5. ~~**Update integration tests**~~ **Done in Session 6** — All 22 camelCase assertion failures fixed.
6. **Regenerate frontend API client** — After backend camelCase is confirmed working, regenerate the OpenAPI client types to ensure alignment.
7. **Consider moderate CQRS** — See CQRS assessment above.

## Session 6 (2026-04-09) — Integration Test camelCase Fix + SetupStatus Dict Bug

### Problem

Session 5 left 22 test failures where assertions expected `snake_case` JSON keys but the API now correctly returns `camelCase` (due to `ApiModel.alias_generator`).

### Approach: TDD Red-Green-Refactor

**RED:** Confirmed 22 failures, 631 passed across the full suite. All failures were `KeyError` or `AssertionError` on `snake_case` keys in JSON responses.

**GREEN:** Updated test assertions file-by-file to match camelCase output.

**REFACTOR:** Discovered and fixed a production bug during GREEN phase (see below).

### Critical Bug Found

#### 21. `SetupStatusResponse` used `dict` fields — camelCase silently skipped

`SetupStatusResponse` in `campaign_router.py` declared `voter_list: dict`, `petitions: dict`, `jobs: dict`. Pydantic's `alias_generator` only transforms model field names, NOT dict contents. The nested keys (`row_count`, `uploaded_at`, `file_count`, `signature_count`) remained `snake_case` in API output while all other endpoints correctly returned `camelCase`.

**Fix:** Created typed sub-models `VoterListStatus`, `PetitionsStatus`, `JobsStatus` (all extending `ApiModel`) and replaced `dict` fields with typed model fields.

### Session 6 Files Changed

| File | Change |
|------|--------|
| `backend/app/routers/campaign_router.py` | Replaced `dict` fields with typed `ApiModel` sub-models in `SetupStatusResponse` |
| `backend/tests/integration/api/test_sessions.py` | Updated 4 assertions: `campaign_id`→`campaignId`, `session_type`→`sessionType`, `snapshot_data`→`snapshotData`, `created_at`→`createdAt` |
| `backend/tests/integration/api/test_campaign_metrics.py` | Updated 16 assertions: `totalSignatures`, `progressPercentage`, `highConfidence`/`mediumConfidence`/`lowConfidence`, `voterListCount`, `lastJob` |
| `backend/tests/integration/api/test_campaign_results.py` | Updated 6 assertions: `pageSize`, `extractedName`, `extractedAddress`, `jobId`, `voterName`, `voterAddress` |
| `backend/tests/integration/api/test_campaign_scans.py` | Updated 2 assertions: `fileSize` |
| `backend/tests/integration/api/test_setup_status.py` | Updated 4 assertions: `voterList`, `rowCount`, `fileCount` |
| `backend/tests/integration/api/test_jobs.py` | Updated 1 assertion: `originalFilename` |
| `backend/tests/unit/jobs/test_batch_threshold.py` | Updated 3 tests: `model_fields` keys use Python snake_case names, attribute access uses `always_batch_ocr` |
| `backend/tests/unit/routers/test_config_router.py` | Updated 1 assertion: `deletedCounts` |

### Test Results

**Test Results (Session 6):** 653 passed, 0 failures, 0 errors, 8 skipped

### Recommendations (updated)

1. ~~**Rename `backend/.env` to `backend/.env.example`**~~ **Fixed in Session 3**
2. ~~**Fix 2 CORS tests**~~ **Fixed in Session 3**
3. **Consider removing `dotenv` dependency** — the Settings system + env_loader handles all env loading.
4. ~~**Complete `ApiModel` migration**~~ **Done in Session 5**
5. ~~**Update integration tests**~~ **Done in Session 6** — All 22 camelCase assertion failures fixed.
6. **Audit `dict` fields in `ApiModel` subclasses** — Any `dict`-typed field silently bypasses `alias_generator`. Consider a contract test or linter rule.
7. **Regenerate frontend API client** — Backend camelCase is confirmed working. Regenerate OpenAPI client types.
8. **Consider moderate CQRS** — See CQRS assessment above.
