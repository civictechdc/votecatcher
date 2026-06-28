#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  set -- AGENTS.md frontend/AGENTS.md backend/AGENTS.md docs/agents
fi

pattern='<skills_system|<available_skills|SKILLS_TABLE_START'

if grep -R -n -E "$pattern" "$@" 2>/dev/null; then
  echo "BLOCK: generated agent catalog markers found" >&2
  exit 1
fi

echo "CONTINUE: no generated agent catalog markers found"
