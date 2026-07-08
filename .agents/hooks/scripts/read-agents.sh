#!/usr/bin/env bash
# read-agents.sh — Session-start hook that guarantees the agent sees root
# AGENTS.md followed by machine-local agent preferences.
#
# Default output is JSON with hookSpecificOutput.additionalContext for
# cross-platform compatibility (Claude Code, VS Code, Cursor, Codex, Pi).
# Use --plain for raw text output (direct execution, OpenCode plugin).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
agents_dir="$(cd "$script_dir/../.." && pwd)"
project_root="$(cd "$agents_dir/.." && pwd)"

sections=()

# 1. Root AGENTS.md — sibling of .agents/, guarantee the agent reads it
root_agents="$project_root/AGENTS.md"
if [[ -f "$root_agents" ]]; then
  sections+=("$(cat "$root_agents")")
fi

# 2. Root-local agent preferences — sibling of AGENTS.md
root_local_agents="$project_root/AGENTS.local.md"
if [[ -f "$root_local_agents" ]]; then
  sections+=("--- BEGIN AGENTS.local.md ---
$(cat "$root_local_agents")
--- END AGENTS.local.md ---")
fi

# 3. Local agent preferences — inside .agents/local/
local_agents="$agents_dir/local/AGENTS.local.md"
if [[ -f "$local_agents" ]]; then
  sections+=("--- BEGIN .agents/local/AGENTS.local.md ---
$(cat "$local_agents")
--- END .agents/local/AGENTS.local.md ---")
fi

if [[ ${#sections[@]} -eq 0 ]]; then
  exit 0
fi

output=""
for i in "${!sections[@]}"; do
  if [[ $i -gt 0 ]]; then
    output+=$'\n\n'
  fi
  output+="${sections[$i]}"
done

# Plain text mode
if [[ "${1:-}" == "--plain" ]]; then
  printf '%s\n' "$output"
  exit 0
fi

# JSON output for hook platforms
if command -v jq &>/dev/null; then
  escaped=$(printf '%s' "$output" | jq -Rs .)
elif command -v python3 &>/dev/null; then
  escaped=$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$output")
else
  escaped="\"$(printf '%s' "$output" | sed 's/\\/\\\\/g; s/"/\\"/g; s/$/\\n/' | tr -d '\n')\""
fi

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$escaped"
