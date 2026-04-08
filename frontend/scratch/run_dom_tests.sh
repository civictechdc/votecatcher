#!/usr/bin/env bash
set -euo pipefail
# Run component DOM tests and remove scratch folder when done
cd "$(dirname "$0")/.."
# Run the DOM tests
npx vitest run "src/lib/components/__tests__/*.dom.spec.ts"
# If successful, remove scratch directory
cd "$(dirname "$0")"
rm -rf "$(pwd)"
echo "Scratch folder removed"
