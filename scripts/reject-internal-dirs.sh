#!/usr/bin/env bash
set -euo pipefail

staged=$(git diff --cached --name-only)

rejected=$(echo "$staged" | grep -E '^(\.agent-workspace|\.chainlink|\.crosslink)/' || true)

if [ -n "$rejected" ]; then
	echo "ERROR: Internal directory files must not be committed:"
	echo "$rejected" | sed 's/^/  /'
	echo ""
	echo "These directories are for local agent/tool use only."
	exit 1
fi
