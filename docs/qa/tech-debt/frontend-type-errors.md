# Frontend Type Errors & Test Failures Tech Debt

> Last updated: 2026-04-06
> Source: svelte-check, vitest
> Status: Open (out of scope — jsdom/Svelte 5 incompatibility)

## TD-15: svelte-check Errors (~197 errors)

**Severity:** Low
**Area:** `frontend-svelt/`
**Tool:** `svelte-check`

svelte-check reports ~197 errors across ~107 files. Root cause is Svelte 5 strict TypeScript + jsdom incompatibility. Errors are in both pre-existing and new files (response-types.ts, featureFlags.ts, jobs.ts, handlers.ts use bracket notation on env vars that strict tsconfig requires `['env']` syntax).

**Status:** Open — out of scope for feature work. Track as tech debt.

**Resolution options:**
1. Fix bracket notation to use `['env']` syntax per strict tsconfig
2. Evaluate Svelte 5 + jsdom + vitest compatibility upgrade
3. Accept as known limitation

## TD-19: Integration Test ResourceWarning

**Severity:** Low
**Area:** `tests/integration/`
**Tool:** pytest

2 ResourceWarning: unclosed database connections in integration tests. Down from 236 (R7-5 fixed most of them).

**Status:** Mitigated — remaining 2 warnings are non-critical.

## Frontend Test Failures (~180 of 268 failing)

**Severity:** Medium (tracks as context for TD-15)
**Area:** `frontend-svelt/tests/unit/`
**Tool:** vitest

~180 frontend component tests fail due to Svelte 5 + jsdom rendering incompatibility. This is a test infrastructure issue, not broken application code. The 84-88 passing tests include non-component tests (demo.test.ts, stores/featureFlags.test.ts).

**Status:** Open — requires Svelte 5 + jsdom + vitest compatibility investigation.
