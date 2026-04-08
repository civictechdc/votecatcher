# PR #14 CI Failure Analysis

**PR:** [civictechdc/votecatcher#14](https://github.com/civictechdc/votecatcher/pull/14)
**Title:** refactor: SvelteKit frontend migration, OCR consolidation, and rename to `frontend/`
**Scope:** 696 changed files, ~90K additions, ~13K deletions
**Branch:** `refactor/svelte_frontend` → `main`
**Date analyzed:** 2026-04-08
**CI runs:** [CI](https://github.com/civictechdc/votecatcher/actions/runs/24159608946), [Security](https://github.com/civictechdc/votecatcher/actions/runs/24159608935), [Performance](https://github.com/civictechdc/votecatcher/actions/runs/24159608942)

## Summary

9 checks failed, 6 passed, 7 skipped (cascading from failures). The failures fall into three categories: CI config issues, code quality fixes, and dependency vulnerabilities.

### Passing

| Check | Workflow |
|-------|----------|
| backend-lint | CI |
| lockfile-integrity | CI |
| docs-validation | CI |
| changes | CI |
| frontend-fallow | CI |
| justfile-makefile-sync | CI |
| benchmarks | Performance |

### Skipped (cascading)

backend-test, frontend-test, frontend-typecheck, docker-build, dast, dast-smoke, security-test-backend — all gated on upstream checks that failed.

---

## Failing Checks

### 1. secrets-scan — CI Config Fix

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386125 |
| Fix effort | Low |
| Fixable in PR? | **Yes** — workflow YAML change only |

**Root cause:** `gitleaks git detect . --verbose` passes too many positional arguments. The current gitleaks version only accepts 1 arg for the `git` subcommand.

```
Error: accepts at most 1 arg(s), received 2
Usage: gitleaks git [flags] [repo]
```

**Fix:** Change the workflow command from `gitleaks git detect . --verbose` to `gitleaks detect . --verbose` (drop the `git` subcommand) or `gitleaks git --verbose .` depending on the installed version.

---

### 2. sca — CI Config Fix

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386115 |
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

### 3. frontend-lint — Code Fix

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608946/job/70507423354 |
| Fix effort | Trivial |
| Fixable in PR? | **Yes** |

**Root cause:** `oxfmt` found a formatting issue in one file. Two empty-file warnings from oxlint are non-blocking.

```
src/routes/(app)/auth/sign-in/+server.ts (0ms)
Format issues found in above 1 files. Run without `--check` to fix.
```

**Fix:** Run `just lint-frontend` locally and commit the result.

---

### 4. backend-typecheck — Config Fix

| Field | Value |
|-------|-------|
| Workflow | CI |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608946/job/70507479155 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** basedpyright cannot resolve `sqlalchemy`, `sqlmodel`, or `alembic` imports inside migration files under `backend/alembic/`. These are auto-generated migration scripts that run in a separate context and don't need type checking.

Key errors:
- `backend/alembic/env.py:6` — `Import "sqlalchemy" could not be resolved`
- `backend/alembic/env.py:7` — `Import "sqlmodel" could not be resolved`
- `backend/alembic/env.py:9` — `"context" is unknown import symbol`
- `backend/alembic/versions/20260312200000_*.py` — same pattern across all migration files
- `backend/alembic/versions/20260312210000_*.py`
- `backend/alembic/versions/20260317140000_*.py`
- `backend/alembic/versions/20260318230000_*.py`

**Fix:** Add `alembic/` to the basedpyright exclude configuration in `backend/pyrightconfig.json`:

```json
{
  "exclude": ["alembic"]
}
```

---

### 5. backend-security (bandit) — Code Fix

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386223 |
| Fix effort | Low–Medium |
| Fixable in PR? | **Yes** |

**Root cause:** bandit found 5 issues in application code:

| Rule | Severity | File | Line | Issue |
|------|----------|------|------|-------|
| B101 | Low | `app/common/data/supabase.py` | 13 | `assert` used for env var validation |
| B101 | Low | `app/common/data/supabase.py` | 27 | `assert` used for env var validation |
| B101 | Low | `app/data/database_client.py` | 20 | `assert` used for env var validation |
| B108 | Medium | `app/jobs/job_orchestrator.py` | 56 | Hardcoded `/tmp` directory |
| B101 | Low | (additional assert usage) | — | — |

**Fix:**

- Replace `assert url and key, "..."` with explicit `if not url or not key: raise ValueError("...")` or `RuntimeError`
- Replace `Path("/tmp")` with `Path(tempfile.gettempdir())` from the `tempfile` module

---

### 6. sast (semgrep) — Design Decision

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386119 |
| Fix effort | Medium–High |
| Fixable in PR? | **Partially** — suppress or fix |

**Root cause:** Semgrep (with `p/owasp-top-ten,p/fastapi` rules) found **42 blocking findings** — all are `semgrep.fastapi-unauthenticated-route` in backend routers. Every route in `campaign_router.py` and other routers lacks authentication decorators.

Affected routes (from `campaign_router.py` alone):
- `POST ""` — create campaign
- `GET ""` — list campaigns
- `GET "/{campaign_id}"` — get campaign
- `DELETE "/{campaign_id}"` — delete campaign
- `GET "/{campaign_id}/metrics"` — get campaign metrics
- `GET "/{campaign_id}/scans"` — list campaign scans
- `DELETE "/{campaign_id}/scans/{scan_id}"` — delete scan
- `GET "/{campaign_id}/results"` — get campaign results
- `GET "/{campaign_id}/setup-status"` — get setup status

**Options:**

1. **Suppress inline** — Add `# nosemgrep` to each route and create a follow-up issue for auth
2. **Add auth middleware** — Implement FastAPI `Depends()` auth on all routes
3. **Suppress at rule level** — Add to `.semgrepignore` or semgrep config

**Recommendation:** This is the most important real finding. Create a dedicated follow-up issue. For this PR, suppress with `# nosemgrep: fastapi-unauthenticated-route` and a TODO comment referencing the follow-up issue.

---

### 7. container-scan (Trivy) — Dependency Update

| Field | Value |
|-------|-------|
| Workflow | Security |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386180 |
| Fix effort | Low |
| Fixable in PR? | **Yes** |

**Root cause:** Trivy found 5 HIGH vulnerabilities in npm dependencies inside the backend Docker image:

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
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608935/job/70507386192 |
| Fix effort | Low–Medium |
| Fixable in PR? | **Mostly** |

**Root cause:** `bun audit` found 9 vulnerabilities (4 high, 4 moderate, 1 low):

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

### 9. bundle-size — Code Fix + Config

| Field | Value |
|-------|-------|
| Workflow | Performance |
| Job URL | https://github.com/civictechdc/votecatcher/actions/runs/24159608942/job/70507386011 |
| Fix effort | Low–Medium |
| Fixable in PR? | **Yes** |

**Root cause:** Vite build succeeds but produces ~20 Svelte compiler warnings. The actual failure appears to be a bundle size threshold violation.

Svelte 5 deprecation warnings (non-blocking but should be fixed):

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

**Fix:**

1. Migrate Svelte 4 event syntax to Svelte 5 (`on:click` → `onclick`, etc.)
2. Wrap reactive variables with `$state(...)`
3. Use `$derived` for computed values referencing store data
4. Add `aria-label` to icon-only buttons
5. Replace `<div onclick>` with `<button>` or add keyboard handlers
6. Check and adjust bundle size threshold if the SvelteKit baseline has legitimately changed

---

## Recommended Fix Order

| Priority | Check | Category | Effort | Impact |
|----------|-------|----------|--------|--------|
| 1 | secrets-scan | CI config | Trivial | Unblocks security pipeline |
| 2 | sca | CI config | Low | Unblocks dependency scanning |
| 3 | frontend-lint | Formatting | Trivial | 1-file auto-fix |
| 4 | backend-typecheck | Config | Low | Exclude alembic from pyright |
| 5 | backend-security | Code | Low | Replace asserts, fix /tmp |
| 6 | container-scan | Dependencies | Low | `bun update` + rebuild |
| 7 | frontend-security | Dependencies | Low–Medium | `bun update` + overrides |
| 8 | bundle-size | Code | Medium | Svelte 5 syntax migration |
| 9 | sast | Design | Medium–High | Auth strategy decision |

## Critical Finding

The **42 unauthenticated FastAPI routes** flagged by Semgrep (`sast`) are the most important real issue. Even with `# nosemgrep` suppressions in this PR, this needs a dedicated follow-up issue and implementation plan. Every CRUD endpoint in the application is currently publicly accessible.
