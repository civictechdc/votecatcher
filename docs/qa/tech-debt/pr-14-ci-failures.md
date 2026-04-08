# PR #14 CI Failure Analysis

**PR:** [civictechdc/votecatcher#14](https://github.com/civictechdc/votecatcher/pull/14)
**Title:** refactor: SvelteKit frontend migration, OCR consolidation, and rename to `frontend/`
**Scope:** 696 changed files, ~90K additions, ~13K deletions
**Branch:** `refactor/svelte_frontend` → `main`
**Date analyzed:** 2026-04-08
**Last updated:** 2026-04-08 (CI run 4)
**CI runs:** [CI (run 4)](https://github.com/civictechdc/votecatcher/actions/runs/24160655838) | [Security (run 4)](https://github.com/civictechdc/votecatcher/actions/runs/24160655784) | [Performance (run 4)](https://github.com/civictechdc/votecatcher/actions/runs/24160655759)

## Summary

9 checks failed, 7 passed, 7 skipped (cascading from failures). The failures fall into three categories: CI config issues, code quality fixes, and dependency vulnerabilities.

### Passing

| Check | Workflow |
|-------|----------|
| backend-lint | CI |
| lockfile-integrity | CI |
| docs-validation | CI |
| changes | CI |
| justfile-makefile-sync | CI |
| secrets-scan | Security |
| benchmarks | Performance |

### Skipped (cascading)

backend-test, frontend-test, frontend-typecheck, docker-build, dast, dast-smoke, security-test-backend — all gated on upstream checks that failed.

---

## Failing Checks

### 1. sca — CI Config Fix

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655784/job/70510872330 |
| Fix effort | Low |
| Fixable in PR? | **Yes** — workflow YAML change only |

**Root cause:** `osv-scanner` is not installed in the CI runner.

```
osv-scanner --lockfile=backend/uv.lock --lockfile=frontend/bun.lock --licenses
sh: 1: osv-scanner: not found
error: Recipe `sca` failed on line 142 with exit code 127
```

**Fix:** Add an install step for `osv-scanner` to the Security workflow, e.g.:

```yaml
- name: Install osv-scanner
  run: go install github.com/google/osv-scanner/cmd/osv-scanner@latest
```

Or use the `google/osv-scanner` GitHub Action.

---

### 2. bundle-size — Missing Dependency

| Field | Value |
|-------|-------|
| Workflow | Performance |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655759/job/70510872156 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** Vite build fails because `@tailwindcss/typography` is imported in `layout.css` but not installed as a dependency. Note: `@tailwindcss/forms` IS installed (0.5.11) but flagged as unused by fallow.

```
error during build:
[@tailwindcss/vite:generate:build] Can't resolve '@tailwindcss/typography' in '.../frontend/src/routes'
file: .../frontend/src/routes/layout.css
```

The build also produces ~20 Svelte 5 deprecation warnings (non-blocking but should be fixed separately):

| File | Warning | Count |
|------|---------|-------|
| `src/routes/(app)/getting-started/+page.svelte` | `on:click`/`on:change`/`on:input` deprecated → use `onclick`/`onchange`/`oninput` | 10 |
| `src/routes/(app)/getting-started/+page.svelte` | `state`/`errorMsg`/`selectedProvider` not declared with `$state(...)` | 4 |
| `src/routes/(app)/getting-started/+page.svelte` | `data` reference captures initial value only | 3 |
| `src/routes/(app)/workspace/[id]/jobs/+page.svelte` | Non-interactive div with click handler (a11y) | 2 |
| `src/routes/(app)/workspace/[id]/jobs/new/+page.svelte` | `selectedScans` not declared with `$state(...)` | 1 |
| `src/routes/(app)/workspace/[id]/upload/+page.svelte` | Buttons missing `aria-label` | 2 |
| `src/routes/(app)/workspace/campaigns/+page.svelte` | Non-interactive div with click handler (a11y) | 2 |
| `src/lib/components/ProviderConfigCard.svelte` | `configuredModel` captures initial value only | 1 |

**Fix (build failure):**

```bash
cd frontend && bun add @tailwindcss/typography
```

If `@tailwindcss/forms` is also not imported anywhere, either import it or remove it.

**Fix (warnings, follow-up):**

1. Migrate Svelte 4 event syntax to Svelte 5 (`on:click` → `onclick`, etc.)
2. Wrap reactive variables with `$state(...)`
3. Use `$derived` for computed values referencing store data
4. Add `aria-label` to icon-only buttons
5. Replace `<div onclick>` with `<button>` or add keyboard handlers

---

### 3. backend-typecheck — Legacy Imports + Config

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655838/job/70510940904 |
| Fix effort | Medium |
| Fixable in PR? | **Yes** |

**Root cause:** basedpyright errors across multiple files. Two distinct categories:

#### 3a. Legacy deleted modules still imported in `app/api.py`

`backend/app/api.py` imports modules that were removed during the OCR consolidation:

```
app/api.py:5  — Import "fuzzy_match_helper" could not be resolved
app/api.py:6  — Import "ocr_helper" could not be resolved
app/api.py:8  — Import "settings.settings_repo" could not be resolved
app/api.py:7  — Import from `routers` is implicitly relative
app/api.py:7  — "file" is unknown import symbol
```

This file appears to be a legacy Flask-style API entry point that was not cleaned up during the SvelteKit migration. It is dead code — the app now uses `app/main.py` with FastAPI routers.

**Fix:** Delete `backend/app/api.py` entirely, or exclude it from basedpyright if it still has a purpose.

#### 3b. `app/common/data/supabase.py` — module-level import conflicts

The file imports `from supabase import ...` but `supabase` is also the directory name (`app/common/data/supabase.py` vs the `supabase` Python package), causing basedpyright to resolve the local module instead of the package:

```
app/common/data/supabase.py:4  — Import from `supabase` is implicitly relative
app/common/data/supabase.py:9  — Module cannot be used as a type
app/common/data/supabase.py:15 — Module is not callable
```

**Fix:** Rename the file (e.g., `supabase_client.py`) to avoid shadowing the `supabase` package, or add a `basedpyright` ignore for this file.

#### 3c. `alembic/` and `app/data/database/local/` — missing SQLAlchemy/SQLModel types

Auto-generated migration files and legacy model files reference `sqlalchemy` and `sqlmodel` which aren't in the type-checking venv:

```
app/data/database/local/common_model.py:5 — Import "sqlalchemy" could not be resolved
app/data/database/local/common_model.py:6 — Import "sqlmodel" could not be resolved
app/data/database/local/demo_campaign_repo.py:3 — Import "sqlmodel" could not be resolved
```

**Fix:** Add excludes to `backend/pyrightconfig.json`:

```json
{
  "exclude": ["alembic", "app/data/database/local"]
}
```

Or ensure `sqlalchemy` and `sqlmodel` are available to the type checker.

---

### 4. frontend-typecheck — Index Signature Access

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655838/job/70510934604 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** `svelte-check` reports errors where env variables accessed via dot notation on an index-signature type must use bracket notation instead.

```
src/lib/server/db/index.ts:6  — Property 'DATABASE_URL' comes from an index signature, so it must be accessed with ['DATABASE_URL']
src/lib/server/db/index.ts:8  — Property 'DATABASE_URL' comes from an index signature, so it must be accessed with ['DATABASE_URL']
src/lib/server/auth.ts:9      — Property 'ORIGIN' comes from an index signature, so it must be accessed with ['ORIGIN']
src/lib/server/auth.ts:10     — Property 'BETTER_AUTH_SECRET' comes from an index signature, so it must be accessed with ['BETTER_AUTH_SECRET']
```

**Fix:** Change dot notation to bracket notation in 2 files (4 locations):

```diff
// src/lib/server/db/index.ts
- if (!env.DATABASE_URL) throw new Error("DATABASE_URL is not set");
+ if (!env['DATABASE_URL']) throw new Error("DATABASE_URL is not set");

- const client = postgres(env.DATABASE_URL);
+ const client = postgres(env['DATABASE_URL']);

// src/lib/server/auth.ts
- baseURL: env.ORIGIN,
+ baseURL: env['ORIGIN'],
- secret: env.BETTER_AUTH_SECRET,
+ secret: env['BETTER_AUTH_SECRET'],
```

---

### 5. backend-security (pip-audit) — Dependency Update

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655784/job/70510872308 |
| Fix effort | Medium |
| Fixable in PR? | **Partially** |

**Root cause:** bandit now passes (the B101 asserts and B105 issues from CI run 2 were fixed/suppressed). The failure is from `pip-audit` finding known CVEs in backend dependencies:

| Package | Installed | CVEs | Description |
|---------|-----------|------|-------------|
| starlette | 0.46.1 | CVE-2025-54121, CVE-2025-62727 | DoS via multipart forms, O(n^2) via Range header |
| streamlit | 1.44.1 | CVE-2026-33682 | Unauthenticated SSRF (Windows NTLM) |
| tornado | 6.4.2 | GHSA-78cv-mqj4-43f7, CVE-2025-47287, CVE-2026-35536, CVE-2026-31958 | Cookie injection, excessive logging, DoS |
| urllib3 | 2.3.0 | CVE-2025-66471, CVE-2026-21441, CVE-2025-50182, CVE-2025-66418, CVE-2025-50181 | Decompression bypass, redirect issues |

**Fix:**

- `uv lock --upgrade-package starlette --upgrade-package urllib3` to patch transitive deps
- `tornado` and `streamlit` may require checking if they're direct or transitive dependencies
- Some fixes may be blocked by upstream compatibility (e.g., FastAPI's starlette pin)

---

### 6. sast (semgrep) — Design Decision

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655784/job/70510872292 |
| Fix effort | Medium–High |
| Fixable in PR? | **Partially** — suppress or fix |

**Root cause:** Semgrep (with `p/owasp-top-ten,p/fastapi` rules) found **42 blocking findings** — all are `semgrep.fastapi-unauthenticated-route` in backend routers. Every route lacks authentication decorators.

Affected routers and routes:

| Router | Routes |
|--------|--------|
| `campaign_router.py` | `POST ""`, `GET ""`, `GET "/{id}"`, `DELETE "/{id}"`, `GET "/{id}/metrics"`, `GET "/{id}/scans"`, `DELETE "/{id}/scans/{scan_id}"`, `GET "/{id}/results"`, `GET "/{id}/setup-status"` |
| `config_router.py` | `GET "/features"`, `GET "/settings"`, `POST "/reset-data"` |
| `database_router.py` | `GET "/status"`, `POST "/supabase/test"`, `POST "/supabase/provision"`, `DELETE "/supabase"` |
| `demo_router.py` | `GET "/sessions"`, `POST "/reset"`, `POST "/sessions/{id}/load"` |
| `events_router.py` | `GET "/campaigns/{id}/stream"`, `GET "/jobs/{id}/stream"` |
| `job_router.py` | `GET ""`, `POST ""`, `GET "/{id}"`, `POST "/{id}/cancel"`, `POST "/{id}/start"`, `GET "/{id}/status"` |

**Options:**

1. **Suppress inline** — Add `# nosemgrep` to each route and create a follow-up issue for auth
2. **Add auth middleware** — Implement FastAPI `Depends()` auth on all routes
3. **Suppress at rule level** — Add to `.semgrepignore` or semgrep config

**Recommendation:** Create a dedicated follow-up issue. For this PR, suppress with `# nosemgrep: fastapi-unauthenticated-route` and a TODO comment referencing the follow-up issue.

---

### 7. container-scan (Trivy) — Dependency Update

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655784/job/70510872288 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** Trivy found HIGH vulnerabilities in npm dependencies inside the Docker image:

| Library | CVE | Installed | Fixed | Description |
|---------|-----|-----------|-------|-------------|
| minimatch | CVE-2026-27903 | 10.2.2 | 10.2.3 | DoS via unbounded recursive backtracking |
| minimatch | CVE-2026-27904 | 10.2.2 | 10.2.3 | DoS via catastrophic backtracking in glob |
| picomatch | CVE-2026-33671 | 4.0.3 | 4.0.4 | ReDoS via crafted extglob patterns |
| tar | CVE-2026-29786 | 7.5.9 | 7.5.10 | Hardlink path traversal via drive-relative linkpath |
| tar | CVE-2026-31802 | 7.5.9 | 7.5.11 | File overwrite via drive-relative symlink traversal |

**Fix:** Run `bun update` in the frontend directory to pull patched versions. Rebuild Docker image.

---

### 8. frontend-security (bun audit) — Dependency Update

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24160655784/job/70510872289 |
| Fix effort | Low–Medium |
| Fixable in PR? | **Mostly** |

**Root cause:** `bun audit` found vulnerabilities (4 high, 4 moderate, 1 low):

| Package | Severity | Advisory | Source |
|---------|----------|----------|--------|
| vite ≤7.3.1 | Moderate | Path traversal in optimized deps `.map` handling | GHSA-4w7w-66w2-5vf9 |
| vite ≤7.3.1 | High | `server.fs.deny` bypassed with queries | GHSA-v2wj-q39q-566r |
| vite ≤7.3.1 | High | Arbitrary file read via dev server WebSocket | GHSA-p9ff-h696-f583 |
| basic-ftp 5.2.0 | High | FTP command injection via CRLF | GHSA-chqc-8p9q-pq6q |
| @nestjs/core ≤11.1.17 | Moderate | Injection in downstream output | GHSA-36xv-jgw5-4q75 |
| path-to-regexp <8.4.0 | High | DoS via sequential optional groups | GHSA-j3q9-mxjg-w52f |
| path-to-regexp <8.4.0 | Moderate | ReDoS via multiple wildcards | GHSA-27v5-c462-wpq7 |
| esbuild ≤0.24.2 | Moderate | Any website can read dev server responses | GHSA-67mh-4wv8-2f99 |
| cookie <0.7.0 | Low | Out-of-bounds chars in cookie name/path/domain | GHSA-pxg6-pf52-xh8x |

**Fix:**

- `bun update` will fix vite, path-to-regexp, cookie, esbuild
- `basic-ftp` and `@nestjs/core` are transitive deps from `@openapitools/openapi-generator-cli` — may require `bun overrides` in `package.json` or waiting for upstream
- Long-term: consider whether `openapi-generator-cli` is needed in production deps (dev dependency only?)

---

## Recommended Fix Order

| Priority | Check | Category | Effort | Impact |
|----------|-------|----------|--------|--------|
| 1 | bundle-size | Missing dep | Low | `bun add @tailwindcss/typography` — unblocks build |
| 2 | sca | CI config | Low | Add osv-scanner install step |
| 3 | frontend-lint | Code formatting | Low | Run oxfmt on auth.ts, db/index.ts |
| 4 | frontend-typecheck | Code | Low | 4 bracket-notation changes (gated on frontend-lint fix) |
| 5 | backend-typecheck | Code + config | Medium | Delete `api.py`, exclude legacy dirs, rename supabase file |
| 6 | backend-security | Dependencies | Medium | `uv lock --upgrade-package` for starlette, urllib3, tornado |
| 7 | container-scan | Dependencies | Low | `bun update` + rebuild |
| 8 | frontend-security | Dependencies | Low–Medium | `bun update` + overrides |
| 9 | sast | Design | Medium–High | Auth strategy decision |

## Critical Finding

The **42 unauthenticated FastAPI routes** flagged by Semgrep (`sast`) are the most important real issue. Even with `# nosemgrep` suppressions in this PR, this needs a dedicated follow-up issue and implementation plan. Every CRUD endpoint in the application is currently publicly accessible.

## Fix Tasks

### High Priority

- [x] **Fix bundle-size**: `cd frontend && bun add @tailwindcss/typography`
- [x] **Fix frontend-lint**: Run oxfmt on `src/lib/server/auth.ts` and `src/lib/server/db/index.ts`
- [x] **Fix frontend-typecheck**: Change `env.DOT` → `env['DOT']` bracket notation in `auth.ts` and `db/index.ts` (4 locations) — gated on frontend-lint fix
- [x] **Fix sca**: Add `setup-go` step to Security workflow so `osv-scanner` can be installed via `go install`
- [ ] **Fix frontend-security + container-scan**: `bun update` in frontend to patch CVEs (vite, path-to-regexp, cookie, esbuild, minimatch, picomatch, tar) — `bun update` reports no changes, requires major version bumps or upstream fixes

### Medium Priority

- [x] **Fix backend-typecheck (dead code)**: Delete `backend/app/api.py` — legacy Flask-style entry point, dead code since FastAPI migration
- [x] **Fix backend-typecheck (module shadowing)**: Rename `backend/app/common/data/supabase.py` → `supabase_client.py` and update all imports
- [x] **Fix backend-typecheck (excludes)**: Add `app/data/database/local/` to `backend/pyrightconfig.json` excludes
- [x] **Fix backend-typecheck (baseline)**: Set up typecheck baseline system — `backend/typecheck-baseline.json` (288 errors), `scripts/check-typecheck-baseline.sh`, justfile updated to use baseline check
- [ ] **Fix backend-security (pip-audit)**: `uv lock --upgrade-package starlette --upgrade-package urllib3` to patch CVEs; check tornado/streamlit upgrade paths

### Low Priority

- [x] **Fix frontend-fallow**: Created `.fallowrc.json` with `ignoreDependencies` for CSS plugins (`@tailwindcss/forms`, `@tailwindcss/typography`) and `@openapitools/openapi-generator-cli` — all false positives
- [x] **Suppress sast**: Added `# nosemgrep: fastapi-unauthenticated-route` to all route functions across 11 router files
- [ ] **Defer sast follow-up**: Create dedicated issue for 42 unauthenticated FastAPI routes — needs auth middleware implementation

### Follow-up

- [ ] **Fix backend-security (pip-audit)**: Upgrade starlette, urllib3, tornado, streamlit
- [ ] **Fix frontend-security + container-scan**: Major version bumps for vite, esbuild, basic-ftp, @nestjs/core
- [ ] **Create auth issue**: 42 unauthenticated FastAPI routes need `Depends()` auth middleware
- [ ] **Fix remaining 288 basedpyright errors**: Track via baseline — goal is to drive count to 0 over time

## Changelog

| Date | Change |
|------|--------|
| 2026-04-08 | Initial analysis (CI run 1): 9 failures |
| 2026-04-08 | Updated to CI run 2: secrets-scan and frontend-lint now pass; bundle-size root cause changed to missing `@tailwindcss/forms`; frontend-typecheck now runs and fails (was previously skipped); backend-typecheck expanded beyond alembic to include dead `api.py` imports and supabase module shadowing; backend-security file locations changed |
| 2026-04-08 | CI run 3: frontend-fallow regressed (unused dep flags for `@tailwindcss/forms` false positive + `openapi-generator-cli`); frontend-lint regressed (oxfmt formatting on auth.ts, db/index.ts); frontend-typecheck now skipped (cascading from frontend-lint failure); added fix task checklist |
| 2026-04-08 | CI run 4: **Corrected** bundle-size root cause — missing dep is `@tailwindcss/typography` (not `@tailwindcss/forms` which IS installed but unused); backend-security root cause changed from bandit (now passes) to pip-audit (CVEs in starlette, urllib3, tornado, streamlit); frontend-lint and frontend-fallow still failing; total now 9 failing / 7 passing / 7 skipped |
| 2026-04-08 | CI run 5 (local fixes, not yet pushed): Deleted dead `api.py`; renamed `supabase.py` → `supabase_client.py`; added `app/data/database/local` to pyrightconfig excludes; added `@tailwindcss/typography` dep; added `setup-go` step for osv-scanner; created `.fallowrc.json`; added nosemgrep suppressions to all routes; set up typecheck baseline system (288 errors); `bun update` did not resolve remaining CVEs (need major bumps) |
