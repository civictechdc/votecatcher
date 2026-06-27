#!/usr/bin/env bash
# Wrapper around read-local-agents.sh that outputs JSON for hook platforms.
# Claude Code and Codex accept plain stdout as developer context.
# VS Code requires JSON with hookSpecificOutput.additionalContext.
# This wrapper produces JSON so a single config works across all platforms.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output="$("$script_dir/read-local-agents.sh" 2>/dev/null || true)"

if [[ -z "$output" ]]; then
  exit 0
fi

if command -v jq &>/dev/null; then
  escaped=$(printf '%s' "$output" | jq -Rs .)
elif command -v python3 &>/dev/null; then
  escaped=$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$output")
else
  escaped="\"$(printf '%s' "$output" | sed 's/\\/\\\\/g; s/"/\\"/g; s/$/\\n/' | tr -d '\n')\""
fi

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$escaped"
