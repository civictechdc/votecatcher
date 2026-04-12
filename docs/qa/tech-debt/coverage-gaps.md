# Coverage Gaps Tech Debt

> Last updated: 2026-03-29
> Source: pytest-cov (backend), vitest (frontend)
> Status: Baseline captured (Phase 0)

## Critical

| Finding | Area | Tool | Details |
|---------|------|------|---------|
| Frontend coverage not measurable | `frontend-svelt/` | vitest | `@vitest/coverage-v8` not installed. Cannot set `--coverage` thresholds. |

**Remediation**: `cd frontend-svelt && bun add -D @vitest/coverage-v8` — must be Phase 1 entrance gate.

## High

| Finding | Area | Tool | Details |
|---------|------|------|---------|
| 27 frontend tests failing | `frontend-svelt/` | vitest | `vi.resetModules` undefined, `localStorage`/`document` not defined, unresolved imports. 187 pass / 27 fail / 4 skip across 26 files. |
| 3 backend test errors | `backend/` | pytest | DB integration test errors. 340 pass / 3 errors / 5 skipped. |

## Medium

| Finding | Area | Tool | Details |
|---------|------|------|---------|
| Backend coverage at 64% | `backend/` | pytest-cov | 3749 statements, 1341 missed. Phase 1 threshold: `--cov-fail-under=64`. |

## Low / Informational

- Backend full report: `baselines/coverage-backend.txt` (118KB)
- Frontend full report: `baselines/coverage-frontend.txt` (35KB)
- Frontend has 13 test files with failures
