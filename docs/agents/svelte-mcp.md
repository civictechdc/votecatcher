# Svelte MCP Workflow

Use this when working in `frontend/` on Svelte or SvelteKit code and the Svelte MCP server is available.

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
