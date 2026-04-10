# Backend Architecture Improvements — Session Log

**Date:** 2026-04-10
**Status:** Active. Service layer extraction in progress.
**Test Results (Session 19):** 784 passed, 0 failures, 0 errors, 8 skipped
**svelte-check (Session 16):** 0 errors, 32 warnings in 9 files
**Vulture (Session 17):** 0 findings at 80%+ confidence
**Ruff (Session 19):** 0 errors

## Original Problem (Resolved, Sessions 1–8)

Backend (`main.py`) failed with `Error loading ASGI app. Could not import module "app.api"`. After creating `app/api.py`, a cascade of deeper issues surfaced — all resolved:

1. Missing `app/api.py` — recreated FastAPI entry point with 9 routers, CORS, `/health`, lifespan
2. `app/settings/__init__.py` — fixed stale import from deleted module
3. `app/dependencies.py` — removed module-level `load_dotenv()` that overrode `.env.local` with `.env`
4. Bare `load_dotenv()` in 4 files — created `app/settings/env_loader.py` with correct priority
5. `app/ocr/ocr_client_factory.py` — restored missing symbols after refactor
6. Missing `pyproject.toml` dependencies — added 11 packages, fixed `requires-python` range
7. `pytest-asyncio` mode — added `asyncio_mode = "auto"`
8. `mistralai` v2 breaking import change — updated imports
9. FK table registration — added `ensure_all_models_registered()` autouse fixture
10. `backend/.env` conflicting with `.env.local` — deleted
11. CORS tests missing `Origin` header — added
12–15. API snake_case → camelCase — created `ApiModel` base class, migrated all models, replaced `dict` fields with typed sub-models
16. Stale test patches — removed from integration/security conftest files
17. Removed `dotenv` dependency — replaced with pure-Python `env_parser.py`

## Architecture Improvements (Sessions 9–19)

### Service Layer Extractions

| Service | Session | Router Reduction | Unit Tests |
|---------|---------|-----------------|------------|
| `ResultsQueryService` | 9 | `results_router.py` 328 → ~65 lines | — |
| `CampaignQueryService` | 10 | `campaign_router.py` 672 → 433 lines | 13 BDD tests |
| `JobQueryService` | 12 | `job_router.py` 388 → 202 lines (48%) | 33 BDD tests |
| `CampaignManagementService` | 18 | `campaign_router.py` 433 → 282 lines (35%) | 16 BDD tests |
| `SessionService` | 19 | `session_router.py` 222 → 168 lines (24%) | 13 BDD tests |

### Frontend API Client — camelCase Alignment (Session 9)

Updated `openapi.yaml`, all 5 generated model files, and ~40+ frontend files from snake_case to camelCase.

### Frontend Form Data Contract — BDD/TDD (Session 11)

9 BDD integration tests covering form data contract. **Key finding:** `ApiModel`'s `alias_generator` does NOT apply to `Form()` parameters — FastAPI matches form data by exact Python parameter name. Frontend must send `campaign_id` (snake_case) for form fields.

**Frontend bugs fixed:** `UploadApi.ts` wrong param name, `uploads.ts` missing `campaignId` param, `getting-started/+page.svelte` snake_case/camelCase mismatch.

### Frontend TypeScript Type Sync (Sessions 13–16)

Resolved 115 → 0 `svelte-check` errors across 43 files over 4 sessions. 48 fix categories applied.

**Root causes:** (a) local snake_case interfaces shadowing generated camelCase API types, (b) broken Svelte HTML structure, (c) TypeScript strict-mode violations.

**Key fix patterns:** Replaced local interfaces with generated types, bracket notation for `Record<string, unknown>` and `import.meta.env`, non-null assertions for array access, removed dead code (unused imports/variables/unreachable branches), added `as any` cast for vitest/vite Plugin incompatibility.

### Backend Dead Code Cleanup (Session 17)

All 7 vulture findings at 80%+ confidence confirmed as false positives (framework-required params for FastAPI lifespan, Protocol methods, structlog processors, Pydantic hooks). Created `vulture_whitelist.py` for 7 items. Ruff: 12 → 0 errors.

## Key Architectural Findings

1. **Single source of truth for types:** Generated API types in `$lib/api/generated/models/` are canonical. Component-local interfaces that shadow them cause cascading type errors.
2. **Form data ≠ JSON body:** `ApiModel` aliases don't apply to `Form()` fields. Frontend must use snake_case for form uploads, camelCase for JSON.
3. **Service layer pattern:** Response builder methods (`_build_*_response`) are consistently duplicated across route handlers. Extracting them to services eliminates duplication and reduces router size by 24–48%.
4. **CQRS not yet appropriate:** Service layer extraction is the right first step. Reconsider only when read queries hit measurable performance walls on production PostgreSQL.

## Remaining Work

- `upload_router.py` (164 lines) — mostly HTTP-level orchestration; `FileService` already handles business logic
- `config_router.py` (160 lines), `region_router.py` (116 lines) — thin routers, low extraction value
- 32 `svelte-check` warnings in 9 frontend files
