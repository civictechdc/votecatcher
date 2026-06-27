# Agent Hooks

Agent hooks provide deterministic guardrails around agent behavior. Use them for rules that should not rely on prompt-following alone.

## Project Contract

- Canonical hook scripts live in `.agents/hooks/scripts/`.
- Agents must treat these scripts as project contracts.
- Platform-specific hook configs call these scripts directly.
- Review hook scripts before enabling them. Hooks run with local user permissions.

## Local AGENTS Bootstrap

After reading root `AGENTS.md`, agents must immediately run:

```bash
.agents/hooks/scripts/read-local-agents.sh
```

This script checks the sibling `.agents/local/` directory for `AGENTS.local.md`. If present, it prints the file so the agent can load machine-local preferences without committing them.

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

## Platform Setup Docs

Use each platform's supported hook/plugin system and point it at these scripts:

- VS Code hooks: https://code.visualstudio.com/docs/agent-customization/hooks
- OpenCode plugins: https://opencode.ai/docs/plugins/
- Cursor hooks: https://cursor.com/docs/hooks
- Codex hooks: https://developers.openai.com/codex/hooks
- Claude Code hooks: https://code.claude.com/docs/en/hooks

Do not add a generic `.agents/hooks.json`; project-owned behavior lives in scripts, not a shared manifest.

## Claude Code Adapter Example

Claude Code stores hooks under the `hooks` key in `.claude/settings.json` or `~/.claude/settings.json`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": ".agents/hooks/scripts/enforce-agent-doc-branch.sh"
          }
        ]
      }
    ]
  }
}
```

## OpenCode Adapter Example

OpenCode hook support may vary by version. If using `~/.config/opencode/hooks.json`, call the same script from the relevant pre-edit or stop event supported by that version.

```json
{
  "stop": [
    {
      "command": ".agents/hooks/scripts/enforce-agent-doc-branch.sh"
    }
  ]
}
```

## Manual Fallback

If hook integration is unavailable, agents must run the local preferences hook immediately after reading root `AGENTS.md`:

```bash
.agents/hooks/scripts/read-local-agents.sh
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
