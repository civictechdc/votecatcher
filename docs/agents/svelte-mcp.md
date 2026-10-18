# Svelte MCP Workflow

Use this when working in `frontend/` on Svelte or SvelteKit code.

The Svelte MCP server (`@sveltejs/mcp`, local stdio via `npx -y`) is wired in committed config:

- OpenCode: `opencode.jsonc` at the repo root (project-level config, `mcp.servers.svelte`).
- VS Code and compatible tools: `.mcp.json` at the repo root (portable format, top-level `mcpServers`); read by VS Code, Copilot harness sessions, and compatible tools like Claude Code.

Two skills are installed under `.agents/skills/`: load `svelte-code-writer` when creating, editing, or analyzing `.svelte` / `.svelte.ts` files, and `svelte-core-bestpractices` when writing or reviewing Svelte code.

## Documentation Lookup

1. Call `list-sections` first for Svelte/SvelteKit tasks.
2. Inspect returned titles, paths, and `use_cases`.
3. Call `get-documentation` for every relevant section before writing code.

## Code Validation

- Run `svelte-autofixer` on changed Svelte code.
- Keep applying fixes until it reports no issues or suggestions.

## Playground Links

- Ask before creating a playground link.
- Do not create playground links for code already written to project files.

## CLI Fallback (no MCP session)

When no MCP session is available, the same package works as a CLI:

```sh
npx -y @sveltejs/mcp list-sections
npx -y @sveltejs/mcp get-documentation 'svelte/$state'
npx -y @sveltejs/mcp svelte-autofixer <path-or-code>
```

- `get-documentation` accepts comma-separated sections.
- `svelte-autofixer` supports `--svelte-version` and `--async`.
- Escape `$` as `\$` when passing inline runes through the shell, or prefer passing file paths.
