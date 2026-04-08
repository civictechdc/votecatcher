# Quality Automation

Quality baseline data and tech debt tracking for VoteCatcher.

## Structure

| Path | Purpose |
|------|---------|
| `baselines/SUMMARY.md` | Current baseline measurements and thresholds |
| `tech-debt/README.md` | Tech debt index with cleanup priorities and schedule |
| `tech-debt/*.md` | Per-category findings with severity, file locations, and tool source |

## Categories

- **secrets** — Secret detection findings (detect-secrets)
- **coverage-gaps** — Test coverage baselines (pytest-cov, vitest)
- **dead-code** — Unused code (vulture, ts-prune)
- **complexity** — Cyclomatic complexity (radon)
- **duplication** — Code duplication (jscpd)
- **dependencies** — Vulnerability tracking (osv-scanner, Trivy)
- **dockerfile** — Container image issues (hadolint, checkov)
- **sast-findings** — Static analysis findings (semgrep)

## Current Thresholds

- Backend `--cov-fail-under`: 36% (enforced minimum; baseline measurement is 64%)
- Frontend coverage: blocked (needs `@vitest/coverage-v8`)
- Code duplication threshold: 4%
- SAST: baseline mode (flag new findings only)
