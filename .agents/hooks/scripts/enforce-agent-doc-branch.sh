#!/usr/bin/env bash
set -euo pipefail

branch="$(git branch --show-current 2>/dev/null || true)"

if [[ "$branch" == "docs/concise-agents-md" ]]; then
  exit 0
fi

if [[ "$branch" == agents/* ]]; then
  exit 0
fi

protected_regex='(^|/)(AGENTS\.md)$|^docs/agents/|^\.agents/hooks/'

changed="$(git diff --name-only --cached 2>/dev/null; git diff --name-only 2>/dev/null)"

if printf '%s\n' "$changed" | grep -E "$protected_regex" >/dev/null; then
  cat >&2 <<EOF
Agent instruction files changed outside an agents/<short-topic> branch.

Current branch: ${branch:-unknown}

Protected files require a separate self-learning branch and PR:
- AGENTS.md files
- docs/agents/**
- .agents/hooks/**
EOF
  exit 1
fi
