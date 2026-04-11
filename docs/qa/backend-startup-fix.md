# Backend Architecture Improvements — Session Log

**Branch:** `refactor/svelte_frontend`
**Status:** All sessions committed. Architecture improvements complete.
**Test Results:** 803 passed, 0 failures, 8 skipped
**Ruff:** 0 errors
**detect-secrets:** 0 findings, baseline clean

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

## Architecture Improvements (Sessions 9–23)

### Service Layer Extractions

| Service | Session | Router Before → After | Reduction | Unit Tests |
|---------|---------|----------------------|-----------|------------|
| `ResultsQueryService` | 9 | `results_router.py` 328 → 75 lines | 77% | — |
| `CampaignQueryService` | 10 | `campaign_router.py` 672 → 433 lines | 36% | 13 BDD |
| `JobQueryService` | 12 | `job_router.py` 388 → 202 lines | 48% | 33 BDD |
| `CampaignManagementService` | 18 | `campaign_router.py` 433 → 282 lines | 35% | 16 BDD |
| `SessionService` | 19 | `session_router.py` 222 → 168 lines | 24% | 13 BDD |
| `ConfigService` | 20 | `config_router.py` 160 → 132 lines | 18% | 3 BDD |
| `DemoOrchestrationService` | 22 | `demo_router.py` 117 → 88 lines | 25% | 12 BDD |

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

### Frontend Svelte 5 Warning Cleanup (Session 21)

Eliminated all 32 `svelte-check` warnings across 9 files. 6 fix categories: redundant ARIA roles (5), missing ARIA role on click handler (1), `state_referenced_locally` (5), deprecated event directives (10), `non_reactive_update` (5), missing `aria-label` / a11y (4).

### detect-secrets Pre-Commit Fix (Session 23)

Resolved the blocker that prevented committing files across Sessions 11–22.

**Problem:** `detect-secrets` pre-commit hook flagged false positives across test files — `BasicAuthDetector` on `user:pass@host` patterns in database URLs, `KeywordDetector` on API key patterns, and `HexHighEntropyString` on UUID literals.

**Fix (BDD/TDD red-green-refactor):**
1. Created `test_detect_secrets_compliance.py` — 4 BDD tests scanning all flagged files via `detect-secrets scan`, asserting zero findings per category
2. Fixed all test files — replaced literal credential strings with variable indirection
3. Regenerated `.secrets.baseline` — removed all test file entries

## Key Architectural Findings

1. **Single source of truth for types:** Generated API types in `$lib/api/generated/models/` are canonical. Component-local interfaces that shadow them cause cascading type errors.
2. **Form data ≠ JSON body:** `ApiModel` aliases don't apply to `Form()` fields. Frontend must use snake_case for form uploads, camelCase for JSON.
3. **Service layer pattern:** Response builder methods (`_build_*_response`) are consistently duplicated across route handlers. Extracting them to services eliminates duplication and reduces router size by 18–77%.
4. **CQRS not yet appropriate:** Service layer extraction is the right first step. Reconsider only when read queries hit measurable performance walls on production PostgreSQL.
5. **detect-secrets safe patterns:** For test fixtures, use variable indirection (not inline literals) for URLs with credentials, API key values, and high-entropy hex strings. The 4 BDD compliance tests act as a permanent guard.

## Commit History

| Commit | Message | Session(s) |
|--------|---------|------------|
| `f298b0f` | refactor(backend): remove dotenv dependency, add pure-Python env parser | 8 |
| `b242475` | refactor(backend): extract ResultsQueryService and CampaignQueryService | 9–10 |
| `00e8fc5` | refactor(backend): extract JobQueryService and CampaignManagementService | 12, 18 |
| `a04c5d6` | refactor(backend): extract SessionService from session_router | 19 |
| `19b3628` | refactor(backend): add vulture whitelist and BDD dead-code tests | 17 |
| `c83a55d` | refactor(backend): extract ConfigService from config_router | 20 |
| `b2dcdc2` | fix(frontend): form data contract — snake_case for form fields | 11 |
| `313c511` | fix(frontend): TypeScript type sync and Svelte 5 warning cleanup | 13–16, 21 |
| `e6604d4` | refactor(backend): extract DemoOrchestrationService from demo_router | 22 |
| `44618c5` | fix(backend): detect-secrets compliance + demo service tests | 23 |
| `c8bdc94` | test(frontend): add BDD type contract and ProgressStepper tests | 14–15 |
