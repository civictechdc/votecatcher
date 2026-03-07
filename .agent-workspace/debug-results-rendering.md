# Debug Plan: Matching Results Not Rendering

**Status:** Open
**Severity:** High
**Created:** 2026-03-07
**Last Known Working:** commit `df12170` (WIP: Database integration)

---

## Problem Statement

Smoke test revealed that matching results fail to render on the frontend after our changes. The data flow from backend to frontend may be broken.

**Symptoms:**
- Results don't display after running matching
- Unknown if issue is in backend response, frontend parsing, or data binding

**Critical Constraint:**
- **NO real LLM OCR calls** during debugging
- Must use simulation mode exclusively
- This is why the simulation toggle bug is blocking

---

## Known Working State

**Commit:** `df12170` (2026-02-28)
**Message:** "WIP: Database integration Adding clearer separation between the votecatcher domain code TODO: Fix results displaying out of order/mismatched on front end"

Note: Even the working commit mentions display issues, but results DID render.

---

## Debugging Strategy

### Phase A: Establish Baseline with Simulation

**Goal:** Get simulation mode working so we can debug without real OCR calls

| Step | Action | Expected | Commands |
|------|--------|----------|----------|
| A.1 | Fix simulation toggle placement | Checkbox visible before running | Move checkbox outside `{#if matchResults}` |
| A.2 | Test simulation endpoint directly | Returns 50-200 fake results | `curl http://localhost:8000/workspace/ocr/simulate/test-123` |
| A.3 | Verify frontend calls simulate endpoint | Network tab shows correct URL | Browser DevTools |
| A.4 | Verify data reaches frontend | Console.log shows results | Add temporary logging |

### Phase B: Isolate the Break Point

**Goal:** Find where data flow breaks

```text
BACKEND                    NETWORK                  FRONTEND
   │                          │                         │
   ├─ simulate endpoint ─────┼─────► JSON response ────┤
   │                          │                         │
   │                          │                    ├─ fetch() receives
   │                          │                    │
   │                          │                    ├─ convertMatchResponseToMatchResults()
   │                          │                    │
   │                          │                    ├─ matchResults state updated
   │                          │                    │
   │                          │                    └─ {#if} renders table
```

| Checkpoint | What to Verify | How |
|------------|---------------|-----|
| B.1 | Backend returns valid JSON | `curl` + inspect response structure |
| B.2 | Frontend receives response | `console.log(res)` in `onOcrJobCompleted` |
| B.3 | Converter transforms correctly | `console.log(matchResults)` after conversion |
| B.4 | State triggers re-render | Check `$state` reactivity |
| B.5 | DOM renders table | Inspect DOM, check `{#if}` conditions |

### Phase C: Compare with Working Commit

**Goal:** Identify what changed

```bash
# Get list of files changed since working commit
git diff --name-only df12170..HEAD

# Focus areas (likely culprits):
# - src/routes/workspace/[id]/+page.svelte (frontend logic)
# - src/lib/utils.ts (converter function)
# - src/lib/api/matching-requests.ts (API client)
# - backend/app/routers/ocr_route.py (backend endpoint)
# - backend/app/matching/response_adapter.py (response formatting)
```

| File | What Changed | Impact |
|------|-------------|--------|
| `+page.svelte` | Added pagination, feature flags, simulation toggle | State management, data binding |
| `matching-requests.ts` | Added `simulateOcrResults` method | New API path |
| `response_adapter.py` | Added column sorting | Response structure |
| `utils.ts` | Converter function exists | Data transformation |

### Phase D: Database Investigation (Sub-project)

**Goal:** Understand if database setup affects results

**Current Questions:**
- What database is being used? (SQLite, PostgreSQL, Supabase?)
- Where is it configured?
- Does simulation mode bypass database entirely?
- Do real results require database reads?

**Investigation Tasks:**
1. Review database configuration files
2. Check if demo mode uses in-memory vs real database
3. Verify simulation endpoint doesn't require database
4. Document database setup for future reference

---

## Execution Plan

### Immediate Actions (Before Debugging)

| Priority | Task | Why |
|----------|------|-----|
| **P0** | Fix simulation toggle placement | Cannot debug without simulation |
| **P0** | Verify simulation endpoint works | Establish known-good baseline |
| **P1** | Add debug logging to data flow | Visibility into where break occurs |
| **P2** | Create git diff summary | Understand scope of changes |

### Debugging Commands

```bash
# 1. Check simulation endpoint
curl -s http://localhost:8000/workspace/ocr/simulate/test-task-id | jq '.'

# 2. Check feature flags endpoint
curl -s http://localhost:8000/api/config/features | jq '.'

# 3. List files changed since working commit
git diff --stat df12170..HEAD -- frontend-svelt/src/routes/workspace/
git diff --stat df12170..HEAD -- backend/app/

# 4. View the working version of the page
git show df12170:frontend-svelt/src/routes/workspace/[id]/+page.svelte | head -200

# 5. Check current backend response structure
cd backend && uv run python -c "
from app.matching.response_adapter import MatchResultResponse
from app.ocr.ocr_helper import OCRProvider
# Print expected response structure
"
```

### Frontend Debug Checklist

Add temporary logging to `+page.svelte`:

```svelte
<script>
// Add after line 158
async function onOcrJobCompleted(jobId: string) {
    console.log('[DEBUG] onOcrJobCompleted called with:', jobId);
    console.log('[DEBUG] simulationMode:', $featureFlags.simulationMode);
    
    if ($featureFlags.simulationMode) {
        console.log('[DEBUG] Calling simulate endpoint...');
        const res = await matchApi.simulateOcrResults(jobId);
        console.log('[DEBUG] Simulate response:', res);
        console.log('[DEBUG] Response data:', res.data);
        
        const converted = convertMatchResponseToMatchResults(res.data.results);
        console.log('[DEBUG] Converted results:', converted);
        
        matchResults = converted;
        console.log('[DEBUG] matchResults state:', matchResults);
    } else {
        // ... existing real path
    }
}
</script>
```

---

## Root Cause Hypotheses

### H1: State Reactivity Issue
- **Symptom:** Data arrives but UI doesn't update
- **Cause:** Svelte 5 `$state` not triggering re-render
- **Test:** Console.log before/after state assignment
- **Fix:** Check if `matchResults` properly declared as `$state`

### H2: Data Structure Mismatch
- **Symptom:** Converter fails or produces wrong shape
- **Cause:** `convertMatchResponseToMatchResults` expects different structure
- **Test:** Log input/output of converter
- **Fix:** Update converter or response structure

### H3: Feature Flag Not Working
- **Symptom:** Simulation mode doesn't activate
- **Cause:** `$featureFlags.simulationMode` always false
- **Test:** Log flag value before API call
- **Fix:** Fix feature flag initialization

### H4: API Path Wrong
- **Symptom:** 404 or wrong endpoint called
- **Cause:** `simulateOcrResults` constructs wrong URL
- **Test:** Check Network tab for actual URL
- **Fix:** Update API client path construction

### H5: Conditional Rendering Bug
- **Symptom:** Results exist but `{#if}` doesn't show them
- **Cause:** Condition evaluates incorrectly
- **Test:** Log condition components
- **Fix:** Update rendering logic

---

## Success Criteria

- [ ] Simulation mode works end-to-end
- [ ] Results render in table with correct columns
- [ ] Pagination works
- [ ] No real OCR calls needed for testing
- [ ] Root cause documented
- [ ] Fix implemented and verified

---

## Related Concerns

- **Simulation toggle UI placement bug** — Blocking this debug effort
- **Debug flag system** — Would help with future debugging
- **Database setup** — May need documentation as sub-project

---

## Notes

- **Do NOT** make real LLM API calls during debugging
- **Do NOT** commit debug logging to main branch
- **DO** document findings for future reference
- **DO** consider adding permanent debug logging (behind flag)
