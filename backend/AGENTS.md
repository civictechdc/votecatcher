# VoteCatcher Backend

FastAPI backend for OCR processing, signature validation, matching, campaigns, and persistence.

This file is a backend-specific overlay. Follow `../AGENTS.md` first, including its local-preference hook.

## Read When Relevant

- Project-wide agent rules: `../AGENTS.md`
- Backend setup: `../docs/running-locally.md#backend-setup`
- Architecture or persistence changes: `../docs/architecture/README.md`, `../docs/architecture/decisions/`, `../docs/database/`
- Testing patterns: `../docs/development/testing.md`
- Broad refactors or Python-heavy changes: `../docs/agents/code-quality.md`

## Structure

- `app/routers/`: FastAPI routes; keep handlers thin.
- `app/services/`: business workflows and integration logic.
- `app/domain/`: domain value objects and pure rules.
- `app/repositories/` and `app/data/`: persistence and database access.
- `app/matching/`: fuzzy matching and voter data adaptation.
- `app/regions/`: JSON5 regional field specs.
- `alembic/`: schema migrations.
- `tests/`: unit and integration tests.

## Commands

From repo root for quality gates:

- Tests: `just test-backend`
- Lint: `just lint-backend`
- Typecheck: `just typecheck-backend`
- Broad local CI: `just ci-sim`

From `backend/` for focused iteration:

- Install: `uv sync --dev`
- Run API locally: `uv run python main.py --env local`
- Tests: `uv run pytest tests/ -v`
- Single test file or case: `uv run pytest tests/path/to/test_file.py::test_name -v`
- Lint: `uv run ruff check app tests`
- Format: `uv run ruff format app tests`
- Typecheck: `uv run basedpyright app`
- Run migrations: `uv run alembic upgrade head`

## Conventions

- Keep route handlers thin; put business logic in services/domain modules.
- Type annotate public functions and new service/domain helpers.
- Keep API contract changes aligned with `openapi.yaml` and `app/routers/`.
- Add or update Alembic migrations in `alembic/` for schema changes.
- Prefer behavior-focused tests over implementation-detail mocks.
- Use approval tests for large rendered outputs, score matrices, and config/spec snapshots.

## Boundaries

- Do not commit `.env*`, local databases, generated `.received.txt` approval files, or OCR/API secrets.
- Do not put business logic in route handlers; add or reuse a service/domain function instead.
- Do not change schema models without an Alembic migration and relevant tests.
- Do not embed generated skill catalogs or broad reference docs here; link to focused docs instead.

## Skills

Use backend-specific skills only when relevant. Follow the project skill rules in `../AGENTS.md` and `../docs/agents/skills.md`.
