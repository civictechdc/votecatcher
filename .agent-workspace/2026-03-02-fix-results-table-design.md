# Fix Results Table - Design Document

**Date:** 2026-03-02
**Status:** Approved
**Author:** Agent + User

## Overview

Fix the results table display in the OCR/voter matching workflow. The current implementation has a broken assignment at line 153-154 and results display out of order. Add pagination, simulation capability, and proper testing.

## Problem Statement

- Results table displays columns out of order (not respecting `position_idx`)
- Incomplete code at `+page.svelte` lines 146-154: `onOcrJobCompleted()` has incomplete `matchResults =` assignment and uses wrong type (`MatchRowEntryResponse` instead of `MatchResultResponse`)
- No pagination for large result sets
- No way to test UI without running full OCR pipeline
- No automated tests for this critical workflow

**Pre-existing Issues (Out of Scope):**
- LSP errors in `ocr_route.py`: `provider_config` possibly unbound, duplicate `get_batch_result` function name - these should be fixed separately

## Goals

1. Fix column ordering to respect `position_idx` from backend
2. Add client-side pagination with configurable sizes (10, 25, 50, 100)
3. Add simulation capability (backend + frontend) for testing
4. Add unit tests with mocks for backend components
5. Maintain existing CSS theming from legacy frontend
6. Add comprehensive lint/type/format checking
7. Create Docker/DevContainer setup for easy onboarding

## Non-Goals

- Full API layer refactor (defer to future work)
- Server-side pagination (client-side sufficient for current dataset sizes)
- Database schema changes (not required for this fix)

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Run Match   │───▶│ SSE Monitor  │───▶│ Results Table │  │
│  │ Button      │    │ (progress)   │    │ (paginated)   │  │
│  └─────────────┘    └──────────────┘    └───────┬───────┘  │
│                                                │            │
│                     ┌──────────────────────────┼──────────┐ │
│                     │ Simulation Toggle?       │          │ │
│                     └────────────┬─────────────┘          │ │
│                                  │                        │
└──────────────────────────────────┼────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
┌─────────────────────────────┐   ┌───────────────────────────┐
│  /ocr/results/demo/{id}     │   │  /ocr/simulate/{id}       │
│  (real OCR + matching)      │   │  (mock data)              │
└─────────────────────────────┘   └───────────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │  MatchResultResponse        │
                    │  (Backend format)           │
                    │  {                          │
                    │    column_data: [...],      │
                    │    result_data: [...]       │
                    │  }                          │
                    └──────────────┬──────────────┘
                                   │
                                   ▼ convertMatchResponseToMatchResults()
                                   │
                    ┌──────────────┴──────────────┐
                    │  MatchResults               │
                    │  (Frontend format)          │
                    │  {                          │
                    │    matchColumns: [...],     │
                    │    matchRecords: [...]      │
                    │  }                          │
                    └─────────────────────────────┘
```

### Data Format Conversion

**Important:** The frontend uses a different data structure than the backend.

| Backend (`MatchResultResponse`) | Frontend (`MatchResults`) |
|--------------------------------|---------------------------|
| `column_data` | `matchColumns` |
| `result_data` | `matchRecords` |

**Conversion Function:** `$lib/utils.ts` → `convertMatchResponseToMatchResults()`

This function:
1. Maps `column_data` to `matchColumns` with sorting functions
2. Maps `result_data` to `matchRecords` as key-value pairs
3. Already exists and is imported in the workspace page

**Implementation Note:** Task 6.2 must use this converter:

```typescript
// Correct usage in onOcrJobCompleted():
const res = await matchApi.getMatchResults({ campaign_id: "demo", job_id: jobId });
if (!res.ok) throw new Error(`Server returned ${res.status}`);
matchResults = convertMatchResponseToMatchResults(res.data);
```

## Design Decisions

### 1. Client-Side Pagination

**Decision:** Implement client-side pagination with configurable page sizes.

**Rationale:**
- Petition matching typically produces hundreds to low thousands of rows
- Client-side pagination is simpler and requires no API changes
- Can be upgraded to server-side later if needed

**Alternatives Considered:**
- Server-side pagination: More complex, requires API changes, overkill for current scale
- Infinite scroll: Harder to navigate, users prefer page-based for data tables

### 2. Minimal API Layer Changes

**Decision:** Add only `simulateOcrResults()` method, defer full refactor.

**Rationale:**
- Existing `client.ts` and `matching-requests.ts` work correctly
- Response types already have `position_idx` support
- Full refactor is out of scope for this fix

### 3. OKLCH Color Space + Semantic Tokens

**Decision:** Adopt legacy frontend's design system with OKLCH colors and semantic tokens.

**Rationale:**
- Consistency across frontends during transition period
- OKLCH provides better perceptual uniformity
- Semantic tokens enable easy theming and dark mode

### 4. Unit Tests with Mocks

**Decision:** Use unit tests with mocked dependencies for backend.

**Rationale:**
- Fast execution
- No test database required
- Tests are deterministic and isolated
- Approval tests would add complexity without clear benefit

## Component Specifications

### Backend: Response Adapter Fix

**File:** `backend/app/matching/response_adapter.py`

**Change:** Sort `column_data` by `position_idx` before returning.

```python
# Ensure columns are ordered correctly
column_data.sort(key=lambda col: col.position_idx)
```

### Backend: Simulate Endpoint

**File:** `backend/app/routers/ocr_route.py`

**Endpoint:** `GET /workspace/ocr/simulate/{task_id}`

**Response:** Same schema as `/ocr/results/demo/{task_id}`

**Behavior:**
- Generate 50-200 mock rows using Faker
- Return realistic voter names, addresses, dates
- Include match confidence scores
- No database or OCR operations

### Frontend: Pagination Component

**File:** `frontend-svelt/src/lib/components/Pagination.svelte`

**Props:**
```typescript
interface PaginationProps {
  totalItems: number;
  pageSize: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}
```

**Features:**
- Page size selector: 10, 25, 50, 100
- Current page indicator
- Previous/Next buttons
- Total count display

### Frontend: Design Tokens

**File:** `frontend-svelt/src/lib/styles/tokens.css`

**Key Tokens:**
- `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`
- `--background`, `--foreground`, `--card`, `--border`
- `--radius`, `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`
- Dark mode variants under `.dark` class

### Frontend: Utility Function

**File:** `frontend-svelt/src/lib/utils/cn.ts`

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Testing Strategy

### Backend Tests

**File:** `backend/tests/matching/test_response_adapter.py`

| Test | Description |
|------|-------------|
| `test_column_data_sorted_by_position_idx` | Verify columns are ordered |
| `test_column_data_contains_all_required_fields` | Schema validation |
| `test_result_data_matches_column_order` | Row values align with columns |
| `test_response_serializes_to_valid_json` | JSON serialization |

**File:** `backend/tests/routers/test_ocr_simulate.py`

| Test | Description |
|------|-------------|
| `test_simulate_returns_200` | Endpoint responds |
| `test_simulate_returns_valid_schema` | Response matches OcrMatchResults |
| `test_simulate_column_data_has_correct_position_idx` | Columns are indexed |
| `test_simulate_result_count_in_expected_range` | 50-200 rows |
| `test_simulate_no_database_calls_made` | Mock verification |

### Frontend Tests

**File:** `frontend-svelt/src/lib/components/Pagination.test.ts`

| Test | Description |
|------|-------------|
| `test_renders_page_size_selector` | UI element exists |
| `test_renders_current_page_indicator` | Page number shown |
| `test_onPageChange_called_on_click` | Event handling |
| `test_onPageSizeChange_called_on_select` | Dropdown works |
| `test_displays_total_count_correctly` | Count accurate |

## Verification Commands

### Lint/Type/Format

| Check | Command |
|-------|---------|
| Python type check | `cd backend && uv run basedpyright app/` |
| Python lint | `cd backend && uv run ruff check app/` |
| Python format | `cd backend && uv run ruff format app/ --check` |
| JS/TS type check | `cd frontend-svelt && bun run check` |
| JS/TS lint | `cd frontend-svelt && bun run lint` |
| JS/TS format | `cd frontend-svelt && bun run fmt:check` |

### Tests

| Check | Command |
|-------|---------|
| Backend tests | `cd backend && uv run pytest tests/matching/ tests/routers/test_ocr_simulate.py -v` |
| Frontend tests | `cd frontend-svelt && bun run test:unit --run` |

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | Python type check passes | `cd backend && uv run basedpyright app/` |
| 2 | Python lint passes | `cd backend && uv run ruff check app/` |
| 3 | Python format check passes | `cd backend && uv run ruff format app/ --check` |
| 4 | All backend tests pass | `cd backend && uv run pytest tests/matching/ tests/routers/test_ocr_simulate.py -q` |
| 5 | Frontend type check passes | `cd frontend-svelt && bun run check` |
| 6 | Frontend lint passes | `cd frontend-svelt && bun run lint` |
| 7 | Frontend format check passes | `cd frontend-svelt && bun run fmt:check` |
| 8 | All frontend tests pass | `cd frontend-svelt && bun run test:unit --run` |
| 9 | Simulate endpoint exists | `grep -q "simulate" backend/app/routers/ocr_route.py` |
| 10 | Pagination component exists | `test -f frontend-svelt/src/lib/components/Pagination.svelte` |
| 11 | No incomplete code | `! grep -q "^matchResults =$" frontend-svelt/src/routes/workspace/[id]/+page.svelte` |

## File Changes Summary

### Phase 1: Backend

| File | Action |
|------|--------|
| `app/matching/response_adapter.py` | Modify - add column sort |
| `app/routers/ocr_route.py` | Modify - add simulate endpoint |
| `tests/matching/test_response_adapter.py` | Create |
| `tests/routers/test_ocr_simulate.py` | Create |

### Phase 2: Frontend Styles

| File | Action |
|------|--------|
| `src/lib/styles/tokens.css` | Create - design tokens |
| `src/lib/utils/cn.ts` | Create - class merge utility |

### Phase 3: Frontend Components

| File | Action |
|------|--------|
| `src/lib/components/Pagination.svelte` | Create |

### Phase 4: Frontend Page

| File | Action |
|------|--------|
| `src/routes/workspace/[id]/+page.svelte` | Modify - fix, add pagination, add toggle |

### Phase 5: API Layer

| File | Action |
|------|--------|
| `src/lib/api/client.ts` | Modify - add simulateOcrResults() |
| `src/lib/api/request-types.ts` | Modify - add SimulateOcrPayload |

### Phase 6: Documentation

| File | Action |
|------|--------|
| `docs/running-locally.md` | Create |

### Phase 7: Verification

| File | Action |
|------|--------|
| `scripts/verify-fix-results.sh` | Create |

### Phase 8: Docker/DevContainer (Post-Main)

| File | Action |
|------|--------|
| `docker-compose.yml` | Create |
| `backend/Dockerfile` | Create |
| `backend/.dockerignore` | Create |
| `frontend-svelt/Dockerfile` | Create |
| `frontend-svelt/.dockerignore` | Create |
| `.devcontainer/devcontainer.json` | Create |
| `.devcontainer/setup.sh` | Create |
| `.devcontainer/README.md` | Create |

## Run Commands

### Backend

```bash
cd backend
uv run main.py --env local   # Local development (.env.local)
uv run main.py --env debug   # Debug mode (.env.local)
uv run main.py --env dev     # Development (.env.dev)
uv run main.py --env prod    # Production (.env.prod)
```

### Backend Tests

```bash
cd backend
uv run pytest                              # Run all tests
uv run pytest tests/ -v                    # Verbose output
uv run pytest --cov=app                    # With coverage
uv run pytest tests/matching/ -v           # Specific module
```

### Frontend

```bash
cd frontend-svelt
bun run dev          # Development server
bun run build        # Production build
bun run check        # Type check
bun run lint         # Lint check
bun run fmt:check    # Format check
bun run test:unit    # Unit tests
bun run test:e2e     # E2E tests
```

## Docker/DevContainer

### Quick Start (DevContainer)

1. Open repository in VS Code
2. Click "Reopen in Container" when prompted
3. Run: `.devcontainer/setup.sh`
4. Start backend: `cd backend && uv run main.py --env local`
5. Start frontend: `cd frontend-svelt && bun run dev`

### Docker Compose

```bash
docker-compose up -d        # Start all services
docker-compose down -v      # Stop and cleanup
docker-compose logs -f      # View logs
```

### Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8080 | http://localhost:8080 |
| Backend Docs | 8080 | http://localhost:8080/docs |
| PostgreSQL | 5432 | localhost:5432 |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Run all existing tests before/after changes |
| CSS theming inconsistencies | Use exact tokens from legacy frontend |
| Test flakiness | Use deterministic mocks, avoid timing-dependent tests |
| Docker build failures | Multi-stage builds, proper .dockerignore |

## Future Work

- Server-side pagination for large datasets (>10k rows)
- Full API layer consolidation
- E2E tests for complete workflow
- Dark mode toggle in UI
- Performance monitoring for OCR pipeline

---

## Notes for Implementers

### Token Efficiency

When executing the implementation plan:
- Read only necessary portions of large files (use `limit` parameter)
- Use grep/glob to locate code rather than reading entire files
- Keep progress updates concise
- Reference existing code by path/line rather than duplicating

### Key Reference Files

| Purpose | File |
|---------|------|
| Data conversion | `frontend-svelt/src/lib/utils.ts` |
| Response types | `frontend-svelt/src/lib/api/response-types.ts` |
| Workspace types | `frontend-svelt/src/lib/workspace-types.ts` |
| Match API | `frontend-svelt/src/lib/api/matching-requests.ts` |
| Page to fix | `frontend-svelt/src/routes/workspace/[id]/+page.svelte` |
