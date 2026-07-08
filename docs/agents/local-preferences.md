# Local Agent Preferences

VoteCatcher supports optional machine-local agent preferences at either path:

```text
AGENTS.local.md
.agents/local/AGENTS.local.md
```

Both paths are gitignored. They are for local workstation preferences that should not affect the team or CI.

## Required Agent Behavior

Immediately after reading root `AGENTS.md`, run:

```bash
.agents/hooks/scripts/read-agents.sh --plain
```

The script outputs root `AGENTS.md`, then `AGENTS.local.md` if it exists, then `.agents/local/AGENTS.local.md` if it exists. Because both local preference paths are gitignored, use CLI/file-search tools rather than relying on tracked file lists.

If the local file exists, treat its output as machine-local agent preferences before starting active work.

## Appropriate Content

Keep local preferences limited to machine-specific or user-specific details:

- Preferred local commands or aliases.
- Local service ports.
- Machine-specific paths.
- Personal editor or terminal preferences.

Do not put project-wide conventions, security-sensitive secrets, or durable team knowledge here. Project-wide lessons belong in `AGENTS.md` or `docs/agents/` through the self-learning PR process.
