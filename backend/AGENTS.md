# VoteCatcher Backend

FastAPI backend for OCR processing, signature validation, matching, campaigns, and persistence.

## First Reads

- Project-wide agent rules: `../AGENTS.md`
- Architecture overview: `../docs/architecture/README.md`
- Project structure: `../docs/architecture/project-structure.md`
- Database docs: `../docs/database/README.md`
- Testing guide: `../docs/development/testing.md`

## Commands

- Install: `uv sync --dev`
- Run API locally: `uv run python main.py --env local`
- Tests: `uv run pytest tests/ -v`
- Lint: `uv run ruff check app tests`
- Format: `uv run ruff format app tests`
- Typecheck: `uv run basedpyright app`

## Conventions

- Keep route handlers thin; put business logic in services/domain modules.
- Type annotate new public functions.
- Add or update Alembic migrations for schema changes.
- Prefer behavior-focused tests over implementation-detail mocks.
- Read `../docs/agents/code-quality.md` before broad refactors or Python-heavy changes.

## Skills

Use backend-specific skills only when relevant. See `../docs/agents/skills.md`; search with `npx skills find <query>` or `bunx skills find <query>`.
