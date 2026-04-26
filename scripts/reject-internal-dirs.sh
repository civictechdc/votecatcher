#!/usr/bin/env bash
# reject-internal-dirs.sh — Pre-commit hook that blocks internal files from being committed.
#
# Reads blocked patterns from .gitblock (gitignore syntax) at the repo root.
# .gitblock itself is excluded via .git/info/exclude so it's never tracked or pushed.
#
# Usage:
#   1. Add patterns to .gitblock (same format as .gitignore):
#        internal-dir/         # block directory
#        secrets.json         # block specific file
#        *.key                # block by glob
#        !allowed.key         # allowlist exception
#
#   2. Wire into .pre-commit-config.yaml:
#        - id: reject-internal-dirs
#          name: Reject internal directories
#          entry: bash scripts/reject-internal-dirs.sh
#          language: system
#          pass_filenames: false
#          always_run: true
#
#   3. Ensure .gitblock is excluded from tracking:
#        echo ".gitblock" >> .git/info/exclude
#
set -euo pipefail

staged=$(git diff --cached --name-only)

if [ -z "$staged" ]; then
	exit 0
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
blocked_file="$script_dir/../.gitblock"

if [ ! -f "$blocked_file" ]; then
	echo "WARNING: .gitblock not found, skipping internal dir check."
	exit 0
fi

abs_blocked="$(cd "$(dirname "$blocked_file")" && pwd)/$(basename "$blocked_file")"

rejected=$(printf '%s' "$staged" | git -c core.excludesFile="$abs_blocked" check-ignore --stdin 2>/dev/null || true)

if [ -n "$rejected" ]; then
	echo "ERROR: Blocked files must not be committed:"
	echo "$rejected" | sed 's/^/  /'
	echo ""
	echo "Blocked patterns are listed in .gitblock"
	exit 1
fi
