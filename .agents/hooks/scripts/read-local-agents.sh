#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
agents_dir="$(cd "$script_dir/../.." && pwd)"
local_agents="$agents_dir/local/AGENTS.local.md"

if [[ ! -f "$local_agents" ]]; then
  exit 0
fi

cat <<EOF
--- BEGIN .agents/local/AGENTS.local.md ---
$(cat "$local_agents")
--- END .agents/local/AGENTS.local.md ---
EOF
