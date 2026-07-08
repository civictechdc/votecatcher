# VoteCatcher Frontend

SvelteKit 2 / Svelte 5 application for VoteCatcher.

## First Reads

- Frontend overview and scripts: `README.md`
- Project-wide agent rules: `../AGENTS.md`
- Svelte MCP workflow: `../docs/agents/svelte-mcp.md`
- Local development: `../docs/development/README.md`

## Commands

- Install: `bun install`
- Dev server: `bun run dev`
- Build: `bun run build`
- Unit tests: `bun run test:unit`
- E2E tests: `bun run test:e2e`
- All tests: `bun run test`
- Lint: `bun run lint`
- Fix lint: `bun run lint:fix`
- Format: `bun run fmt`
- Check format: `bun run fmt:check`
- Typecheck: `bun run check`

## Tooling

- Prefer Bun in `frontend/`: `bun install`, `bun run <script>`, `bunx <package> <command>`.
- Do not replace SvelteKit/Vite, Vitest, or Playwright with generic Bun server/test patterns.
- Do not add `dotenv` for frontend scripts unless existing project code requires it; Bun loads `.env` automatically.

## Conventions

- Use Svelte 5 runes and SvelteKit 2 patterns.
- Prefer existing component and route patterns before adding new abstractions.
- Keep server-only code under `src/lib/server/`.
- Keep TypeScript, Tailwind CSS v4, Better Auth, Drizzle, Vitest, and Playwright aligned with existing project patterns.

## Svelte MCP

Use this workflow for Svelte or SvelteKit tasks when the Svelte MCP server is available:

1. Call `list-sections` first.
2. Inspect returned titles, paths, and `use_cases`.
3. Call `get-documentation` for every relevant section before writing code.
4. Run `svelte-autofixer` on changed Svelte code until it reports no issues or suggestions.
5. Ask before creating a `playground-link`; never create one for code already written to project files.

## Skills

Use frontend-specific skills only when relevant. See `../docs/agents/skills.md`; search with `bunx skills find <query>` from `frontend/`.
