# Secrets Tech Debt

> Last updated: 2026-03-29
> Source: detect-secrets v1.5.0
> Status: Baseline captured (Phase 0)

## Critical

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| Real OpenAI API key | `Votecatcher/Large batch status.yml:14` | detect-secrets | `is_secret: true` in baseline. Historical commit (`ecb74f5`). Blocks GitHub push. |
| Real OpenAI API key | `Votecatcher/opencollection.yml:20` | detect-secrets | `is_secret: true` in baseline. Historical commit. Blocks GitHub push. |

**Remediation**: Run `git-filter-repo` or BFG Repo-Cleaner to purge from history. Allowlist URL: https://github.com/civictechdc/votecatcher/security/secret-scanning/unblock-secret/3BdZxjZFUoAwmRIAPvL0wuO8tSO

## High

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| Hardcoded DB password | `docker-compose.yml:35` | manual review | `POSTGRES_PASSWORD: votecatcher_dev` — should use `.env` variable |

## Medium

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| 37 potential secret matches (false positives) | 24 files | detect-secrets | Keyword matches in docs/skill files, UUID hex strings, example URLs. All audited as `is_secret: false`. |

## Low / Informational

- `.secrets.baseline` has 39 total findings across 24 files with 27 plugins active
- Baseline copy saved to `baselines/secrets-baseline.json`
