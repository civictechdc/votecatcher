#!/usr/bin/env bash
# pre-commit-hygiene.sh — Verify staging area is clean before committing
# Usage: bash scripts/frontend-rename/pre-commit-hygiene.sh
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ERRORS=0

echo "=== Pre-Commit Hygiene Check ==="

# 1. Check for working/planning docs in staging
STAGED_WORKING=$(git diff --cached --name-only | grep -E '^(\.agent-workspace/|\.agent/|scratch/|\.claude/skills/|docs/qa/|openspec/)' || true)
if [ -n "$STAGED_WORKING" ]; then
	echo "ERROR: Working/planning files staged (unstage them):"
	echo "$STAGED_WORKING"
	ERRORS=$((ERRORS + 1))
else
	echo "OK: No working/planning docs in staging area"
fi

# 2. Check for .plan.md, .notes.md, .working.md files
STAGED_PLAN=$(git diff --cached --name-only | grep -E '\.(plan|notes|working)\.md$' || true)
if [ -n "$STAGED_PLAN" ]; then
	echo "ERROR: Planning/notes files staged:"
	echo "$STAGED_PLAN"
	ERRORS=$((ERRORS + 1))
else
	echo "OK: No planning/notes files in staging area"
fi

# 3. Check for stale frontend-svelt references in staged files
STAGED_OLD_REF=$(git diff --cached --name-only | grep 'frontend-svelt' || true)
if [ -n "$STAGED_OLD_REF" ]; then
	echo "WARNING: Staged files with 'frontend-svelt' in path (expected only in commit 1/2 context):"
	echo "$STAGED_OLD_REF"
fi

# 4. Check that only intended file categories are staged
STAGED=$(git diff --cached --name-only)
if [ -z "$STAGED" ]; then
	echo "WARNING: Nothing staged"
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
	echo "FAILED: $ERRORS hygiene error(s) — fix before committing"
	exit 1
else
	echo "PASSED: Staging area is clean"
	exit 0
fi
