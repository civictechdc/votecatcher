# ADR-0010: Adopt Architecture Fitness Tests

## Status

Accepted

## Date

2026-07-21

## Crosslink

L2

## Context

VoteCatcher's backend and frontend have well-documented module boundaries (see `docs/architecture/project-structure.md` and `docs/agents/architecture-testing.md`), but those boundaries are currently enforced only by code review. As the codebase grows, accidental dependency inversion, cycles, and adapter leakage are becoming likely. We need an automated, repeatable way to prove that structural rules hold.

## Decision

Adopt architecture fitness tests as a first-class part of the test pyramid.

| Stack | Library | Test runner | Production code under test |
|-------|---------|-------------|----------------------------|
| Backend | [ArchUnitPython](https://github.com/LukasNiessen/ArchUnitPython) | pytest | `backend/app/` |
| Frontend | [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS) (`archunit`) | Vitest | `frontend/src/` |

Both libraries are kept as **development dependencies** and run with normal unit-test suites in pull-request CI.

### Structural rules

The tests enforce the inside-out, hexagonal direction already documented in `docs/agents/architecture-testing.md`:

1. **No import cycles** in production code.
2. **Inside-out boundaries**: domain/application code cannot depend on frameworks, persistence, transport, storage, OCR providers, or SvelteKit server integration. Adapters at the outside may depend on inner layers; dependencies point inward.
3. **Backend-specific boundaries**:
    - `app/domain/` cannot import `app/routers/`, `app/services/`, `app/jobs/`, `app/files/`, `app/persistence/`, `app/data/`, `app/repositories/`, FastAPI, SQLModel, or provider SDKs.
    - Routers cannot access persistence or data/database modules directly.
    - Outer backend modules (`app/services/`, `app/jobs/`, `app/files/`, `app/persistence/`, `app/data/`, and `app/repositories/`) cannot depend on `app/routers/`.
4. **Frontend-specific boundaries**:
   - Browser UI (routes, components, stores) cannot import `src/lib/server/` or database modules.
   - `src/lib/server/` cannot import route/page UI.
   - Stores cannot import routes, server-only modules, or database modules.
   - Generated OpenAPI clients are transport adapters and are excluded from internal-boundary rules.

### Legacy ratchet

The existing codebase has uneven boundaries, so the rollout will not block on every pre-existing violation. Each known violation is captured as a **checked-in, source-to-target exemption** in the relevant architecture test. CI fails for any violation not in that narrow baseline. New code must not add exemptions. Exemptions are removed as refactors eliminate the underlying dependency. Broad folder-wide exemptions or disabling an entire rule are prohibited.

### Metric gates

Start only with dependency direction and cycle detection. Do **not** gate on file length, method count, cohesion, or abstractness metrics. A metric may be introduced only after measuring a stable baseline, documenting why it predicts a real maintenance risk, and agreeing on a threshold.

## Verification

Each structural rule must be verifiable by a test that can be run locally and in CI:

- Backend: `cd backend && uv run pytest tests/architecture -v`
- Frontend: `cd frontend && bun run test:unit -- tests/architecture`

Rules must include their architectural rationale using the library's `because(...)` API or the test description. Exemptions must identify the source-to-target dependency, explain why it exists, link a removal issue, name an owner, and state removal criteria. When a PR changes a boundary, port, adapter classification, architecture test, exemption, or CI architecture gate, the agent must update `docs/agents/architecture-testing.md` and this ADR as needed.

## Consequences

### Positive

- Structural boundaries are enforced automatically, catching regressions before merge.
- Architectural intent is encoded in executable tests rather than relying on reviewer memory.
- The legacy ratchet lets us improve boundaries incrementally without a risky big-bang rewrite.

### Negative

- New architecture tests add maintenance overhead and may initially fail due to existing violations that must be baselined.
- Exemptions require disciplined tracking; unmaintained exemptions can hide technical debt.

### Neutral

- These tests are fitness functions, not replacements for behavior-driven tests. Domain and service tests must continue to assert observable scenarios.
- Frontend rules use `rule.check()` with normal imported Vitest assertions, so Vitest globals configuration is not required.
- Dependency graph reports may be generated for discovery and ADR/C4 maintenance, but they are not mandatory CI artifacts until report ownership and retention are defined.

## Alternatives Considered

1. **Strict clean-slate enforcement**
   - Pros: Boundaries would be pristine from day one.
   - Cons: Would require a large, risky refactor of existing code before any value is delivered.
   - Why not chosen: The current codebase has uneven boundaries; a ratchet preserves velocity while still preventing new decay.

2. **Advisory-only architecture tests**
   - Pros: No CI friction; easy to introduce.
   - Cons: Violations would be ignored and the tests would quickly become dead code.
   - Why not chosen: Advisory checks do not protect the architecture; CI must fail on unexempted violations.

## References

- `docs/agents/architecture-testing.md`
- `docs/architecture/project-structure.md`
- [ArchUnitPython](https://github.com/LukasNiessen/ArchUnitPython)
- [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS)
