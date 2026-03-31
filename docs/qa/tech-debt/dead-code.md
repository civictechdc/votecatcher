# Dead Code Tech Debt

> Last updated: 2026-03-29
> Source: vulture v2.16 (Python), ts-prune (TypeScript)
> Status: Baseline captured (Phase 0)

## Critical

_None._

## High

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| ~96 unused TypeScript exports | `frontend-svelt/src/` | ts-prune | Excluding `.svelte-kit/` and "used in module". Includes types, functions, and API helpers. |

**Key unused exports**: `default` (vite.config.ts:7), `mockMatchResponse` (mockMatchData.ts:6), `VoterList` (workspace-types.ts:1), `OcrProvider` (workspace-types.ts:47), `matchApi` (matching-requests.ts:12), `campaignsApi/uploadApi/jobsApi` (openapi-client.ts:9-11)

## Medium

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| Unused variable `cropped_assets` | `app/files/file_repository.py:78` | vulture | 100% confidence |
| Unused import `OCRService` | `app/jobs/job_orchestrator.py:22` | vulture | 90% confidence |
| Unreachable code after return | `app/jobs/worker.py:208` | vulture | 100% confidence |
| Unused variable `method_name` | `app/logger_config/app_logger.py:41` | vulture | 100% confidence |
| Unused variable `method_name` | `app/logger_config/app_logger.py:67` | vulture | 100% confidence |
| Unreachable code after return | `app/ocr/ocr_helper.py:453` | vulture | 100% confidence |

## Low / Informational

- vulture report: `baselines/vulture-baseline.txt`
- ts-prune report: `baselines/ts-prune-baseline.txt` (42KB)
