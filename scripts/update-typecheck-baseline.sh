#!/usr/bin/env bash
set -euo pipefail

BASELINE_FILE="backend/typecheck-baseline.json"

echo "Running basedpyright and capturing errors..."
TMPFILE=$(mktemp /tmp/basedpyright-XXXXXX.json)
trap "rm -f $TMPFILE" EXIT

(cd backend && uv run basedpyright --outputjson 2>/dev/null) >"$TMPFILE"

python3 -c "
import json

data = json.load(open('$TMPFILE'))
errors_by_file = {}
for d in data.get('generalDiagnostics', []):
    if d['severity'] == 'error':
        key = f\"{d['file']}:{d['range']['start']['line']+1}:{d['range']['start']['character']}\"
        errors_by_file[key] = d['message']

output = {'count': len(errors_by_file), 'errors': errors_by_file}
json.dump(output, open('$BASELINE_FILE', 'w'), indent=2)

old_count = 0
try:
    old = json.load(open('$BASELINE_FILE'))
    old_count = old.get('count', 0)
except:
    pass

print(f'Baseline updated: {len(errors_by_file)} errors written to $BASELINE_FILE')
"

echo "Done. Commit the updated baseline file."
