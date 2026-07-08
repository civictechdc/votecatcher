# VoteCatcher

Open source ballot signature recognition for grassroots campaigns.

Stack: Python/FastAPI backend, SvelteKit 5 frontend, SQLModel/Alembic data layer, Docker/just for local workflow.

## Agent Contract

- Be honest and direct. Push back when something seems wrong.
- Flag unclear but important choices before making them.
- Say `I don't know` when evidence is missing.
- Start with `❗️` when calling out a likely error, miss, or risk.
- Do not invent project facts. Read the source or docs first.

## First Reads

- After reading this file, run `.agents/hooks/scripts/read-agents.sh --plain` to load any machine-local preferences from `AGENTS.local.md` or `.agents/local/AGENTS.local.md`.
- For project overview, read `README.md`.
- For setup and commands, read `docs/development/README.md` and `docs/running-locally.md`.
- For architecture changes, read `docs/architecture/README.md` and relevant ADRs in `docs/architecture/decisions/`.
- For project layout, read `docs/architecture/project-structure.md`.

## Core Commands

- List tasks: `just`
- Install dependencies: `just install`
- Run all tests: `just test`
- Lint: `just lint`
- Typecheck: `just typecheck`
- Local CI simulation: `just ci-sim`

Prefer narrower package commands while iterating, then run the broader check before claiming completion.

## Sources Of Truth

| Topic | Source |
| --- | --- |
| Product overview | `README.md` |
| Local development | `docs/development/README.md`, `docs/running-locally.md` |
| Architecture | `docs/architecture/` |
| Project structure | `docs/architecture/project-structure.md` |
| API contract | `backend/openapi.yaml`, `backend/app/routers/` |
| Database schema | `docs/database/`, `backend/alembic/` |
| Testing | `docs/development/testing.md` |
| Versioning | `docs/development/versioning.md` |

## Agent-Specific Guidance

- Code quality: `docs/agents/code-quality.md`
- Version and changelog work: `docs/agents/versioning.md`
- Frontend/Svelte MCP: `docs/agents/svelte-mcp.md`
- Local preferences: `docs/agents/local-preferences.md`; loaded by `.agents/hooks/scripts/read-agents.sh` when `AGENTS.local.md` or `.agents/local/AGENTS.local.md` exists.

Read these only when relevant to the current task.

## Skills

`find-skills` is a core project skill. Use it when specialized help may exist.

- Search: `npx skills find <query>` or `bunx skills find <query>`
- Inspect options before installing.
- Install project skills for Universal:
  `npx skills add <source> --skill <skill-name> -a universal -y`

Do not embed generated skill catalogs in `AGENTS.md`.

## Self-Learning

At task end, if you discovered a durable project-specific rule, pitfall, command, convention, or stale instruction, propose a learning update.

Strict filter:
- Keep durable project knowledge likely useful across future sessions.
- Skip task trivia, temporary state, one-off debugging notes, and generic coding advice.

Before editing learning docs:
1. Ask the user first.
2. Create a separate branch named `agents/<short-topic>`.
3. Open a separate PR for the AGENTS/docs-agent update.
4. Do not mix self-learning changes into feature branches.

## Agent Hook Contract

Agent hook scripts live in `.agents/hooks/scripts/`.

Agents must treat these scripts as project contracts. Individual platforms should configure their hook/plugin systems to call the scripts directly.

If changing `AGENTS.md` or `docs/agents/**`, branch name must start with `agents/` unless this is the initial approved rewrite branch.

## Worktree Safety

- You may be in a dirty worktree. Do not revert or overwrite changes you did not make.
- Check `git status --short --branch` before edits and before commits.
- Create focused branches for non-trivial work.
- Commit only when the user asks.
