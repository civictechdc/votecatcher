# Fix Results Table Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the results table display with proper column ordering, pagination, and simulation capability.

**Architecture:** Backend adds simulate endpoint and fixes column sorting. Frontend adds pagination component, design tokens, and simulation toggle. All changes verified with automated tests and linting.

**Tech Stack:** Python 3.13, FastAPI, pytest, ruff, basedpyright, SvelteKit 5, TypeScript, Tailwind CSS v4, Vitest, oxlint, oxfmt

**Design Doc:** `.agent-workspace/2026-03-02-fix-results-table-design.md`
**Progress Tracker:** `.agent-workspace/PROGRESS.md`

---

## Sample Test Data

When testing the OCR/matching workflow, use these sample files:

| File | Description | Path |
|------|-------------|------|
| Petition PDF (small) | 10 pages of fake signed petitions | `samples/dc/fake_signed_petitions_1-10.pdf` |
| Petition PDF (full) | Full petition dataset | `samples/dc/fake_signed_petitions.pdf` |
| Voter Records CSV | ~100k fake voter records | `samples/dc/fake_voter_records.csv` |

**Voter Records CSV Columns:**
- `First_Name`, `Last_Name`
- `Street_Number`, `Street_Name`, `Street_Type`, `Street_Dir_Suffix`

These files are used to test the full OCR → fuzzy match → results display workflow.

---

## ⚠️ MANDATORY: Progress Tracking

**After completing EACH task, you MUST update the progress tracker:**

```bash
# Read current progress
cat .agent-workspace/PROGRESS.md

# After completing a task, update PROGRESS.md:
# 1. Change task status: Not Started → In Progress → Completed
# 2. Add commit hash if applicable
# 3. Add timestamp and any notes
# 4. Update phase status in Status Overview table
# 5. Update Overall Progress percentage
```

**At checkpoint reviews (end of each phase):**
1. Add entry to Checkpoint Log in PROGRESS.md
2. Verify all tests pass before proceeding
3. Summarize what was accomplished

**This ensures future agents can quickly understand progress and resume work.**

---

## Phase 1: Backend - Response Adapter Fix

### Task 1.1: Write Test for Column Ordering

**Files:**
- Create: `backend/tests/matching/test_response_adapter.py`

**Step 1: Create test file with failing test**

```python
"""Tests for response adapter column ordering."""
import pytest
from app.matching.response_adapter import (
    OcrMatchColumnSpec,
    OcrMatchRow,
    OcrMatchValueItem,
    OcrMatchResults,
)


def test_column_data_sorted_by_position_idx():
    """Column data should be sorted by position_idx."""
    columns = [
        OcrMatchColumnSpec(name="third", position_idx=2, data_type="string"),
        OcrMatchColumnSpec(name="first", position_idx=0, data_type="string"),
        OcrMatchColumnSpec(name="second", position_idx=1, data_type="string"),
    ]
    rows = [
        OcrMatchRow(
            row_idx=0,
            values=[
                OcrMatchValueItem(value="A", column_idx=0, data_type="string"),
                OcrMatchValueItem(value="B", column_idx=1, data_type="string"),
                OcrMatchValueItem(value="C", column_idx=2, data_type="string"),
            ],
        )
    ]
    result = OcrMatchResults(column_data=columns, result_data=rows)
    
    assert result.column_data[0].position_idx == 0
    assert result.column_data[1].position_idx == 1
    assert result.column_data[2].position_idx == 2


def test_column_data_contains_all_required_fields():
    """Column data should contain all required fields."""
    column = OcrMatchColumnSpec(name="test_col", position_idx=0, data_type="string")
    
    assert column.name == "test_col"
    assert column.position_idx == 0
    assert column.data_type == "string"


def test_response_serializes_to_valid_json():
    """Response should serialize to valid JSON."""
    import json
    
    columns = [OcrMatchColumnSpec(name="name", position_idx=0, data_type="string")]
    rows = [
        OcrMatchRow(
            row_idx=0,
            values=[OcrMatchValueItem(value="John", column_idx=0, data_type="string")],
        )
    ]
    result = OcrMatchResults(column_data=columns, result_data=rows)
    
    json_str = result.model_dump_json()
    parsed = json.loads(json_str)
    
    assert "column_data" in parsed
    assert "result_data" in parsed
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/matching/test_response_adapter.py -v
```

Expected: FAIL (columns not sorted)

**Step 3: Read response_adapter.py to understand current implementation**

```bash
cat backend/app/matching/response_adapter.py
```

**Step 4: Implement column sorting in response_adapter.py**

Find the location where `OcrMatchResults` is constructed and add sorting:

```python
# In OcrMatchResults model or where it's returned
# Sort column_data by position_idx before returning
column_data.sort(key=lambda col: col.position_idx)
```

**Step 5: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/matching/test_response_adapter.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
cd backend && git add tests/matching/test_response_adapter.py app/matching/response_adapter.py
git commit -m "fix: ensure column_data is sorted by position_idx in OcrMatchResults"
```

---

## Phase 2: Backend - Simulate Endpoint

### Task 2.1: Write Test for Simulate Endpoint

**Files:**
- Create: `backend/tests/routers/test_ocr_simulate.py`

**Step 1: Create test file**

```python
"""Tests for OCR simulate endpoint."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.api import app
    return TestClient(app)


def test_simulate_returns_200(client):
    """Simulate endpoint should return 200."""
    response = client.get("/workspace/ocr/simulate/test-task-id")
    assert response.status_code == 200


def test_simulate_returns_valid_schema(client):
    """Simulate should return valid OcrMatchResults schema."""
    response = client.get("/workspace/ocr/simulate/test-task-id")
    data = response.json()
    
    assert "column_data" in data
    assert "result_data" in data
    assert isinstance(data["column_data"], list)
    assert isinstance(data["result_data"], list)


def test_simulate_column_data_has_correct_position_idx(client):
    """Column data should have sequential position_idx."""
    response = client.get("/workspace/ocr/simulate/test-task-id")
    data = response.json()
    
    positions = [col["position_idx"] for col in data["column_data"]]
    assert positions == sorted(positions)


def test_simulate_result_count_in_expected_range(client):
    """Should generate between 50-200 rows."""
    response = client.get("/workspace/ocr/simulate/test-task-id")
    data = response.json()
    
    assert len(data["result_data"]) >= 50
    assert len(data["result_data"]) <= 200


def test_simulate_no_database_calls_made(client):
    """Simulate should not make any database calls."""
    with patch("app.routers.ocr_route.OcrResultRepository") as mock_repo:
        response = client.get("/workspace/ocr/simulate/test-task-id")
        
        # Repository should not be instantiated
        mock_repo.assert_not_called()
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/routers/test_ocr_simulate.py -v
```

Expected: FAIL (404 - endpoint not found)

### Task 2.2: Implement Simulate Endpoint

**Files:**
- Modify: `backend/app/routers/ocr_route.py`

**Step 1: Read current ocr_route.py**

```bash
head -100 backend/app/routers/ocr_route.py
```

**Step 2: Add simulate endpoint to ocr_route.py**

Add this new endpoint after the existing routes:

```python
from faker import Faker

@router.get("/ocr/simulate/{task_id}", response_model=OcrMatchResponse)
async def simulate_ocr_results(task_id: str):
    """
    Generate simulated OCR match results for testing.
    
    No database or OCR operations are performed.
    Returns realistic mock data following the OcrMatchResults schema.
    """
    import random
    from app.matching.response_adapter import (
        OcrMatchResults,
        OcrMatchColumnSpec,
        OcrMatchRow,
        OcrMatchValueItem,
    )
    
    fake = Faker()
    random.seed(hash(task_id))  # Deterministic based on task_id
    
    # Define columns
    columns = [
        OcrMatchColumnSpec(name="ocr_name", position_idx=0, data_type="string"),
        OcrMatchColumnSpec(name="ocr_address", position_idx=1, data_type="string"),
        OcrMatchColumnSpec(name="matched_name", position_idx=2, data_type="string"),
        OcrMatchColumnSpec(name="matched_address", position_idx=3, data_type="string"),
        OcrMatchColumnSpec(name="match_score", position_idx=4, data_type="float"),
        OcrMatchColumnSpec(name="ocr_date", position_idx=5, data_type="string"),
        OcrMatchColumnSpec(name="ocr_ward", position_idx=6, data_type="int"),
    ]
    
    # Generate rows
    row_count = random.randint(50, 200)
    rows = []
    
    for i in range(row_count):
        ocr_name = fake.name()
        ocr_address = fake.address().replace("\n", ", ")
        match_score = round(random.uniform(0.5, 1.0), 3)
        
        # Sometimes match is close, sometimes different
        if random.random() > 0.3:
            matched_name = ocr_name
            matched_address = ocr_address
        else:
            matched_name = fake.name()
            matched_address = fake.address().replace("\n", ", ")
        
        values = [
            OcrMatchValueItem(value=ocr_name, column_idx=0, data_type="string"),
            OcrMatchValueItem(value=ocr_address, column_idx=1, data_type="string"),
            OcrMatchValueItem(value=matched_name, column_idx=2, data_type="string"),
            OcrMatchValueItem(value=matched_address, column_idx=3, data_type="string"),
            OcrMatchValueItem(value=str(match_score), column_idx=4, data_type="float"),
            OcrMatchValueItem(value=fake.date(), column_idx=5, data_type="string"),
            OcrMatchValueItem(value=str(random.randint(1, 8)), column_idx=6, data_type="int"),
        ]
        rows.append(OcrMatchRow(row_idx=i, values=values))
    
    result = OcrMatchResults(column_data=columns, result_data=rows)
    
    return OcrMatchResponse(
        results=result,
        stats={
            "total_rows": row_count,
            "simulated": True,
            "task_id": task_id,
        }
    )
```

**Step 3: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/routers/test_ocr_simulate.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
cd backend && git add app/routers/ocr_route.py tests/routers/test_ocr_simulate.py
git commit -m "feat: add /workspace/ocr/simulate/{task_id} endpoint for testing"
```

---

## Phase 3: Backend - Verification

### Task 3.1: Run All Backend Checks

**Step 1: Run type check**

```bash
cd backend && uv run basedpyright app/
```

Expected: 0 errors (or pre-existing errors only)

**Step 2: Run lint**

```bash
cd backend && uv run ruff check app/
```

Expected: No output (exit 0)

**Step 3: Run format check**

```bash
cd backend && uv run ruff format app/ --check
```

Expected: No changes needed

**Step 4: Run all tests**

```bash
cd backend && uv run pytest tests/matching/ tests/routers/test_ocr_simulate.py -v
```

Expected: All PASS

---

## Phase 4: Frontend - Design Tokens

### Task 4.1: Create Design Tokens CSS

**Files:**
- Create: `frontend-svelt/src/lib/styles/tokens.css`

**Step 1: Create styles directory**

```bash
mkdir -p frontend-svelt/src/lib/styles
```

**Step 2: Create tokens.css**

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  /* Radius */
  --radius: 0.625rem;
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);

  /* Light Mode */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.985 0 0);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --destructive-foreground: oklch(0.985 0 0);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
}
```

**Step 3: Import in app.css or +layout.svelte**

Add to `frontend-svelt/src/app.css` or at the top of `frontend-svelt/src/routes/+layout.svelte`:

```svelte
<script lang="ts">
  import '../lib/styles/tokens.css';
  // ... rest of imports
</script>
```

**Step 4: Verify CSS compiles**

```bash
cd frontend-svelt && bun run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/styles/tokens.css
git commit -m "style: add design tokens CSS with OKLCH color space"
```

### Task 4.2: Create CN Utility

**Files:**
- Create: `frontend-svelt/src/lib/utils/cn.ts`

**Step 1: Install dependencies**

```bash
cd frontend-svelt && bun add clsx tailwind-merge
```

**Step 2: Create utils directory**

```bash
mkdir -p frontend-svelt/src/lib/utils
```

**Step 3: Create cn.ts**

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Step 4: Verify type check**

```bash
cd frontend-svelt && bun run check
```

Expected: No errors

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/utils/cn.ts frontend-svelt/package.json frontend-svelt/bun.lock
git commit -m "feat: add cn utility for class merging"
```

---

## Phase 5: Frontend - Pagination Component

### Task 5.1: Write Pagination Component Tests

**Files:**
- Create: `frontend-svelt/src/lib/components/Pagination.test.ts`

**Step 1: Create test file**

```typescript
import { render, fireEvent } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import Pagination from "./Pagination.svelte";

describe("Pagination", () => {
  it("renders page size selector", () => {
    const { getByRole } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 1,
      },
    });
    
    const select = getByRole("combobox");
    expect(select).toBeTruthy();
  });

  it("renders current page indicator", () => {
    const { getByText } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 2,
      },
    });
    
    expect(getByText(/Page 2/)).toBeTruthy();
  });

  it("calls onPageChange when next button clicked", async () => {
    const onPageChange = vi.fn();
    const { getByText } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 1,
        onPageChange,
      },
    });
    
    const nextButton = getByText("Next");
    await fireEvent.click(nextButton);
    
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageSizeChange when select changes", async () => {
    const onPageSizeChange = vi.fn();
    const { getByRole } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 1,
        onPageSizeChange,
      },
    });
    
    const select = getByRole("combobox");
    await fireEvent.change(select, { target: { value: "25" } });
    
    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });

  it("displays total count correctly", () => {
    const { getByText } = render(Pagination, {
      props: {
        totalItems: 250,
        pageSize: 25,
        currentPage: 1,
      },
    });
    
    expect(getByText(/250/)).toBeTruthy();
  });

  it("disables previous on first page", () => {
    const { getByText } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 1,
      },
    });
    
    const prevButton = getByText("Previous");
    expect(prevButton).toBeDisabled();
  });

  it("disables next on last page", () => {
    const { getByText } = render(Pagination, {
      props: {
        totalItems: 100,
        pageSize: 10,
        currentPage: 10,
      },
    });
    
    const nextButton = getByText("Next");
    expect(nextButton).toBeDisabled();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend-svelt && bun run test:unit --run src/lib/components/Pagination.test.ts
```

Expected: FAIL (component doesn't exist)

### Task 5.2: Implement Pagination Component

**Files:**
- Create: `frontend-svelt/src/lib/components/Pagination.svelte`

**Step 1: Create component**

```svelte
<script lang="ts">
  import { cn } from "$lib/utils/cn";

  interface Props {
    totalItems: number;
    pageSize: number;
    currentPage: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (size: number) => void;
    class?: string;
  }

  let {
    totalItems,
    pageSize,
    currentPage,
    onPageChange,
    onPageSizeChange,
    class: className,
  }: Props = $props();

  const pageSizes = [10, 25, 50, 100];

  const totalPages = $derived(Math.ceil(totalItems / pageSize));
  const startItem = $derived((currentPage - 1) * pageSize + 1);
  const endItem = $derived(Math.min(currentPage * pageSize, totalItems));

  function handlePrevious() {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  }

  function handleNext() {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  }

  function handlePageSizeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onPageSizeChange(parseInt(target.value, 10));
  }
</script>

<div class={cn("flex items-center justify-between px-4 py-3", className)}>
  <div class="flex items-center gap-4">
    <span class="text-sm text-muted-foreground">
      Showing {startItem}-{endItem} of {totalItems}
    </span>
    
    <div class="flex items-center gap-2">
      <label for="page-size" class="text-sm text-muted-foreground">Rows:</label>
      <select
        id="page-size"
        class="h-9 rounded-md border border-input bg-background px-2 text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
        value={pageSize}
        onchange={handlePageSizeChange}
      >
        {#each pageSizes as size}
          <option value={size}>{size}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="flex items-center gap-2">
    <span class="text-sm text-muted-foreground">
      Page {currentPage} of {totalPages}
    </span>
    
    <div class="flex gap-1">
      <button
        type="button"
        class="px-3 py-1 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        onclick={handlePrevious}
        disabled={currentPage <= 1}
      >
        Previous
      </button>
      
      <button
        type="button"
        class="px-3 py-1 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        onclick={handleNext}
        disabled={currentPage >= totalPages}
      >
        Next
      </button>
    </div>
  </div>
</div>
```

**Step 2: Run test to verify it passes**

```bash
cd frontend-svelt && bun run test:unit --run src/lib/components/Pagination.test.ts
```

Expected: PASS

**Step 3: Commit**

```bash
git add frontend-svelt/src/lib/components/Pagination.svelte frontend-svelt/src/lib/components/Pagination.test.ts
git commit -m "feat: add Pagination component with configurable page sizes"
```

---

## Phase 6: Frontend - Fix Results Page

### Task 6.1: Read Current Page Implementation

**Step 1: Read the full page file**

```bash
cat frontend-svelt/src/routes/workspace/\[id\]/+page.svelte
```

**Step 2: Identify the broken line 153-154**

Note the incomplete `matchResults =` assignment.

### Task 6.2: Update Results Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/+page.svelte`

**Step 1: Add imports and state**

At the top of the script section, add:

```svelte
<script lang="ts">
  // ... existing imports
  import Pagination from "$lib/components/Pagination.svelte";
  import { api } from "$lib/api/client";
  
  // ... existing state
  
  // Pagination state
  let pageSize = $state(25);
  let currentPage = $state(1);
  
  // Simulation state
  let useSimulation = $state(false);
  
  // Derived pagination values
  const totalPages = $derived(Math.ceil((matchResults?.result_data?.length ?? 0) / pageSize));
  const paginatedRows = $derived(() => {
    const rows = matchResults?.result_data ?? [];
    const start = (currentPage - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  });
</script>
```

**Step 2: Fix the broken matchResults assignment**

Find and fix line 153-154:

```typescript
// Before (broken):
matchResults =

// After (fixed):
matchResults = response.results;
```

**Step 3: Add fetch results function with simulation support**

```typescript
async function fetchResults(taskId: string) {
  const response = useSimulation
    ? await api.simulateOcrResults(taskId)
    : await api.demoGetMatchingResults(taskId);
  
  if (response.ok) {
    matchResults = response.data.results;
  }
}
```

**Step 4: Update the results table section**

Replace the results display section with:

```svelte
{#if matchResults}
  <div class="rounded-xl border bg-card shadow-sm">
    <!-- Simulation Toggle -->
    <div class="flex items-center justify-between px-4 py-3 border-b">
      <h3 class="text-lg font-semibold">Match Results</h3>
      <label class="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          bind:checked={useSimulation}
          class="h-4 w-4 rounded border-input"
        />
        Use Simulated Data
      </label>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-muted text-muted-foreground text-sm">
          <tr>
            {#each matchResults.column_data.sort((a, b) => a.position_idx - b.position_idx) as column}
              <th class="px-4 py-3 text-left font-medium">
                {column.name}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each paginatedRows() as row}
            <tr class="border-b hover:bg-accent/50">
              {#each row.values as value}
                <td class="px-4 py-3 text-sm">
                  {#if value.data_type === 'float'}
                    <span class="font-mono">{parseFloat(value.value).toFixed(3)}</span>
                  {:else}
                    {value.value}
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <Pagination
      totalItems={matchResults.result_data.length}
      {pageSize}
      {currentPage}
      onPageChange={(page) => currentPage = page}
      onPageSizeChange={(size) => {
        pageSize = size;
        currentPage = 1;
      }}
    />
  </div>
{/if}
```

**Step 5: Verify page compiles**

```bash
cd frontend-svelt && bun run check
```

Expected: No errors

**Step 6: Commit**

```bash
git add frontend-svelt/src/routes/workspace/\[id\]/+page.svelte
git commit -m "fix: repair results table with column ordering, pagination, and simulation toggle"
```

---

## Phase 7: Frontend - API Layer Update

### Task 7.1: Add Simulate Method to Client

**Files:**
- Modify: `frontend-svelt/src/lib/api/client.ts`

**Step 1: Add simulateOcrResults to api object**

Add to the `api` object in `client.ts`:

```typescript
export const api = {
  // ... existing methods
  
  simulateOcrResults: (task_id: string) =>
    request<MatchResponse>({
      opts: {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      },
      path: ['api', 'workspace', 'ocr', 'simulate', task_id],
    }),
};
```

**Step 2: Verify type check**

```bash
cd frontend-svelt && bun run check
```

Expected: No errors

**Step 3: Commit**

```bash
git add frontend-svelt/src/lib/api/client.ts
git commit -m "feat: add simulateOcrResults API method"
```

---

## Phase 8: Frontend - Verification

### Task 8.1: Run All Frontend Checks

**Step 1: Run type check**

```bash
cd frontend-svelt && bun run check
```

Expected: No errors

**Step 2: Run lint**

```bash
cd frontend-svelt && bun run lint
```

Expected: No errors

**Step 3: Run format check**

```bash
cd frontend-svelt && bun run fmt:check
```

Expected: No changes needed

**Step 4: Run unit tests**

```bash
cd frontend-svelt && bun run test:unit --run
```

Expected: All PASS

**Step 5: Run build**

```bash
cd frontend-svelt && bun run build
```

Expected: Build succeeds

---

## Phase 9: Documentation

### Task 9.1: Create Running Locally Documentation

**Files:**
- Create: `docs/running-locally.md`

**Step 1: Create documentation**

```markdown
# Running VoteCatcher Locally

## Prerequisites

- Python 3.13+
- uv package manager
- Node.js 20+
- Bun package manager
- PostgreSQL (optional, for full functionality)

## Backend Setup

### Installation

```bash
cd backend
uv sync --dev
```

### Environment Configuration

Create `.env.local` in the backend directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/votecatcher
VITE_API_URL=http://localhost:8080
```

### Running

```bash
cd backend

# Local development
uv run main.py --env local

# Debug mode
uv run main.py --env debug

# Development
uv run main.py --env dev

# Production
uv run main.py --env prod
```

The API will be available at http://localhost:8080

API documentation: http://localhost:8080/docs

### Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=app

# Run specific test module
uv run pytest tests/matching/ -v
```

### Linting & Formatting

```bash
cd backend

# Type check
uv run basedpyright app/

# Lint
uv run ruff check app/

# Format check
uv run ruff format app/ --check

# Auto-fix lint issues
uv run ruff check app/ --fix

# Auto-format
uv run ruff format app/
```

## Frontend Setup

### Installation

```bash
cd frontend-svelt
bun install
```

### Running

```bash
cd frontend-svelt

# Development server
bun run dev
```

The app will be available at http://localhost:5173

### Testing

```bash
cd frontend-svelt

# Unit tests
bun run test:unit

# Unit tests (watch mode)
bun run test:unit --watch

# E2E tests
bun run test:e2e

# All tests
bun run test
```

### Linting & Formatting

```bash
cd frontend-svelt

# Type check
bun run check

# Lint
bun run lint

# Auto-fix lint issues
bun run lint:fix

# Format check
bun run fmt:check

# Auto-format
bun run fmt
```

### Building

```bash
cd frontend-svelt

# Production build
bun run build

# Preview production build
bun run preview
```

## Full Development Workflow

### Terminal 1 - Backend

```bash
cd backend
uv run main.py --env local
```

### Terminal 2 - Frontend

```bash
cd frontend-svelt
bun run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- API Docs: http://localhost:8080/docs

## Docker Setup (Coming Soon)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Troubleshooting

### Backend won't start

1. Check Python version: `python --version` (should be 3.13+)
2. Check uv is installed: `uv --version`
3. Check .env.local exists and has correct values
4. Try fresh install: `rm -rf .venv && uv sync --dev`

### Frontend won't start

1. Check Node version: `node --version` (should be 20+)
2. Check Bun is installed: `bun --version`
3. Try fresh install: `rm -rf node_modules && bun install`

### Tests failing

1. Ensure all dependencies are installed
2. Check environment variables are set
3. Run with verbose output for details

### Type errors

1. Run `bun run check` in frontend
2. Run `uv run basedpyright app/` in backend
3. Check for missing type stubs
```

**Step 2: Commit**

```bash
git add docs/running-locally.md
git commit -m "docs: add running locally documentation"
```

---

## Phase 10: Verification Script

### Task 10.1: Create Verification Script

**Files:**
- Create: `scripts/verify-fix-results.sh`

**Step 1: Create scripts directory**

```bash
mkdir -p scripts
```

**Step 2: Create verification script**

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "VoteCatcher Fix Results Table Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass() {
  echo -e "${GREEN}✓ $1${NC}"
}

fail() {
  echo -e "${RED}✗ $1${NC}"
  exit 1
}

# Backend checks
echo "=== Backend Checks ==="

echo "1. Python type check (basedpyright)..."
cd backend
if uv run basedpyright app/ > /dev/null 2>&1; then
  pass "Type check passed"
else
  fail "Type check failed"
fi

echo "2. Python lint (ruff)..."
if uv run ruff check app/ > /dev/null 2>&1; then
  pass "Lint passed"
else
  fail "Lint failed"
fi

echo "3. Python format check (ruff)..."
if uv run ruff format app/ --check > /dev/null 2>&1; then
  pass "Format check passed"
else
  fail "Format check failed"
fi

echo "4. Backend tests..."
if uv run pytest tests/matching/ tests/routers/test_ocr_simulate.py -q > /dev/null 2>&1; then
  pass "Backend tests passed"
else
  fail "Backend tests failed"
fi

# Frontend checks
echo ""
echo "=== Frontend Checks ==="

cd ../frontend-svelt

echo "5. Frontend type check..."
if bun run check > /dev/null 2>&1; then
  pass "Type check passed"
else
  fail "Type check failed"
fi

echo "6. Frontend lint (oxlint)..."
if bun run lint > /dev/null 2>&1; then
  pass "Lint passed"
else
  fail "Lint failed"
fi

echo "7. Frontend format check (oxfmt)..."
if bun run fmt:check > /dev/null 2>&1; then
  pass "Format check passed"
else
  fail "Format check failed"
fi

echo "8. Frontend unit tests..."
if bun run test:unit --run > /dev/null 2>&1; then
  pass "Unit tests passed"
else
  fail "Unit tests failed"
fi

# File existence checks
echo ""
echo "=== File Existence Checks ==="

cd ..

echo "9. Simulate endpoint exists..."
if grep -q "simulate" backend/app/routers/ocr_route.py 2>/dev/null; then
  pass "Simulate endpoint found"
else
  fail "Simulate endpoint not found"
fi

echo "10. Pagination component exists..."
if test -f frontend-svelt/src/lib/components/Pagination.svelte; then
  pass "Pagination component found"
else
  fail "Pagination component not found"
fi

echo "11. Design tokens exist..."
if test -f frontend-svelt/src/lib/styles/tokens.css; then
  pass "Design tokens found"
else
  fail "Design tokens not found"
fi

echo "12. CN utility exists..."
if test -f frontend-svelt/src/lib/utils/cn.ts; then
  pass "CN utility found"
else
  fail "CN utility not found"
fi

echo "13. No incomplete code..."
if ! grep -q "^matchResults =$" frontend-svelt/src/routes/workspace/\[id\]/+page.svelte 2>/dev/null; then
  pass "No incomplete code found"
else
  fail "Incomplete code still present"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}All verifications passed!${NC}"
echo "=========================================="
```

**Step 3: Make executable**

```bash
chmod +x scripts/verify-fix-results.sh
```

**Step 4: Run verification**

```bash
./scripts/verify-fix-results.sh
```

Expected: All checks pass

**Step 5: Commit**

```bash
git add scripts/verify-fix-results.sh
git commit -m "feat: add verification script for fix-results-table"
```

---

## Phase 11: Docker & DevContainer (Post-Main)

### Task 11.1: Create Docker Compose

**Files:**
- Create: `docker-compose.yml`

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - ENV=local
    env_file:
      - ./backend/.env.local
    volumes:
      - ./backend:/app
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend-svelt
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend-svelt:/app
      - /app/node_modules
    depends_on:
      - backend

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: votecatcher
      POSTGRES_PASSWORD: votecatcher_dev
      POSTGRES_DB: votecatcher
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Task 11.2: Create Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

RUN uv sync --dev

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py", "--env", "local"]
```

### Task 11.3: Create Backend .dockerignore

**Files:**
- Create: `backend/.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.venv
venv/
.eggs
*.egg-info/
*.egg
.pytest_cache
.coverage
htmlcov/
.env.*
!.env.local
```

### Task 11.4: Create Frontend Dockerfile

**Files:**
- Create: `frontend-svelt/Dockerfile`

```dockerfile
FROM oven/bun:1 AS base
WORKDIR /app

FROM base AS deps
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

FROM base AS dev
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173

CMD ["bun", "run", "dev", "--host"]
```

### Task 11.5: Create Frontend .dockerignore

**Files:**
- Create: `frontend-svelt/.dockerignore`

```
node_modules
.svelte-kit
build
dist
.env
.env.*
!.env.example
*.log
```

### Task 11.6: Create DevContainer Configuration

**Files:**
- Create: `.devcontainer/devcontainer.json`

```json
{
  "name": "VoteCatcher Dev",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "frontend",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/common-utils:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "svelte.svelte-vscode",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode",
        "dbaeumer.vscode-eslint",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff"
        },
        "[svelte]": {
          "editor.defaultFormatter": "svelte.svelte-vscode"
        }
      }
    }
  },
  "forwardPorts": [5173, 8080, 5432],
  "postCreateCommand": "cd backend && uv sync && cd ../frontend-svelt && bun install",
  "remoteUser": "vscode"
}
```

### Task 11.7: Create DevContainer Setup Script

**Files:**
- Create: `.devcontainer/setup.sh`

```bash
#!/bin/bash
set -e

echo "=== Setting up VoteCatcher DevContainer ==="

echo "Setting up backend..."
cd /workspace/backend
uv sync --dev

echo "Setting up frontend..."
cd /workspace/frontend-svelt
bun install

if [ ! -f /workspace/backend/.env.local ]; then
  echo "Creating .env.local template..."
  cat > /workspace/backend/.env.local << EOF
DATABASE_URL=postgresql://votecatcher:votecatcher_dev@db:5432/votecatcher
VITE_API_URL=http://localhost:8080
EOF
fi

echo "=== Setup complete ==="
echo "Run 'bun run dev' in frontend-svelt/ and 'uv run main.py --env local' in backend/"
```

### Task 11.8: Create DevContainer README

**Files:**
- Create: `.devcontainer/README.md`

```markdown
# VoteCatcher DevContainer

## Quick Start

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container"
3. Wait for container to build (first time takes ~5 minutes)
4. Run the setup:
   ```bash
   .devcontainer/setup.sh
   ```

## Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
uv run main.py --env local
```

**Terminal 2 - Frontend:**
```bash
cd frontend-svelt
bun run dev
```

## Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8080 | http://localhost:8080 |
| Backend Docs | 8080 | http://localhost:8080/docs |
| PostgreSQL | 5432 | localhost:5432 |

## Troubleshooting

### Container won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Dependencies out of sync
```bash
.devcontainer/setup.sh
```
```

### Task 11.9: Commit Docker/DevContainer Files

```bash
git add docker-compose.yml backend/Dockerfile backend/.dockerignore frontend-svelt/Dockerfile frontend-svelt/.dockerignore .devcontainer/
git commit -m "feat: add Docker Compose and DevContainer configuration"
```

### Task 11.10: Verify Docker Setup

**Step 1: Build containers**

```bash
docker-compose build
```

Expected: All services build successfully

**Step 2: Start containers**

```bash
docker-compose up -d
```

Expected: All services start

**Step 3: Check health**

```bash
curl http://localhost:8080/docs
curl http://localhost:5173
```

Expected: Both respond

**Step 4: Cleanup**

```bash
docker-compose down -v
```

---

## Final Commit

After all phases complete:

```bash
git add docs/plans/2026-03-02-fix-results-table-design.md docs/plans/2026-03-02-fix-results-table.md
git commit -m "docs: add design document and implementation plan for fix-results-table"
```

---

## Summary

**Total Tasks:** 11 phases, ~35 individual steps

**Estimated Time:** 3-4 hours

**Key Deliverables:**
1. Fixed column ordering in backend
2. Simulate endpoint for testing
3. Backend unit tests
4. Design tokens and CN utility
5. Pagination component
6. Fixed results page with pagination and simulation toggle
7. API layer update
8. Running locally documentation
9. Verification script
10. Docker/DevContainer setup

**Success Criteria:**
- All tests pass
- All lint/format checks pass
- Verification script runs green
- Manual testing confirms results table works correctly

---

## Post-Task Checklist (Apply After EVERY Task)

After completing each task in this plan, you MUST:

1. **Update Progress Tracker** (`.agent-workspace/PROGRESS.md`)
   - Mark task as `Completed`
   - Add commit hash
   - Add timestamp
   - Add any notes/blockers encountered

2. **Update Status Overview**
   - Increment "Tasks Done" for the phase
   - Update "Overall Progress" percentage
   - Update "Last Updated" timestamp

3. **Verify the Change**
   - Run relevant tests
   - Run lint/format checks for changed files
   - Ensure no regressions

4. **Commit if Not Already Done**
   - Each task should have its own commit
   - Use descriptive commit messages per plan

**At Phase Completion:**
1. Add entry to Checkpoint Log in PROGRESS.md
2. Run full phase verification
3. Only proceed to next phase if all checks pass
