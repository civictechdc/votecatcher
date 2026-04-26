#!/usr/bin/env bash
# reject-internal-dirs.sh — Pre-commit hook that blocks internal files from being committed.
#
# Reads blocked patterns from .gitblock (gitignore syntax) at the repo root.
# .gitblock itself should be excluded via .git/info/exclude so it's never tracked or pushed.
#
# NOTE on symlinked dirs: Blocked dirs may be symlinks to the bare repo root
# in worktree setups. git-check-ignore cannot resolve paths through symlinks,
# so this hook uses --no-index mode which matches purely on path patterns
# without filesystem resolution.
#
# See --help for full usage.

set -euo pipefail

PROG_NAME="$(basename "$0")"
readonly PROG_NAME

usage() {
	cat <<EOF
Usage: $PROG_NAME [OPTIONS]

Pre-commit hook that blocks files matching patterns in .gitblock from being
committed. Designed for use with pre-commit framework or as a standalone
git hook.

Options:
  -h, --help     Show this help message and exit
  -t, --test     Dry-run: show which staged files would be rejected (exit 0)

Setup:
  1. Create .gitblock at the repo root (gitignore syntax):
       internal-dir/         # block directory
       secrets.json          # block specific file
       *.key                 # block by glob
       !allowed.key          # allowlist exception

  2. Wire into .pre-commit-config.yaml:
       - id: reject-internal-dirs
         name: Reject internal directories
         entry: bash scripts/reject-internal-dirs.sh
         language: system
         pass_filenames: false
         always_run: true

  3. Exclude .gitblock from tracking:
       echo ".gitblock" >> .git/info/exclude

Exit codes:
  0  No blocked files found (or --help, --test)
  1  Blocked files detected in staging area
EOF
}

dry_run=0

while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
			usage
			exit 0
			;;
		-t|--test)
			dry_run=1
			shift
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

staged=$(git diff --cached --name-only)

if [ -z "$staged" ]; then
	exit 0
fi

repo_root="$(git rev-parse --show-toplevel)"
blocked_file="$repo_root/.gitblock"

if [ ! -f "$blocked_file" ]; then
	echo "WARNING: .gitblock not found at $blocked_file, skipping check." >&2
	exit 0
fi

# --no-index: match purely on path patterns, don't consult the index.
# Staged files are in the index, so without --no-index they'd be skipped.
# This also avoids symlink resolution errors for worktree symlinked dirs.
rejected=$(printf '%s' "$staged" | git -c core.excludesFile="$blocked_file" check-ignore --no-index --stdin 2>/dev/null || true)

if [ -z "$rejected" ]; then
	exit 0
fi

if [ "$dry_run" -eq 1 ]; then
	echo "DRY RUN: the following staged files match .gitblock patterns:"
	echo "$rejected" | sed 's/^/  /'
	exit 0
fi

echo "ERROR: Blocked files must not be committed:" >&2
echo "$rejected" | sed 's/^/  /' >&2
echo "" >&2
echo "Blocked patterns are listed in .gitblock" >&2
exit 1
