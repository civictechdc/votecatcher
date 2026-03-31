# SAST Findings Tech Debt

> Last updated: 2026-03-29
> Source: semgrep v1.156.0
> Status: Baseline captured (Phase 0)

## Critical

_None._

## High

| Finding | File:Line | Rule | Severity | Details |
|---------|-----------|------|----------|---------|
| Missing USER in Dockerfile | `backend/Dockerfile:15` | `dockerfile.security.missing-user.missing-user` | ERROR | Container may run as root |
| Raw SQL queries (15 occurrences) | `backend/scripts/purge_old_campaigns.py:29-193` | `python.sqlalchemy.security.sqlalchemy-execute-raw-query` | ERROR | SQL string concatenation — SQL injection risk |

**purge_old_campaigns.py details**: Lines 29, 57, 66, 71, 77, 86, 99, 108, 125, 134, 147, 156, 161, 170, 175, 193 contain raw SQLAlchemy `execute()` with formatted SQL strings.

## Medium

| Finding | File:Line | Rule | Severity | Details |
|---------|-----------|------|----------|---------|
| Formatted SQL query | `backend/scripts/purge_old_campaigns.py:29` | `python.lang.security.audit.formatted-sql-query` | WARNING | Use parameterized queries |
| Formatted SQL query | `backend/scripts/purge_old_campaigns.py:193` | `python.lang.security.audit.formatted-sql-query` | WARNING | Use parameterized queries |
| len(QUERY.all()) vs count() | `backend/app/routers/campaign_router.py:123` | `python.sqlalchemy.performance.performance-improvements.len-all-count` | WARNING | Use `QUERY.count()` for better performance |

## Low / Informational

- **Total**: 20 findings (17 ERROR, 3 WARNING)
- All findings are in `backend/` (no frontend SAST findings)
- `purge_old_campaigns.py` is a script (not runtime code) — lower risk but still needs parameterized queries
- Full report: `baselines/semgrep-baseline.json`
- Phase 2 strategy: Use `--baseline-commit` to only flag new findings
