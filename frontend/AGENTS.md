# VoteCatcher Frontend

SvelteKit 5 application for VoteCatcher.

## First Reads

- Frontend overview and scripts: `frontend/README.md`
- Project-wide agent rules: `../AGENTS.md`
- Svelte MCP workflow: `../docs/agents/svelte-mcp.md`
- Local development: `../docs/development/README.md`

## Commands

- Install: `bun install`
- Dev server: `bun run dev`
- Unit tests: `bun run test:unit`
- E2E tests: `bun run test:e2e`
- All tests: `bun run test`
- Lint: `bun run lint`
- Format: `bun run fmt`
- Typecheck: `bun run check`

## Conventions

- Use Svelte 5 runes and SvelteKit 2 patterns.
- Prefer existing component and route patterns before adding new abstractions.
- Keep server-only code under `src/lib/server/`.
- Use the Svelte MCP docs before writing or changing Svelte/SvelteKit code.
- Run the Svelte autofixer on changed Svelte code when the MCP server is available.

## Skills

Use frontend-specific skills only when relevant. See `../docs/agents/skills.md`; search with `npx skills find <query>` or `bunx skills find <query>`.
