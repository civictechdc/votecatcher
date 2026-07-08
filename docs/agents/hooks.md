# Agent Hooks

Agent hooks provide deterministic guardrails around agent behavior. Use them for rules that should not rely on prompt-following alone.

## Project Contract

- Canonical hook scripts live in `.agents/hooks/scripts/`.
- Agents must treat these scripts as project contracts.
- Platform-specific hook configs call these scripts directly.
- Review hook scripts before enabling them. Hooks run with local user permissions.

## AGENTS Bootstrap

At session start, the hook script outputs root `AGENTS.md` followed by any machine-local preferences from `AGENTS.local.md`, then `.agents/local/AGENTS.local.md`:

```bash
.agents/hooks/scripts/read-agents.sh
```

The script outputs JSON by default (for hook platforms). Use `--plain` for direct execution.

## Self-Learning Branch Guard

Any branch that changes `AGENTS.md` or files under `docs/agents/` must be named `agents/<short-topic>`.

This keeps self-learning updates separate from feature work and makes review intent clear.

Expected script:

```bash
.agents/hooks/scripts/enforce-agent-doc-branch.sh
```

The script should fail when staged or modified agent instruction files are present and the current branch does not start with `agents/`.

## Portable Pattern

There is no single hook config schema that all agents consume. Hook behavior is portable through shared scripts, not shared JSON.

Use this pattern:

1. Put enforcement logic in `.agents/hooks/scripts/`.
2. Configure each agent platform to call the shared scripts from its own hook mechanism.
3. If a platform is not covered here, consult that platform's hook/plugin documentation and set up equivalent calls to the same scripts.
4. If a platform does not support hooks, agents must manually run the relevant script before editing protected files.

## Platform Configs

Default hook configs ship in the repo so each platform loads root `AGENTS.md` and local agent preferences at session start:

| Platform | Config file | Event |
| --- | --- | --- |
| Claude Code | `.claude/settings.json` | `SessionStart` |
| VS Code | `.claude/settings.json` (shared) | `SessionStart` |
| Cursor | `.cursor/hooks.json` | `sessionStart` |
| Codex | `.codex/hooks.json` | `SessionStart` |
| OpenCode | `.opencode/plugins/local-agents.js` | `session.created` |
| Pi | `.pi/hook/hooks.yaml` | `session.created` |

All platform hooks call `.agents/hooks/scripts/read-agents.sh`, which outputs root `AGENTS.md` plus local preferences as JSON for cross-platform compatibility.

Platform hook documentation:

- Claude Code: https://code.claude.com/docs/en/hooks
- VS Code: https://code.visualstudio.com/docs/agent-customization/hooks
- Cursor: https://cursor.com/docs/hooks
- Codex: https://developers.openai.com/codex/hooks
- OpenCode: https://opencode.ai/docs/plugins/
- Pi: https://pi.dev/packages/pi-yaml-hooks

Do not add a generic `.agents/hooks.json`; project-owned behavior lives in scripts, not a shared manifest.

## Branch Guard Adapter Example

To enforce the self-learning branch rule, wire `enforce-agent-doc-branch.sh` into each platform's pre-edit hook. Example for Claude Code:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.agents/hooks/scripts/enforce-agent-doc-branch.sh"
          }
        ]
      }
    ]
  }
}
```

## Manual Fallback

If hook integration is unavailable, agents must run the AGENTS bootstrap script immediately after reading root `AGENTS.md`:

```bash
.agents/hooks/scripts/read-agents.sh --plain
```

Agents must also run this before editing or committing agent instruction files:

```bash
.agents/hooks/scripts/enforce-agent-doc-branch.sh
```

Protected files:

- `AGENTS.md`
- `frontend/AGENTS.md`
- `backend/AGENTS.md`
- `docs/agents/**`
- `.agents/hooks/**`
