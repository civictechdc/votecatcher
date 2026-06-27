# Local Agent Preferences

VoteCatcher supports optional machine-local agent preferences at:

```text
.agents/local/AGENTS.local.md
```

This path is gitignored. It is for local workstation preferences that should not affect the team or CI.

## Required Agent Behavior

Immediately after reading root `AGENTS.md`, run:

```bash
.agents/hooks/scripts/read-local-agents.sh
```

The script checks for `.agents/local/AGENTS.local.md` by locating the sibling `.agents/local/` directory relative to `.agents/hooks/scripts/`. Because `.agents/local/` is gitignored, use CLI/file-search tools rather than relying on tracked file lists.

If the file exists, the script prints it. Treat that output as machine-local agent preferences before starting active work.

## Appropriate Content

Keep local preferences limited to machine-specific or user-specific details:

- Preferred local commands or aliases.
- Local service ports.
- Machine-specific paths.
- Personal editor or terminal preferences.

Do not put project-wide conventions, security-sensitive secrets, or durable team knowledge here. Project-wide lessons belong in `AGENTS.md` or `docs/agents/` through the self-learning PR process.
