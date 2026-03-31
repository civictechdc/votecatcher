# Baseline Summary

> Generated: 2026-03-29

## Coverage

- **Backend**: 64% (3749 statements, 1341 missed) — 340 pass / 3 errors / 5 skipped
- **Frontend**: NOT MEASURABLE — `@vitest/coverage-v8` not installed; 187 pass / 27 fail / 4 skip

## Secret Detection

- **detect-secrets**: 39 findings across 24 files
  - 2 REAL secrets: OpenAI API keys in `Votecatcher/Large batch status.yml:14` and `Votecatcher/opencollection.yml:20`
  - 37 false positives: docs/skill keyword matches, UUID hex strings, example URLs

## Static Analysis Findings

- **semgrep**: 20 findings (17 ERROR, 3 WARNING)
  - Top: Dockerfile missing USER, SQLAlchemy raw queries, formatted SQL
- **vulture**: 6 dead code items
  - Unused variables, unreachable code, unused import
- **ts-prune**: ~96 unused exports (excluding `.svelte-kit` and "used in module")
- **radon complexity**: Multiple B/C rated functions, 1 E-rated function (`get_campaign_results`)
- **jscpd**: 3.37% duplication (654 lines across 63 clones)
  - Python: 2.65%, TypeScript: 4.81%

## Infrastructure Findings

- **hadolint**: 2 Dockerfile issues
  - DL3013: Pin pip versions (backend/Dockerfile:5)
  - DL3042: Avoid pip cache directory (backend/Dockerfile:5)
- **checkov**: 4 failed / 12 passed
  - CKV_DOCKER_2: No HEALTHCHECK in both Dockerfiles
  - CKV_DOCKER_3: No USER directive in either Dockerfile

## Dependency Vulnerabilities

- **osv-scanner**: 63 vulnerabilities (1 Critical, 28 High, 26 Medium, 7 Low, 1 Unknown)
  - Critical: `langchain-core` CVE-2025-68664 (arbitrary code execution via serialization)
  - 62 fixable with version updates
  - 35 packages affected across 2 ecosystems
- **Trivy fs**: 14 vulnerabilities in backend/uv.lock (1 CRITICAL, 10 HIGH), 3 in frontend/package-lock.json
  - Critical: `langchain-core` CVE-2025-68664

## Initial Thresholds (for Phase 1)

- Backend `--cov-fail-under`: 64%
- Frontend coverage: BLOCKED (needs `@vitest/coverage-v8`)
- jscpd threshold: 4% (current 3.37% + buffer)
- semgrep: Use `--baseline-commit` mode to only flag new findings

## Blockers

1. **GitHub push protection** blocks push — historical OpenAI key in `Votecatcher/` dir
2. **Frontend coverage not measurable** — needs `@vitest/coverage-v8` installed
3. **docker-compose.yml hardcoded password** — `POSTGRES_PASSWORD: votecatcher_dev`
