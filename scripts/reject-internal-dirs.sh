#!/usr/bin/env bash
set -euo pipefail

staged=$(git diff --cached --name-only)

# Allow CI-managed benchmarks through — these are tracked artifacts, not local state
rejected=$(echo "$staged" | grep -E '^(\.agent-workspace|\.chainlink|\.crosslink)/' | grep -v '^\.agent-workspace/changelog-samples/benchmarks/' || true)

if [ -n "$rejected" ]; then
	echo "ERROR: Internal directory files must not be committed:"
	echo "$rejected" | sed 's/^/  /'
	echo ""
	echo "These directories are for local agent/tool use only."
	exit 1
fi
