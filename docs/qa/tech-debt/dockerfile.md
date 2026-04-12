# Dockerfile Tech Debt

> Last updated: 2026-03-29
> Source: hadolint v2.14.0, checkov v3.2.510
> Status: Baseline captured (Phase 0)

## Critical

_None._

## High

| Finding | File | Check | Tool | Details |
|---------|------|-------|------|---------|
| No HEALTHCHECK | `backend/Dockerfile` | CKV_DOCKER_2 | checkov | Container won't report health status to orchestrator |
| No HEALTHCHECK | `frontend-svelt/Dockerfile` | CKV_DOCKER_2 | checkov | Container won't report health status to orchestrator |
| No USER directive | `backend/Dockerfile` | CKV_DOCKER_3 | checkov | Container runs as root — security risk |
| No USER directive | `frontend-svelt/Dockerfile` | CKV_DOCKER_3 | checkov | Container runs as root — security risk |

## Medium

| Finding | File:Line | Rule | Tool | Details |
|---------|-----------|------|------|---------|
| Pin pip versions | `backend/Dockerfile:5` | DL3013 | hadolint | Use `pip install <package>==<version>` or `--requirement` |
| Avoid pip cache | `backend/Dockerfile:5` | DL3042 | hadolint | Use `pip install --no-cache-dir` |

## Low / Informational

- checkov: 12 passed / 4 failed (all failures are CKV_DOCKER_2 and CKV_DOCKER_3 for both Dockerfiles)
- hadolint: 2 warnings (both in backend/Dockerfile:5)
- frontend-svelt/Dockerfile: clean per hadolint
- Reports: `baselines/hadolint-baseline.txt`, `baselines/checkov-baseline.txt`
