# Architecture Testing

Use architecture tests as executable fitness functions. They protect dependency direction while behavior-focused tests protect product outcomes.

## Tools

- Backend: [`archunitpython`](https://github.com/LukasNiessen/ArchUnitPython), run through pytest.
- Frontend: [`archunit`](https://github.com/LukasNiessen/ArchUnitTS), run through Vitest.

Keep both as development dependencies. Architecture tests run with normal unit tests and must execute in pull-request CI for changed backend or frontend paths.

## Design Principle

VoteCatcher follows an inside-out, hexagonal direction:

1. Domain rules are independent of frameworks, persistence, transport, storage, and external providers.
2. Application services orchestrate domain behavior through explicit ports.
3. Routers, database engines, file storage, OCR providers, and SvelteKit server integration are adapters at the outside.
4. Dependencies point inward. Adapters may depend on application/domain code; domain code must not depend on adapters.

Architecture tests enforce structural boundaries. They do not replace behavior-driven tests. Domain and service tests must state observable scenarios, such as a valid petition upload creating resumable page work, rather than asserting private calls or implementation order.

## Backend Rules

Architecture tests under `backend/tests/architecture/` must cover production `backend/app/` code and enforce:

- No import cycles.
- `app/domain/` cannot depend on `app/routers/`, `app/services/`, `app/jobs/`, `app/files/`, `app/persistence/`, `app/data/`, `app/repositories/`, FastAPI, SQLModel, or provider SDKs.
- Routers are transport adapters and cannot access persistence or data/database modules directly.
- Outer backend modules (`app/services/`, `app/jobs/`, `app/files/`, `app/persistence/`, `app/data/`, and `app/repositories/`) cannot depend on `app/routers/`.
- Application services use domain code and declared ports. Direct legacy adapter dependencies are recorded as temporary exemptions.

Exclude tests, Alembic migrations, scripts, generated code, and explicit compatibility shims from these checks. Keep exclusions narrow and explain them in the test or `.archignore` entry.

## Frontend Rules

Architecture tests under `frontend/tests/architecture/` must cover production `frontend/src/` code and enforce:

- No import cycles.
- Browser UI, including routes, components, and stores, cannot import `src/lib/server/` or database modules.
- `src/lib/server/` cannot import route/page UI.
- Stores cannot import routes, server-only modules, or database modules.
- Generated OpenAPI clients are transport adapters and are excluded from internal-boundary rules.

SvelteKit route files are delivery adapters. Keep domain policy and reusable application behavior outside routes and page components where practical.

## Ratchet Policy

The current codebase has uneven boundaries. Do not block the initial rollout on every pre-existing violation.

- Capture each existing violation as a checked-in, source-to-target exemption in the relevant architecture test.
- CI fails for every violation not in that narrow baseline.
- New code must not add exemptions.
- Remove exemptions as refactors eliminate the underlying dependency.
- Never use broad folder-wide exemptions or disable an entire rule to make CI pass.

Each rule must include its architectural reason using the library's `because(...)` API or the test description. This makes failures actionable and preserves decision context.

## Rule Selection

Start with dependency direction and cycle detection. Do not initially gate file length, method count, cohesion, or abstractness metrics. Introduce a metric only after measuring a stable baseline, documenting why it predicts a real maintenance risk, and agreeing on a threshold.

Use dependency graph reports for discovery and ADR/C4 maintenance, not as a mandatory build artifact until report ownership and retention are defined.

## Verification Commands

After the architecture-test dependencies and suites are installed, run focused checks from the repository root:

```bash
cd backend && uv run pytest tests/architecture -v
```

```bash
cd frontend && bun run test:unit -- tests/architecture
```

Run the normal backend or frontend unit suite before merge as well. ArchUnitPython and ArchUnitTS execute inside pytest and Vitest; neither requires a separate architecture-test CLI.

## CI Integration

Backend architecture tests run as part of the backend Test step in `.github/workflows/ci.yml` (`tests/architecture` is included in the pytest invocation). Frontend architecture tests are collected automatically by Vitest's `tests/**/*.{test,spec}.{js,ts}` include pattern — no separate workflow step is needed.

## Continuous Improvement

Treat architecture guidance, architecture tests, and decision records as one system of record.

- When a PR changes a boundary, port, adapter classification, architecture test, exemption, or CI architecture gate, update this document when its rule or rationale changes.
- When that change creates, revises, or supersedes an architectural decision, add or update the relevant ADR in `docs/architecture/decisions/`. Do not leave an architecture decision only in code, tests, or pull-request discussion.
- New exemptions must identify the source-to-target dependency, explain why it exists, link a removal issue, name an owner, and state removal criteria.
- Removing an exemption must update this guidance or its ADR when it changes a documented boundary or decision.
- Treat an architecture-test failure as design feedback: fix the dependency, revise the documented boundary with evidence, or add a narrow, tracked exemption.
- During review, confirm that this document, the architecture tests, C4 documentation, and ADRs agree.

## Review Checklist

- Does new code keep domain policy framework- and adapter-free?
- Does a route delegate instead of embedding business workflow?
- Does a service use a port instead of reaching through an adapter where a port exists?
- Does frontend browser code avoid server/database imports?
- Does the change add a behavior-focused test for new domain or application behavior?
- Does an architecture exemption identify one known legacy edge and include a removal path?
- Does the change create, revise, or supersede an ADR in `docs/architecture/decisions/`?
