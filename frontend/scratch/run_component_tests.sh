#!/usr/bin/env bash
# Run component tests only under jsdom environment
npx vitest run src/lib/components/__tests__/PaginatedMatchTable.spec.ts --environment jsdom
