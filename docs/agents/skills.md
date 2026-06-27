# Agent Skills

`find-skills` is a core project skill. Use it when specialized help may exist.

## Commands

- Search: `npx skills find <query>`
- Search with Bun if preferred: `bunx skills find <query>`
- List installed skills: `npx skills list`
- Inspect repository skills without installing: `npx skills add <source> --list`
- Install project skills for Universal: `npx skills add <source> --skill <skill-name> -a universal -y`

## Rules

- Do not embed generated skill catalogs in `AGENTS.md`.
- Prefer project installs with `-a universal` so skills land under `.agents/skills/`.
- Additional platform-specific installs may be appended as machine-local preference in `.agents/local/AGENTS.local.md`.
- Inspect skill quality before installing: source reputation, install count, repository health, and relevance.
- Ask before installing new skills unless the user explicitly requested installation.
