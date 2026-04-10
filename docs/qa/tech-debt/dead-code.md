# Dead Code Tech Debt

> Last updated: 2026-04-10
> Source: vulture v2.16 (Python), ts-prune (TypeScript)
> Status: Phase 0 baseline captured. Session 17: all 80%+ Python findings resolved as false positives (whitelisted).

## Critical

_None._

## High

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| ~96 unused TypeScript exports | `frontend-svelt/src/` | ts-prune | Excluding `.svelte-kit/` and "used in module". Includes types, functions, and API helpers. |

**Key unused exports**: `default` (vite.config.ts:7), `mockMatchResponse` (mockMatchData.ts:6), `VoterList` (workspace-types.ts:1), `OcrProvider` (workspace-types.ts:47), `matchApi` (matching-requests.ts:12), `campaignsApi/uploadApi/jobsApi` (openapi-client.ts:9-11)

## Medium

~~All Python (vulture) findings at 80%+ confidence resolved in Session 17 — all were false positives.~~ See `backend/vulture_whitelist.py` for details.

| Finding | File:Line | Tool | Resolution |
|---------|-----------|------|------------|
| Unused variable `cropped_assets` | `app/files/file_repository.py:78` | vulture | **False positive** — Protocol method param, used by implementers. Whitelisted. |
| Unused import `OCRService` | `app/jobs/job_orchestrator.py:23` | vulture | **False positive** — TYPE_CHECKING import used as string type annotation (`"OCRService \| None"`). Whitelisted. |
| Unused variable `method_name` | `app/logger_config/app_logger.py:41` | vulture | **False positive** — Required by structlog processor protocol signature. Whitelisted. |
| Unused variable `method_name` | `app/logger_config/app_logger.py:67` | vulture | **False positive** — Required by structlog processor protocol signature. Whitelisted. |
| Unreachable code after return | ~~`app/jobs/worker.py:208`~~ | vulture | No longer reported at 80%+ confidence (stale baseline). |
| Unreachable code after return | ~~`app/ocr/ocr_helper.py:453`~~ | vulture | No longer reported at 80%+ confidence (stale baseline). |

**Session 17 actions:**
- Renamed `application` → `_application` in `app/api.py` lifespan callback (only actionable fix)
- Added `ConfidenceLevel` to TYPE_CHECKING import in `results_query_service.py` (ruff F821 fix)
- Created `backend/vulture_whitelist.py` for framework-required false positives
- 13 BDD tests added in `tests/unit/test_dead_code_cleanup.py` to guard against regressions

**Current vulture status:** 0 findings at 80%+ confidence. 0 ruff errors.

## Low / Informational

- vulture whitelist: `backend/vulture_whitelist.py`
- vulture baseline report: `baselines/vulture-baseline.txt`
- ts-prune report: `baselines/ts-prune-baseline.txt` (42KB)
- Run vulture: `cd backend && uv run vulture app/ vulture_whitelist.py --min-confidence 80`
