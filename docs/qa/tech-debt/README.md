# Tech Debt Tracking

Legacy issues discovered during baseline capture. Tracked separately from active feature work. Addressed incrementally after the next major feature milestone.

## Files

| File | Source | Updated When |
|------|--------|-------------|
| `secrets.md` | detect-secrets, gitleaks | Phase 0 + PR reviews |
| `coverage-gaps.md` | pytest-cov, vitest | Phase 0 + weekly |
| `dead-code.md` | vulture, ts-prune | Nightly scan |
| `complexity.md` | radon | Nightly scan |
| `duplication.md` | jscpd | Nightly scan |
| `dependencies.md` | osv-scanner, Trivy, license scan | Phase 0 + Renovate |
| `dockerfile.md` | hadolint, checkov | Phase 0 + infra changes |
| `sast-findings.md` | semgrep, bandit | Phase 0 + PR reviews |
| `frontend-type-errors.md` | svelte-check, vitest | Phase 13 + review |

## Cleanup Priority

1. **Security** — secrets in baseline, unauthenticated routes, dependency CVEs
2. **Suspicious deps** — remove streamlit, ipywidgets, matplotlib, duckdb from production
3. **`pymupdf` AGPL-3.0** — evaluate alternatives or accept risk
4. **Dockerfile hardening** — dev deps in production, non-root user, HEALTHCHECK
5. **docker-compose.yml** — hardcoded creds, healthchecks, resource limits
6. **Dead code** — remove unused functions/classes
7. **Duplication** — refactor patterns above threshold
8. **Complexity** — refactor functions above complexity threshold

## Schedule

| When | Action |
|------|--------|
| **After next major feature ships** | Full tech debt review. Address Critical + High items. |
| **Weekly** | Review nightly scan reports. Triage new findings. |
| **Per sprint** | Pick 2-3 tech debt items. Include in sprint planning. |
| **Coverage** | Increase `--cov-fail-under` by 5% per sprint. |

## Regenerating Baselines

```bash
# Re-run all baseline scans
bash .agent-workspace/quality-automation/baselines/capture-baselines.sh
```
