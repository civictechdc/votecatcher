# ADR-0012: PR-Only Advisory Gates with Scheduled Triage

## Status

Accepted

## Date

2026-11-13

## Crosslink

L3

## Context

CI gates dependency-advisory freshness with `uv audit` (backend) and `bun audit` (frontend). Both ran as hard, blocking steps on every workflow trigger — PRs, pushes to main, and the weekly schedule — against a live advisory database that the repository does not control.

Between 2026-11-12 and 2026-11-13 UTC, three advisories published within about a day of one another reddened main between PRs, with no code change responsible:

- soupsieve — GHSA-mmhr-3c5m-f64f
- basic-ftp — GHSA-5pm8-86m8-9m6r
- opentelemetry-api — GHSA-mf5v-w3w3-f6cg (fixed by #210, `bump opentelemetry-api to 1.45.2`)

When an advisory lands hours after a green merge, the next push-to-main CI run fails on `uv audit`/`bun audit` even though the merge itself passed its PR gate. The red main is unowned: there is no PR under review to attach the fix to, the failure blocks unrelated main-side automation (coverage badge, Docker builds), and the remediation arrives as a drive-by dependency bump competing with other work for attention.

## Decision

Gate advisory freshness by event type, not by branch:

1. **PRs keep the hard gates.** `uv audit` and `bun audit` (with the documented ignore list) fail the PR quality jobs when they report advisories. A PR is exactly where a fix can be requested alongside the change under review.
2. **Push-to-main runs stop gating on advisory freshness only.** The `uv audit`/`bun audit` steps are skipped on `push` and `schedule` events. Gates that reflect our code or shipped images stay unconditional on main: `bandit`, the backend security test suite, `vulture`, the SCA scans (osv-scanner, Trivy filesystem), and the Docker image Trivy gates all remain hard on every trigger.
3. **A triage job owns main's freshness.** It runs on the nominal weekly cron, after every main push, and on demand (`workflow_dispatch`), re-audits main with the same ignore lists, and files (or updates) a `dependency-advisories`-labeled issue with the full audit output. Advisory findings never fail the job — the audit steps exit 0 on findings and only the issue records them. Tooling failures (dependency install, audit crashes, GitHub API errors) do fail the run by design, so infrastructure problems stay visible instead of being swallowed into "no advisories". A human triages findings: bump the dependency, add a justified ignore, or accept the risk on the issue. A clean re-audit comments on and closes any open triage issue.

The local recipes `just security-scan-backend` / `just security-scan-frontend` are unchanged — developers triaging locally still see advisory failures immediately.

### Same-day advisory scenario

Advisory published 14:00, main last merged green 10:00. Under the old policy, the next main push (or the weekly scheduled run) failed `uv audit` with no code change to point at; the fix landed as an unscheduled drive-by bump while main stayed red for unrelated PRs. Under this policy: the PR that follows the advisory fails its own `uv audit` step with the advisory in the job log, the reviewer asks for the bump in that PR, and main never reddens on database drift. If no PR touches the affected stack for days, the post-merge triage run (with the weekly cron as backstop) files an issue with the advisory output — visibility without a red main.

## Verification

- `actionlint` passes on the modified workflow.
- The audit steps carry `if: github.event_name == 'pull_request'`, so push/schedule runs cannot hard-fail on advisories; job summaries annotate the skip.
- `dependency-advisory-triage` runs on `schedule`, `workflow_dispatch`, and `push` (the push trigger is already main-only), holds `issues: write`, and serializes via a `concurrency` group. Advisory findings cannot fail it: the audit steps exit 0 on findings (exit-code 1) and only the issue records them; other audit exit codes and infrastructure failures fail the run by design.
- bun's exit 1 conflates findings with registry/malformed-response errors — and its `--json` mode does not apply `--ignore` (it lists every advisory, ignored or not) — so the triage job classifies bun's exit 1 as findings only when the corroborating `bun audit --json` report parses and contains an advisory id outside the ignore list; otherwise the run fails as a tooling error.
- `just security-scan-backend` / `just security-scan-frontend` still run both audits hard for local use; their ignore-list comments stay in sync with CI.

## Consequences

### Positive

- Main stays green on advisory-database drift it cannot control; red main means red code.
- Advisories are still caught at review time (PRs) and tracked on main (triage issue), with known coverage gaps to accept explicitly: GitHub auto-disables scheduled workflows in public repositories after 60 days without repo activity; scheduled runs can be delayed or dropped under load; and direct pushes to main or admin merges bypass the PR gates entirely, so they land unscoped until the next triage run.
- The triage issue accumulates history via comments, giving one place to see when advisories appeared and how they were resolved.

### Negative

- If a PR is open for days and CI ran before the advisory landed, the advisory surfaces only at the next PR run or the nominally weekly triage job. That cadence is a target, not a guaranteed bound: GitHub documents that scheduled workflows can be delayed or dropped under load, so "about a week" is an expectation for the cron backstop, not an SLA. Post-merge triage runs narrow this for advisories that land between PRs.
- `uv audit` exits 0 when only "adverse project statuses" (archived, deprecated, or quarantined packages) are reported — those never reach PR review or triage. This matches the PR gate's behavior and is recorded as a known blind spot rather than an accident.
- `bandit` and the audit steps now diverge in gating, which needs the comment block to explain.

### Neutral

- The ignore list now lives in three places (PR gate, triage job, justfile recipe); each carries a keep-in-sync comment.
- The scheduled job depends on the default `GITHUB_TOKEN` having issues-write permission, which is explicit on the job.

## Alternatives Considered

1. **Keep audits hard everywhere; add `continue-on-error` on main**
   - Pros: audit always runs; minimal diff.
   - Cons: failed-then-continued steps still render as ❌ in job summaries, observably "red" main-side automation; audit output on every main push duplicates the scheduled job's role.
   - Why not chosen: the policy's goal is that main is visibly green and follow-up is tracked in one issue, not in scattered warnings.

2. **Pin the advisory databases (snapshot advisories at lockfile time)**
   - Pros: fully deterministic audits.
   - Cons: `uv audit`/`bun audit` have no documented support for pinning a remote advisory snapshot; building a custom advisory mirror is heavy machinery for this problem.
   - Why not chosen: out of proportion to the failure mode; event-type gating solves the visible problem with workflow logic only.

3. **Daily triage cron instead of weekly**
   - Pros: tighter bound on untracked advisories.
   - Cons: six more runs a week for a repository whose advisories historically arrive in bursts that PR gates already catch.
   - Why not chosen: weekly matches the existing schedule trigger; revisit if triage issues routinely age.

## References

- #210 — `fix(backend): bump opentelemetry-api to 1.45.2 (GHSA-mf5v-w3w3-f6cg)` (the first of the three remediations that motivated this ADR)
- `.github/workflows/ci.yml` — `dependency-audit` steps (PR-only) and `dependency-advisory-triage` job
- `justfile` — `security-scan-backend` / `security-scan-frontend` (unchanged local gates)
- GHSA-mmhr-3c5m-f64f (soupsieve), GHSA-5pm8-86m8-9m6r (basic-ftp, published 2026-11-12), GHSA-mf5v-w3w3-f6cg (opentelemetry-api) — the advisories that reddened main across 2026-11-12/13
