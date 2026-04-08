#!/usr/bin/env bash
set -euo pipefail

BASELINE_FILE="backend/typecheck-baseline.json"

if [ ! -f "$BASELINE_FILE" ]; then
	echo "::error::Baseline file not found: $BASELINE_FILE"
	echo "Run scripts/update-typecheck-baseline.sh to create it."
	exit 1
fi

BASELINE_COUNT=$(python3 -c "import json; print(json.load(open('$BASELINE_FILE'))['count'])")

TMPFILE=$(mktemp /tmp/basedpyright-XXXXXX.json)
trap "rm -f $TMPFILE" EXIT

(cd backend && uv run basedpyright --outputjson 2>/dev/null) >"$TMPFILE"

ACTUAL_COUNT=$(python3 -c "
import json
data = json.load(open('$TMPFILE'))
errors = [d for d in data.get('generalDiagnostics', []) if d['severity'] == 'error']
print(len(errors))
")

if [ "$ACTUAL_COUNT" -gt "$BASELINE_COUNT" ]; then
	echo "::error::$ACTUAL_COUNT type errors (baseline: $BASELINE_COUNT). Run 'scripts/update-typecheck-baseline.sh' to accept new baseline."
	exit 1
fi

if [ "$ACTUAL_COUNT" -lt "$BASELINE_COUNT" ]; then
	echo "Improved! $ACTUAL_COUNT errors (baseline: $BASELINE_COUNT). Run 'scripts/update-typecheck-baseline.sh' to lock in the improvement."
fi

echo "Typecheck baseline check passed: $ACTUAL_COUNT <= $BASELINE_COUNT"
