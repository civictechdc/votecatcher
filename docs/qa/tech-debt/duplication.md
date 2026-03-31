# Duplication Tech Debt

> Last updated: 2026-03-29
> Source: jscpd v4.0.8
> Status: Baseline captured (Phase 0)

## Critical

_None._

## High

_None._

## Medium

| Finding | Area | Tool | Details |
|---------|------|------|---------|
| 3.37% overall code duplication | codebase-wide | jscpd | 654 duplicated lines across 63 clones |
| TypeScript: 4.81% duplication | `frontend-svelt/` | jscpd | Higher than Python; test files are primary source |

**Key duplication hotspots (TypeScript)**:
- `frontend-svelt/src/routes/workspace/api/upload/+server.ts` — 20-line clone (lines 63-83 vs 36-55)
- `frontend-svelt/src/routes/getting-started/+page.server.ts` — 3 overlapping clones (lines 70-123)
- `frontend-svelt/src/routes/auth/+page.server.ts` — 2 clones (lines 25-53)
- Test files (`Select.test.ts`, `Modal.test.ts`, `Table.test.ts`) — repeated test patterns

## Low / Informational

- Python: 2.65% duplication
- Phase 1 jscpd threshold: 4% (current 3.37% + buffer)
- Full report: `baselines/jscpd-baseline.txt`
