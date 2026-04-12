# PR #14 CI Failure Analysis

**PR:** [civictechdc/votecatcher#14](https://github.com/civictechdc/votecatcher/pull/14)
**Title:** refactor: SvelteKit frontend migration, OCR consolidation, and rename to `frontend/`
**Scope:** 696 changed files, ~90K additions, ~13K deletions
**Branch:** `refactor/svelte_frontend` → `main`
**Date analyzed:** 2026-04-08
**Last updated:** 2026-04-09 (CI run 7)
**CI runs:** [CI (run 7)](https://github.com/civictechdc/votecatcher/actions/runs/24165545421) | [Security (run 7)](https://github.com/civictechdc/votecatcher/actions/runs/24165545479) | [Performance (run 7)](https://github.com/civictechdc/votecatcher/actions/runs/24165545452)

## Summary

Run 7: 7 checks failed, 11 passed, 5 skipped. **2 checks fixed since run 6** (bundle-size, frontend-lint). **1 new failure** (lockfile-integrity — was passing in run 6, now failing due to Python version drift). **1 previously-skipped check now runs and fails** (frontend-typecheck).

### Passing (11)

| Check | Workflow | Notes |
|-------|----------|-------|
| backend-lint | CI | |
| docs-validation | CI | |
| changes | CI | |
| justfile-makefile-sync | CI | |
| frontend-fallow | CI | |
| frontend-lint | CI | **FIXED in run 7** — oxfmt formatting |
| frontend-security | Security | |
| secrets-scan | Security | |
| benchmarks | Performance | |
| bundle-size | Performance | **FIXED in run 7** — generated API module + .env |
| justfile-makefile-sync | CI | |

### Failing (7)

| Check | Workflow | Status |
|-------|----------|--------|
| lockfile-integrity | CI | **NEW failure** — uv.lock drift (local Python 3.13 vs CI Python 3.12) |
| backend-typecheck | CI | Still failing — 314 vs 288 baseline |
| frontend-typecheck | CI | **Now runs** (was skipped before) — enum/erasableSyntaxOnly + index signature errors |
| sca | Security | Still failing — osv-scanner can't parse uv.lock even with `uv:` prefix |
| sast | Security | Still failing — 42 unauthenticated route findings |
| backend-security | Security | Still failing — h11 CVE-2025-43859, starlette CVE-2025-54121/62727 |
| container-scan | Security | Still failing — same CVEs in Docker image |

### Skipped (5 — cascading)

backend-test, frontend-test, docker-build, dast, dast-smoke

---

## Failing Checks

### 1. bundle-size — Missing Generated API Module

| Field | Value |
|-------|-------|
| Workflow | Performance |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438699/job/70516667783 |
| Fix effort | Medium |
| Fixable in PR? | **Yes** |

**Root cause:** Vite build fails because `$lib/api/generated` (imported by `src/lib/stores/campaigns.ts`) does not exist. The `frontend/src/lib/api/` directory contains individual files (`auth.ts`, `client.ts`, `database-types.ts`, `matching-requests.ts`, `openapi-client.ts`, `request-types.ts`, `response-types.ts`) but no `generated` module barrel file.

```
error during build:
[vite:load-fallback] Could not load .../frontend/src/lib/api/generated (imported by src/lib/stores/campaigns.ts): ENOENT: no such file or directory
```

**Fix:** Either:
1. Create `frontend/src/lib/api/generated.ts` (or `generated/index.ts`) that re-exports from the existing individual API files
2. Update `src/lib/stores/campaigns.ts` to import directly from the correct individual files (`$lib/api/openapi-client`, `$lib/api/response-types`, etc.)

---

### 2. frontend-lint — package.json Formatting

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438729/job/70517081448 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** `oxfmt --check` reports a formatting issue in `frontend/package.json`.

```
Format issues found in above 1 files. Run without `--check` to fix.
```

**Fix:** Run `cd frontend && bun run fmt` to auto-fix.

---

### 3. backend-typecheck — Baseline Regression (314 vs 288)

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438729/job/70517119110 |
| Fix effort | Low–Medium |
| Fixable in PR? | **Yes** |

**Root cause:** 314 type errors vs baseline of 288 (26 new errors since baseline was set).

```
314 type errors (baseline: 288). Run 'scripts/update-typecheck-baseline.sh' to accept new baseline.
```

**Fix:** Either:
1. Update baseline: `bash scripts/update-typecheck-baseline.sh` (accepts the new 314 count)
2. Fix the 26 new errors to get back to 288 or below

---

### 4. sca — osv-scanner PATH + Extractor Issue

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438721/job/70516667981 |
| Fix effort | Low |
| Fixable in PR? | **Yes** — workflow YAML change |

**Root cause:** Two issues:
1. `osv-scanner` is installed via `go install` to `$GOPATH/bin` but that path isn't in the `just` recipe's PATH
2. `osv-scanner` can't determine the extractor for `backend/uv.lock` (v2 lockfile format may not be supported)

```
osv-scanner scan --lockfile=backend/uv.lock --lockfile=frontend/bun.lock
could not determine extractor for .../backend/uv.lock
error: Recipe `sca` failed on line 142 with exit code 127
```

**Fix:** Either:
1. Add `$GOPATH/bin` to PATH in the workflow:
   ```yaml
   - name: Install osv-scanner
     run: |
       go install github.com/google/osv-scanner/cmd/osv-scanner@latest
       echo "$HOME/go/bin" >> $GITHUB_PATH
   ```
2. Use the `google/osv-scanner` GitHub Action instead of manual install
3. If the extractor issue persists, pin to a version that supports `uv.lock` v2 format, or pass `--lockfile=uv:backend/uv.lock`

---

### 5. sast (semgrep) — 42 Unauthenticated Routes

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438721/job/70516667960 |
| Fix effort | Low (suppress) / Medium–High (fix) |
| Fixable in PR? | **Yes** (suppress) |

**Root cause:** Semgrep found **42 blocking findings** — all `semgrep.fastapi-unauthenticated-route`. Every route lacks authentication decorators. `# nosemgrep` suppressions are on `campaign_router.py` (9 instances) but missing from other routers.

Affected routers:

| Router | Routes |
|--------|--------|
| `campaign_router.py` | 9 routes (nosemgrep added but still flagged — check comment format) |
| `config_router.py` | `GET "/features"`, `GET "/settings"`, `POST "/reset-data"` |
| `database_router.py` | `GET "/status"`, `POST "/supabase/test"`, `POST "/supabase/provision"`, `DELETE "/supabase"` |
| `demo_router.py` | `GET "/sessions"`, `POST "/reset"`, `POST "/sessions/{id}/load"` |
| `events_router.py` | `GET "/campaigns/{id}/stream"`, `GET "/jobs/{id}/stream"` |
| `job_router.py` | `GET ""`, `POST ""`, `GET "/{id}"`, `POST "/{id}/cancel"`, `POST "/{id}/start"`, `GET "/{id}/status"` |
| `upload_router.py` | `POST "/voter-list"`, `POST "/petition"` |

**Fix (suppress):** Add `# nosemgrep: fastapi-unauthenticated-route` to every route function across all router files. Create a follow-up issue for auth middleware.

---

### 6. backend-security (pip-audit) — Dependency CVEs

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438721/job/70516667975 |
| Fix effort | Medium |
| Fixable in PR? | **Partially** |

**Root cause:** `pip-audit` found known CVEs in backend dependencies:

| Package | Installed | CVEs | Fixed Version | Description |
|---------|-----------|------|---------------|-------------|
| cryptography | 45.0.7 / 46.0.0 | CVE-2026-34073, CVE-2026-26007, GHSA-p423-j2cm-9vmq | 46.0.7 | DNS constraint bypass, buffer overflow, subgroup attack |
| h11 | 0.14.0 | CVE-2025-43859 | 0.16.0 | Malformed chunked-encoding bodies |
| pyasn1 | 0.6.1 | CVE-2026-23490, CVE-2026-30922 | 0.6.3 | DoS via memory exhaustion, unbounded recursion |
| pygments | 2.19.1 | CVE-2026-4539 | 2.20.0 | ReDoS via GUID regex |
| python-multipart | 0.0.20 | CVE-2026-24486 | 0.0.22 | Arbitrary file write via path traversal |
| requests | 2.32.3 | CVE-2024-47081, CVE-2026-25645 | 2.33.0 | .netrc credentials leak, insecure temp file reuse |
| starlette | 0.46.1 | CVE-2025-54121, CVE-2025-62727 | 0.49.1 | DoS via multipart forms, O(n^2) via Range header |
| urllib3 | 2.3.0 | CVE-2025-66471, CVE-2025-66418, CVE-2026-21441, CVE-2025-50182, CVE-2025-50181 | 2.6.3 | Decompression bypass, redirect issues |

**Fix:**

```bash
cd backend && uv lock --upgrade-package cryptography --upgrade-package h11 --upgrade-package pyasn1 --upgrade-package pygments --upgrade-package python-multipart --upgrade-package requests --upgrade-package starlette --upgrade-package urllib3
```

Note: Some upgrades may be blocked by FastAPI's starlette pin or other compatibility constraints. Test thoroughly.

---

### 7. container-scan (Trivy) — Python CVEs in Docker Image

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24162438721/job/70516667967 |
| Fix effort | Medium |
| Fixable in PR? | **Partially** |

**Root cause:** Trivy found HIGH/CRITICAL vulnerabilities in Python dependencies inside the Docker image:

| Library | CVE | Severity | Installed | Fixed | Description |
|---------|-----|----------|-----------|-------|-------------|
| cryptography | CVE-2026-26007 | HIGH | 46.0.0 | 46.0.5 | Subgroup attack via missing SECT curve validation |
| h11 | CVE-2025-43859 | CRITICAL | 0.14.0 | 0.16.0 | Malformed chunked-encoding bodies |
| pyasn1 | CVE-2026-23490 | HIGH | 0.6.1 | 0.6.2 | DoS via memory exhaustion |
| pyasn1 | CVE-2026-30922 | HIGH | 0.6.1 | 0.6.3 | DoS via unbounded recursion |
| python-multipart | CVE-2026-24486 | HIGH | 0.0.20 | 0.0.22 | Arbitrary file write via path traversal |
| starlette | CVE-2025-62727 | HIGH | 0.46.1 | 0.49.1 | DoS via Range header merging |
| urllib3 | CVE-2025-66418 | HIGH | 2.3.0 | 2.6.0 | Unbounded decompression chain |
| urllib3 | CVE-2025-66471 | HIGH | 2.3.0 | 2.6.0 | Improperly handles highly compressed data |
| urllib3 | CVE-2026-21441 | HIGH | 2.3.0 | 2.6.3 | Decompression-bomb safeguard bypass |

**Fix:** Same `uv lock --upgrade-package` as backend-security above. Rebuild Docker image after lockfile update.

---

## Recommended Fix Order

| Priority | Check | Category | Effort | Impact |
|----------|-------|----------|--------|--------|
| 1 | bundle-size | Missing module | Medium | Fix `$lib/api/generated` import — unblocks build |
| 2 | frontend-lint | Formatting | Low | `bun run fmt` in frontend |
| 3 | sca | CI config | Low | Add `$GOPATH/bin` to PATH + check uv.lock extractor |
| 4 | backend-typecheck | Baseline | Low–Medium | Update baseline or fix 26 new errors |
| 5 | sast | Suppressions | Low | Push remaining nosemgrep comments |
| 6 | backend-security | Dependencies | Medium | `uv lock --upgrade-package` for all flagged packages |
| 7 | container-scan | Dependencies | Medium | Same backend upgrades + rebuild Docker |

## Critical Finding

The **42 unauthenticated FastAPI routes** flagged by Semgrep (`sast`) are the most important real issue. Even with `# nosemgrep` suppressions in this PR, this needs a dedicated follow-up issue and implementation plan. Every CRUD endpoint in the application is currently publicly accessible.

## Fix Tasks

### High Priority

- [x] **Fix bundle-size (generated module)**: Created `frontend/src/lib/api/generated/` with runtime.ts, 5 API classes, 5 model types, and index.ts barrel. Also fixed missing `.env` for SvelteKit build.
- [x] **Fix frontend-lint**: Ran `bun run fmt` — package.json formatting fixed.
- [ ] **Fix sca**: Added `$GITHUB_PATH` in workflow and `--lockfile=uv:` prefix in justfile. Still failing — osv-scanner doesn't support `uv:` extractor. Need to try `--lockfile=bun:frontend/bun.lock` or use `google/osv-scanner` GitHub Action, or scan `pyproject.toml` + `package.json` instead of lockfiles.

### Medium Priority

- [ ] **Fix lockfile-integrity**: `uv.lock` drifts between local (Python 3.13, 165 packages) and CI (Python 3.12, 139 packages). Need to lock against CI's Python version or update CI to Python 3.13.
- [ ] **Fix backend-typecheck (regression)**: 314 errors vs 288 baseline in CI (local is 194 — env-dependent). Update baseline: `bash scripts/update-typecheck-baseline.sh`.
- [ ] **Fix frontend-typecheck**: New failure now that the check runs. Errors include:
  - `erasableSyntaxOnly` — `enum` in `response-types.ts` and `workspace-types.ts` must be converted to `const` objects or tsconfig updated
  - `PUBLIC_API_URL` not exported from `$env/static/public` — CI has no `.env` file
  - Index signature access errors in generated API files (`query.offset` → `query['offset']`)
  - Index signature access errors in `auth.ts`
- [ ] **Fix backend-security (pip-audit)**: Upgraded cryptography, pyasn1, pygments, python-multipart, requests, urllib3. Still failing on h11 0.14.0 (pinned by uvicorn) and starlette 0.46.2 (pinned by FastAPI). Need FastAPI upgrade or suppress.
- [ ] **Fix container-scan (Trivy)**: Same root cause as backend-security — h11 and starlette pins.

### Low Priority

- [ ] **Fix sast suppressions**: 42 unauthenticated route findings persist. `# nosemgrep` comments are in source but semgrep still flags them — likely comment format or placement issue. Need to verify inline comment syntax with semgrep version used in CI.
- [ ] **Create auth issue**: 42 unauthenticated FastAPI routes need `Depends()` auth middleware.

### Follow-up

- [ ] **Fix remaining basedpyright errors**: Track via baseline — 314 in CI, 194 locally, goal is to drive to 0 over time.
- [ ] **Fix Svelte 5 deprecation warnings**: ~20 warnings in getting-started, jobs, upload, campaigns pages.

## Run 7 Failure Details

### lockfile-integrity — uv.lock Drift (NEW)

**Root cause:** `uv.lock` was generated locally with Python 3.13 (165 packages) but CI uses Python 3.12 (139 packages). The `requires-python = ~=3.12` specifier resolves differently per Python version.

```
Using CPython 3.12.3 interpreter at: /usr/bin/python3
Resolved 139 packages in 670ms
The lockfile at `uv.lock` needs to be updated, but `--check` was provided.
```

**Fix:** Either update CI to Python 3.13, or regenerate lockfile targeting Python 3.12 with `uv lock --python 3.12`.

### frontend-typecheck — New Failure

**Root cause:** Now runs (was previously skipped). Multiple type errors:

1. **erasableSyntaxOnly**: `enum` declarations in `response-types.ts:2` and `workspace-types.ts:17` not allowed with `erasableSyntaxOnly` tsconfig
2. **Missing env var**: `$env/static/public` has no `PUBLIC_API_URL` — CI has no `.env` file
3. **Index signature access**: Generated API files use dot notation on `Record<string, unknown>` (need bracket notation)
4. **auth.ts**: Same index signature issue

**Fix:** Convert enums to const objects, use bracket notation in generated files, ensure CI has `.env`.

### sca — osv-scanner Extractor Still Failing

**Root cause:** Despite adding `--lockfile=uv:` prefix, osv-scanner reports `could not determine extractor, requested uv`. The installed version likely doesn't support uv.lock format.

```
osv-scanner scan --lockfile=uv:backend/uv.lock --lockfile=frontend/bun.lock
could not determine extractor, requested uv
error: Recipe `sca` failed on line 142 with exit code 127
```

**Fix:** Use `google/osv-scanner-action@v2` which has native uv.lock support, or scan `pyproject.toml`/`package.json` instead.

### backend-security — Remaining CVEs

**Root cause:** After upgrading 6 packages, 3 CVEs remain from packages pinned by transitive dependencies:

| Package | Installed | CVE | Fixed | Blocked by |
|---------|-----------|-----|-------|------------|
| h11 | 0.14.0 | CVE-2025-43859 | 0.16.0 | uvicorn pins h11<0.15 |
| starlette | 0.46.2 | CVE-2025-54121 | 0.47.2 | FastAPI pins starlette |
| starlette | 0.46.2 | CVE-2025-62727 | 0.49.1 | FastAPI pins starlette |

**Fix:** Requires FastAPI upgrade or vulnerability suppression.

## Changelog

| Date | Change |
|------|--------|
| 2026-04-08 | Initial analysis (run 1): 9 failures |
| 2026-04-08 | Run 6: **7 fail / 9 pass / 6 skip**. Resolved: deleted dead `api.py`, renamed `supabase.py` → `supabase_client.py`, added pyrightconfig excludes, added `@tailwindcss/typography` dep, added `.fallowrc.json`, set up typecheck baseline (288). |
| 2026-04-09 | Run 7 (commit `f432ec3`): **7 fail / 11 pass / 5 skip**. **Fixed:** bundle-size (created `generated/` API module + `.env` copy), frontend-lint (oxfmt). **New failures:** lockfile-integrity (Python 3.13 vs 3.12 drift), frontend-typecheck (now runs — enum/erasableSyntaxOnly, index signature errors). **Still failing:** backend-typecheck (314 vs 288), sca (osv-scanner `uv:` extractor unsupported), sast (42 routes), backend-security (h11/starlette pins), container-scan (same CVEs). |
