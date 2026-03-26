# Issues and Changes Log

Tracking issues discovered during implementation walkthroughs and proposed changes.

**Last Updated:** 2026-03-26 (Session 5 - Fixed #36, #40, #42, #43 via parallel subagents)

---

## Issue Summary

| Issue | Severity | Status | Phase |
|-------|----------|--------|-------|
| #1 Orphaned Jobs | 🔴 HIGH | ✅ Fixed | Phase 12 |
| #2 Connected Indicator | 🟢 LOW | ✅ Fixed | P3 |
| #3 Status Filter Style | 🟢 LOW | ✅ Fixed | P3 |
| #5 Voter List Display | 🟡 MEDIUM | ✅ Fixed | Phase 13 |
| #6 Flash of Placeholder | 🟢 LOW | ✅ Fixed | P3 |
| #7 Campaign Context Lost | 🟢 LOW | ✅ Fixed | P4 |
| #8 Dropdown Clipped | 🟡 MEDIUM | ✅ Fixed | Phase 12 |
| #9 Create Job Button | 🟡 MEDIUM | ✅ Fixed | Phase 12 |
| #10 Dashboard State | 🟡 MEDIUM | ✅ Fixed | Phase 13 |
| #11 High Confidence Card | 🟢 LOW | ✅ Fixed | P3 |
| #12 View Results Button | 🟡 MEDIUM | ✅ Fixed | Phase 12 |
| #13 OCR Batching | 🟢 LOW | ✅ Fixed | P3 |
| #14 OCR Duplicates | 🔴 HIGH | ✅ Fixed | Phase 12 |
| #15 Metrics Deduplication | 🔴 HIGH | ✅ Fixed | Phase 12 |
| #16 DEVELOPER.md Out of Sync | 🟢 LOW | ✅ Fixed | Phase 12 |
| #17 Uncommitted Fixes | 🟡 MEDIUM | ✅ Fixed | Phase 12 |
| #18 Flaky Test | 🟢 LOW | ✅ Fixed | Phase 12 |
| #19 Polling Storm | 🟡 MEDIUM | ✅ Fixed | Phase 12 |
| #20 Event Bus | 🟡 MEDIUM | ✅ Implemented | Phase 10 |
| #23 Events Router Missing /api Prefix | 🔴 HIGH | ✅ Fixed | Phase 10 |
| #24 SSE Manager Deprecation | 🟡 MEDIUM | 📝 Documented | Phase 10 |
| #25 Event Bus Integration Test Missing | 🟡 MEDIUM | ✅ Fixed | Phase 10 |
| #26 PROGRESS.md Out of Sync | 🟢 LOW | ✅ Fixed | Process |
| #27 TypeScript Test Mocks Out of Sync | 🟡 MEDIUM | ✅ Fixed | P3 |
| #28 SSE Transport Code Duplication | 🟡 MEDIUM | ✅ Fixed | P3 |
| #29 E2E Tests Fragile (Skip on Empty) | 🟡 MEDIUM | ✅ Fixed | P3 |
| #30 Inconsistent Event ID Types | 🟢 LOW | 📝 By Design | P3 |
| #31 Late Import in Worker | 🟢 LOW | ✅ Fixed | P3 |
| #32 No Event Validation Before Store Update | 🟢 LOW | ✅ Fixed | P3 |
| #33 Test Class Attribute Mutation | 🟢 LOW | ✅ Fixed | P3 |
| #34 E2E Tests Don't Verify Job Events | 🟢 LOW | ✅ Fixed | P3 |
| #35 Race Condition in Event Disconnect | 🟡 MEDIUM | ✅ Fixed | P3 |
| #36 Source Inference Performance | 🟢 LOW | ✅ Fixed | P4 |
| #37 Heartbeat Not Acknowledged | 🟢 LOW | 📝 By Design | P3 |
| #38 SSE Transport Unit Tests Missing | 🟡 MEDIUM | ✅ Fixed | P3 |
| #39 SSE close() Doesn't Cancel Generators | 🟡 MEDIUM | ✅ Fixed | P3 |
| #40 E2E Event Flow Not Verified | 🟡 MEDIUM | ✅ Fixed | P4 |
| #41 Sidebar Redundant Campaign Fetches | 🟡 MEDIUM | ✅ Fixed | P3 |
| #42 Test Assertion Unreachable | 🟢 LOW | ✅ Fixed | P4 |
| #43 Campaign/Job ID Type Inconsistency | 🟢 LOW | ✅ Fixed | P4 |

**Fixed:** 37 | **Documented:** 3 | **Open (P3-P4):** 0 | **Proposals:** 0

---

## Issue #15: Metrics Confidence Counts Not Deduplicated by OCR Result

**Discovered:** 2026-03-17
**Severity:** High (Data Accuracy Bug)
**Status:** ✅ Fixed (2026-03-18)

### Symptoms
- Confidence distribution percentages exceeded 100% (e.g., 500%)
- "Processed" metric showed correct count but confidence breakdown was inflated
- Dashboard donut chart showed impossible percentage totals
- Progress percentage showed 500% (e.g., `processed=50 progress=500.0 total=10`)

### Root Cause Analysis

After BUG-14 fix, each crop can have 5 OCR results (ocr_index 0-4). The metrics service had TWO issues:

**Issue 1: Confidence Deduplication**
- Correctly counted `processed` as unique `ocr_result_id` values
- But incorrectly counted confidence by iterating ALL match results, not deduplicated by `ocr_result_id`

**Issue 2: Semantic Mismatch in Progress Calculation**
- `total_signatures` counted **crops** (10)
- `processed` counted **OCR results** (50 individual signatures)
- Progress = 50/10 = **500%** ❌

**Example:**
- 10 crops × 5 OCR results = 50 OCR results
- 50 match results
- `total_signatures` = 10 (crops) ← Wrong!
- `processed` = 50 (OCR results)
- `high_confidence` = 50 (all matches) → 500% ❌

### Fix Applied

**Fix 1: Confidence Deduplication** (2026-03-17)

Updated `backend/app/services/metrics.py:_count_processed_results()` to:
1. Track unique `ocr_result_id` values in a set
2. Build `ocr_to_confidence` dict mapping each OCR result to its confidence level
3. Count confidence levels from the deduplicated dict, not raw match results

**Fix 2: Semantic Alignment** (2026-03-18)

Updated `backend/app/services/metrics.py:_count_total_signatures()` to count **OCR results** (individual signatures) instead of crops:

```python
def _count_total_signatures(self, campaign_id: UUID) -> int:
    """Count total OCR results (individual signatures) for a campaign.

    After BUG-14 fix, each crop can have up to 5 OCR results (ocr_index 0-4),
    representing individual signatures extracted from a petition page.
    This counts OCR results (signatures), not crops, to align with 'processed'.
    """
    from app.data.database.model.ocr_result import OcrResult

    # ... query OCR results instead of crops ...

    count = self.session.exec(
        select(func.count())
        .select_from(OcrResult)
        .where(OcrResult.crop_id.in_(crop_ids))
    ).one()

    return count or 0
```

**Result:**
- `total_signatures` = 50 (OCR results/signatures) ✓
- `processed` = 50 (OCR results with matches) ✓
- Progress = 50/50 = **100%** ✓

### Tests Updated

- `test_metrics_with_processed_results` - Updated expectations for signature-level semantics
- `test_metrics_deduplicated_by_ocr_result_with_multi_entry_ocr` - Updated to expect 100% progress
- `test_metrics_deduplicated_with_duplicate_match_results` - No changes needed

### Files Changed

| File | Change |
|------|--------|
| `backend/app/services/metrics.py` | Deduplicate confidence counts; count OCR results for total_signatures |
| `backend/tests/integration/api/test_campaign_metrics.py` | Updated test expectations for Option B semantics |

---

## Issue #1: Orphaned Jobs After Backend Restart

Job_id="job-164"

**Discovered:** 2026-03-17
**Severity:** High
**Status:** ✅ Fixed (Phase 12 - 2026-03-17)

### Symptoms
- Job 164 stuck in `MATCHING` state after backend restart
- Cannot cancel the job via UI (400 Bad Request)
- Backend log: `POST /jobs/164/cancel HTTP/1.1" 400 Bad Request`

### Root Cause
1. **No job recovery on startup**: When backend restarts, in-progress jobs are orphaned. The async matching task dies but job status remains `MATCHING`.
2. **Cancel endpoint too restrictive**: Only allows cancellation in these states:
   - `not_started`
   - `ocr_pending`
   - `ocr_started`

   Missing cancelable states:
   - `ocr_completed`
   - `matching_pending`
   - `matching`

### Proposed Fix
**Part 1: Expand cancelable states**
```python
cancelable_states = [
    job_status.NOT_STARTED,
    job_status.OCR_PENDING,
    job_status.OCR_STARTED,
    job_status.OCR_COMPLETED,
    job_status.MATCHING_PENDING,
    job_status.MATCHING,
]
```

**Caveat:** OCR cancellation depends on SDK support. Some providers may not support cancelling in-flight OCR requests. Need per-provider cancellation logic:
- OpenAI Batch API: supports cancellation
- Other providers: TBD

**Part 2: Job recovery on startup (orphan detection)**

On backend startup, detect orphaned jobs based on their state:

| Orphaned State | Recovery Options |
|----------------|------------------|
| `ocr_pending` / `ocr_started` | Resume OCR or cancel |
| `ocr_completed` | Resume matching or delete job |
| `matching_pending` / `matching` | Resume matching or delete job |

**UX:** Show orphaned jobs with action buttons: "Resume" / "Delete"

**Open questions:**
- How to detect "orphaned" vs "legitimately in progress"? (heartbeat? startup flag?)
- Should orphaned jobs auto-resume or wait for user action?

### Files Affected
- `backend/app/routers/job_router.py:203-212` - Cancel endpoint logic

---

## Issue #2: "Connected" Indicator in Job Status

**Discovered:** 2026-03-17
**Severity:** Low
**Status:** ✅ Fixed (2026-03-25)

### Description
The SSE "connected" indicator shown in job status UI is development/debug information that shouldn't be visible in production.

### Fix Applied
Changed indicator to only show when NOT connected (using amber pulse animation). Users now only see connection feedback when there's an issue, not when everything is working.

### Files Changed
| File | Change |
|------|--------|
| `frontend-svelt/src/routes/workspace/[id]/jobs/[job_id]/+page.svelte` | Only show indicator when disconnected |

---

## Issue #3: Status Filter Looks Like a Button

**Discovered:** 2026-03-17
**Severity:** Low
**Status:** ✅ Fixed (2026-03-25)

### Description
On `/workspace/[id]/jobs`, the status filter dropdown:
1. Styled like a button, unclear it's a dropdown
2. Width too small for text content (text gets cramped/truncated)

### Fix Applied
Added explicit dropdown styling with:
- Custom chevron icon
- Minimum width (min-w-40)
- Explicit border and hover states
- Better visual affordance

### Files Changed
| File | Change |
|------|--------|
| `frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte` | Added chevron, min-width, improved styling |

---

## Issue #5: Voter List Tab Missing "Existing Uploads" Display

**Discovered:** 2026-03-17
**Severity:** Medium
**Status:** ✅ Fixed (2026-03-25)

### Description
On `/workspace/[id]/upload`, the **Petitions** tab shows existing petition files with metadata (filename, size, pages, upload date). The **Voter List** tab has no equivalent - user can't see if a voter list was already uploaded for this campaign/region.

### Resolution

All proposed fixes were implemented:

1. **VoterListUpload model** - Created at `backend/app/data/database/model/voter_list_upload.py`
2. **GET endpoint** - `GET /api/regions/{region_id}/voter-list` returns upload metadata
3. **DELETE endpoint** - `DELETE /api/regions/{region_id}/voter-list` removes upload and voters
4. **Frontend display** - Upload page shows existing voter list with filename, row count, file size, upload date
5. **Delete functionality** - Users can delete existing voter list with confirmation dialog

### Files Changed

| File | Change |
|------|--------|
| `backend/app/data/database/model/voter_list_upload.py` | NEW: VoterListUpload model |
| `backend/app/routers/upload_router.py` | GET/DELETE endpoints for voter list |
| `backend/app/files/file_service.py` | Creates VoterListUpload on import |
| `frontend-svelt/src/routes/workspace/[id]/upload/+page.svelte` | Display existing voter list |

---

### Current Behavior
- Petitions tab: Shows list of existing scans with delete option
- Voter List tab: No visibility into existing voter list uploads

### Root Cause Analysis

**1. No Upload Metadata Storage**

Voter list uploads import data directly into `registered_voters` table, but there's **no corresponding metadata table** (unlike `petition_scans` which tracks filename, file_size, page_count, uploaded_at).

Current flow (`backend/app/files/file_service.py:194-273`):
```python
async def import_voter_list(self, file, region_id) -> tuple[str, int]:
    # 1. Validates CSV
    # 2. Saves file to disk at storage_base/voter-lists/{filename}
    # 3. Imports rows into registered_voters table
    # 4. Returns (file_path, imported_count) - but this info is LOST
```

The `RegisteredVoter` model (`backend/app/data/database/model/registered_voter.py`) only stores:
- `id`, `region_id`, `name_data`, `address_data`, `other_field_data`
- `created_at`, `updated_at`
- **No source file tracking**

**2. No GET Endpoint**

`backend/app/routers/upload_router.py` has only:
- `POST /upload/voter-list` - upload and import
- **No GET endpoint** to retrieve voter list status for a region

**3. Frontend Has No Fetch Logic**

`frontend-svelt/src/routes/workspace/[id]/upload/+page.svelte`:
- Petitions tab: calls `fetchExistingScans()` → `GET /api/campaigns/{id}/scans`
- Voter List tab: **No equivalent fetch or display**

### Proposed Fix

**Part 1: Add Voter List Upload Metadata Table**

Create `voter_list_uploads` table to track uploads:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| region_id | UUID | FK to regions |
| original_filename | str | Source file name |
| file_size | int | File size in bytes |
| row_count | int | Number of voters imported |
| uploaded_at | datetime | Upload timestamp |

**Part 2: Add Backend Endpoint**

Add `GET /api/regions/{region_id}/voter-list` to return:
```json
{
  "exists": true,
  "filename": "DC_voters_2024.csv",
  "file_size": 1234567,
  "row_count": 50000,
  "uploaded_at": "2026-03-17T10:30:00Z"
}
```

Or null if no upload exists.

**Part 3: Update Frontend**

- Add `fetchExistingVoterList()` function
- Display existing voter list info similar to petitions
- Add delete/re-upload option

### Design Questions

1. **Scope:** Voter lists are tied to region (not campaign). Should UI show:
   - Voter list for this campaign's region only?
   - Or indicate that this voter list is shared across all campaigns for the region?

2. **Replace vs Append:** When re-uploading, should it:
   - Replace all existing voters for that region?
   - Append (allowing multiple voter lists per region)?

3. **Delete Behavior:** Deleting a voter list should:
   - Remove all `registered_voters` for that region?
   - Or just the metadata record (keeping voters for matching)?

### Files Affected
- `backend/app/routers/upload_router.py` - Add GET endpoint for voter list status
- `frontend-svelt/src/routes/workspace/[id]/upload/+page.svelte` - Add existing voter list display

---

## Issue #6: Flash of Placeholder Text Before Data Loads

**Discovered:** 2026-03-17
**Severity:** Low (UX Polish)
**Status:** ✅ Fixed (2026-03-26)

### Description
When loading workspace pages (e.g., `/workspace/[id]/upload`), users briefly see "Campaign" as placeholder text before the actual campaign name loads. This occurs in two places:

1. **Page subtitle** - `<p class="mt-1 text-slate-600">` shows "Campaign" briefly
2. **Sidebar campaign selector** - Dropdown button shows "Campaign" briefly

### Root Cause

**Race condition between render and data fetch:**

1. Component renders immediately with campaigns store in initial state:
   ```typescript
   // campaigns.ts:13-17
   writable<CampaignsState>({
     campaigns: [],
     loading: true,  // ← Loading, but UI doesn't check this
     error: null
   });
   ```

2. `campaignName` derived from empty store:
   ```svelte
   <!-- +layout.svelte:10-11 -->
   const campaign = $derived($campaigns.campaigns.find(c => c.id === campaignId));
   const campaignName = $derived(campaign?.unique_name || campaign?.title || 'Campaign');
   ```

3. `onMount` fetches data AFTER initial render:
   ```svelte
   <!-- +layout.svelte:13-17 -->
   onMount(() => {
     if ($campaigns.campaigns.length === 0) {
       campaigns.fetchAll();  // ← Happens after render
     }
   });
   ```

4. When data arrives, `campaign` becomes defined, `campaignName` updates → causes flash

### Files Affected

| File | Line | Issue |
|------|------|-------|
| `+layout.svelte` | 10-11 | Derives name without checking loading state |
| `CampaignSidebar.svelte` | 17, 90 | Uses `campaignName` prop which is "Campaign" initially |
| `upload/+page.svelte` | 41, 228 | Same pattern: derives campaign, shows fallback |

### Proposed Fixes

**Option A: Show loading state explicitly**

```svelte
<!-- +layout.svelte -->
{#if $campaigns.loading}
  <span class="text-slate-400">Loading...</span>
{:else if campaign}
  {campaignName}
{:else}
  Campaign
{/if}
```

**Option B: Use skeleton/placeholder animation**

```svelte
{#if $campaigns.loading}
  <span class="animate-pulse bg-slate-200 rounded h-4 w-24 inline-block"></span>
{:else}
  {campaignName}
{/if}
```

**Option C: SSR with +page.server.ts (better UX, more complex)**

Pre-fetch campaign data on server, eliminating client-side flash entirely.

### Recommendation

**Option B** - Skeleton with pulse animation is the simplest fix that provides visual feedback without restructuring the data flow. Apply to:
- `CampaignSidebar.svelte:90` - Campaign selector button
- `upload/+page.svelte:228` - Page subtitle
- Any other pages using the same pattern

### Resolution

Applied Option B (skeleton with pulse animation) to both affected locations:

1. **CampaignSidebar.svelte** - Lines 90-94 show skeleton when `$campaigns.loading` is true
2. **upload/+page.svelte** - Lines 291-296 show skeleton when `$campaigns.loading` is true
3. **+layout.svelte** - Lines 13-17 return empty string when loading, which triggers skeleton in child components

### Files Changed

| File | Change |
|------|--------|
| `CampaignSidebar.svelte` | Shows skeleton during loading |
| `upload/+page.svelte` | Shows skeleton during loading |
| `+layout.svelte` | Returns empty string when loading |

---

## Issue #7: Campaign Context Lost When Navigating to Settings

**Discovered:** 2026-03-17
**Severity:** Low (UX Polish)
**Status:** ✅ Fixed (2026-03-26)

### Description
When navigating from a campaign-scoped page (e.g., `/workspace/[id]/upload`) to `/workspace/settings`, the campaign selector disappears from the sidebar. Users lose their "working context" and must re-navigate to their campaign after viewing settings.

### Root Cause

**Layout switching based on route:**

`+layout.svelte:6-18` conditionally renders different sidebars:
```svelte
<script>
  const isCampaignRoute = $derived(!!$page.params.id);
</script>

{#if isCampaignRoute}
  {@render children()}  <!-- Uses [id]/+layout.svelte → CampaignSidebar -->
{:else}
  <div class="flex min-h-screen bg-slate-50">
    <Sidebar />  <!-- Generic sidebar, no campaign selector -->
    <main>...</main>
  </div>
{/if}
```

- Campaign routes (`/workspace/[id]/*`) → `CampaignSidebar` with selector
- Non-campaign routes (`/workspace/settings`, `/workspace/campaigns`) → Generic `Sidebar` without selector

### Current Behavior

| From | To | Sidebar | Campaign Selector |
|------|-----|---------|-------------------|
| `/workspace/[id]/upload` | `/workspace/settings` | Generic Sidebar | ❌ Disappears |
| `/workspace/[id]/upload` | `/workspace/campaigns` | Generic Sidebar | ❌ Disappears |
| `/workspace/campaigns` | `/workspace/[id]/upload` | CampaignSidebar | ✅ Appears |

### Proposed Fixes

**Option A: Persist "Current Campaign" in Store**

Add `currentCampaignId` to a store that survives navigation:

```typescript
// stores/navigation.ts
interface NavigationState {
  currentCampaignId: string | null;
}

function createNavigationStore() {
  const { subscribe, set, update } = writable<NavigationState>({
    currentCampaignId: null
  });

  return {
    subscribe,
    setCurrentCampaign(id: string) {
      update(s => ({ ...s, currentCampaignId: id }));
    },
    clearCurrentCampaign() {
      update(s => ({ ...s, currentCampaignId: null }));
    }
  };
}
```

Then have `Sidebar` also show the campaign selector if `currentCampaignId` is set.

**Option B: Always Show Campaign Selector (if campaigns exist)**

Modify `Sidebar` to include a campaign selector whenever campaigns are loaded, allowing quick navigation back:

```
┌─────────────────────┐
│ Votecatcher         │
├─────────────────────┤
│ [DC 2024 Primary ▾] │  ← Always visible when campaigns exist
├─────────────────────┤
│ Campaigns           │
│ Settings            │
└─────────────────────┘
```

**Option C: Move Settings Link into Campaign Sidebar**

Add settings as a nav item within `CampaignSidebar` (under "Global" section), so settings is always accessed from within a campaign context. The campaign selector stays visible.

### Recommendation

**Option B** is simplest and provides the best UX:
- Users always see their working context
- Quick switch between campaigns from any workspace page
- Minimal code change (add selector to generic `Sidebar`)

### Files Affected

| File | Change |
|------|--------|
| `Sidebar.svelte` | Add optional campaign selector |
| `stores/navigation.ts` | NEW: track current campaign (for Option A) |
| `+layout.svelte` | Pass current campaign context to Sidebar |

### Resolution

Option B was already implemented in `Sidebar.svelte` (lines 70-96). The generic sidebar now includes a "Jump to Campaign" selector that shows whenever campaigns are loaded, allowing users to navigate back to any campaign from non-campaign routes like `/workspace/settings`.

### Files Changed

| File | Change |
|------|--------|
| None | Implementation already present |

---

## Issue #8: Model Selector Dropdown Clipped by Container

**Discovered:** 2026-03-17
**Severity:** Medium (Broken UX)
**Status:** ✅ Fixed (2026-03-18)

### Description
On `/workspace/settings`, when expanding a provider card and clicking the model selector dropdown, the dropdown list is clipped/hidden by the parent container. Users cannot see or select all available models.

### Root Cause

**Two CSS issues combining:**

1. **`overflow-hidden` on card container** (`ProviderConfigCard.svelte:94`):
   ```html
   <div class="rounded-lg border border-slate-200 bg-white overflow-hidden">
   ```
   This clips any content that extends beyond the card bounds, including dropdowns.

2. **Low z-index on dropdown** (`Select.svelte:233`):
   ```html
   <div class="absolute z-10 w-full mt-1 bg-white ...">
   ```
   `z-10` may be insufficient if parent containers create new stacking contexts.

### Visual Diagram

```
┌─────────────────────────────────────┐
│ Provider Card (overflow-hidden)     │
│  ┌─────────────────────────────┐    │
│  │ Model: [gpt-4o         ▾]  │    │
│  │        ┌──────────────┐    │    │  ← Dropdown clipped here
│  │        │ gpt-4o       │ ✗  │    │
│  │        │ gpt-4o-mini  │ ✗  │    │
│  │        │ gpt-4-turbo  │ ✗  │    │
│  │        └──────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Files Affected

| File | Line | Issue |
|------|------|-------|
| `src/lib/components/ProviderConfigCard.svelte` | 94 | `overflow-hidden` clips dropdown |
| `src/lib/components/ui/Select.svelte` | 179, 233 | Parent is `relative`, dropdown is `z-10` |

### Fix Applied (2026-03-18)

Combined Option A + B as recommended:
1. Removed `overflow-hidden` from `ProviderConfigCard.svelte:94`
2. Increased z-index to `z-50` in `Select.svelte:233`

### Files Changed

| File | Line | Change |
|------|------|--------|
| `src/lib/components/ProviderConfigCard.svelte` | 94 | Removed `overflow-hidden` |
| `src/lib/components/ui/Select.svelte` | 233 | Changed `z-10` to `z-50` |

### Alternative Solutions (Not Implemented)

**Option C: Portal dropdown to body**

Render the dropdown in a portal attached to `<body>`, escaping container constraints entirely. This is more robust but also more complex.

---

## Issue #9: Create Job Button Not Disabled When No Uploads

**Discovered:** 2026-03-17
**Severity:** Medium (UX/Bug)
**Status:** ✅ Fixed (Phase 12 - 2026-03-17)

### Description
On `/workspace/[id]/jobs`, the "Create Job" button is always enabled, even when no petition scans exist. Users can click it, open the modal, and attempt to create a job that will fail or be meaningless.

### Current Behavior
- Page checks for scans via `hasScans` state (line 34)
- Warning banner shows "No uploads yet" when `hasScans === false` (lines 270-285)
- But "Create Job" button remains clickable (line 267)

### Expected Behavior
- "Create Job" button should be disabled when `hasScans === false`
- Tooltip or helper text should explain why it's disabled

### Root Cause
Button at line 267 has no `disabled` condition for scan availability:
```svelte
<Button variant="primary" text="Create Job" onclick={openCreateModal} />
```

### Proposed Fix

```svelte
<Button
  variant="primary"
  text="Create Job"
  onclick={openCreateModal}
  disabled={hasScans === false}
  title={hasScans === false ? 'Upload petition files first' : ''}
/>
```

Alternatively, move the warning banner above the button and style the button as disabled.

### Files Affected

| File | Line | Issue |
|------|------|-------|
| `src/routes/workspace/[id]/jobs/+page.svelte` | 267 | Button missing disabled condition |

---

## Issue #10: Dashboard Missing "Uploads Ready, No Job Run" State

**Discovered:** 2026-03-17
**Severity:** Medium (UX Gap)
**Status:** ✅ Fixed (2026-03-25)

### Description
On `/workspace/[id]` (campaign dashboard), when a user has uploaded petition files but hasn't run any jobs, the dashboard shows "N/A" for all metrics without explaining *why* or what to do next. Users lose context about their campaign state.

### Resolution

Implemented `ProgressStepper` component that shows campaign setup state with CTAs:

1. **State detection** - `/api/campaigns/{id}/setup-status` returns voter_list, petitions, jobs status
2. **Progress stepper** - Shows 3 steps: Voter List → Petitions → Run Job
3. **Contextual CTAs** - Button changes based on current state:
   - "Upload Voter List" when missing
   - "Upload Petitions" when voter list exists but no petitions
   - "Create Job" when both exist but no jobs
4. **Hidden when complete** - Progress stepper hides when jobs exist

### Files Changed

| File | Change |
|------|--------|
| `backend/app/routers/campaign_router.py` | setup-status endpoint |
| `frontend-svelt/src/lib/components/dashboard/ProgressStepper.svelte` | NEW: Progress stepper component |
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | Integrate progress stepper |

---

## Issue #11: Redundant High Confidence Metric Card

**Discovered:** 2026-03-17
**Severity:** Low (UX Polish)
**Status:** ✅ Fixed (2026-03-26)

### Resolution

Replaced "High Confidence" card with "Voter List" card showing registered voter count for the campaign's region.

### Files Changed

| File | Change |
|------|--------|
| `backend/app/routers/campaign_router.py` | Added `voter_list_count` to `CampaignMetricsResponse` |
| `backend/app/services/metrics.py` | Added `_count_registered_voters()` method |
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | Replaced High Confidence card with Voter List card |
| `backend/tests/integration/api/test_campaign_metrics.py` | Added 2 tests for voter list count |

### Description
On `/workspace/[id]` (campaign dashboard), "High Confidence" appears as a standalone metric card in the top row, but the same information is already shown in the "Confidence Distribution" section below with a donut chart. This creates visual redundancy and wastes screen space.

### Current Layout

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Total       │ │ Processed   │ │ Active Jobs │ │ High Conf   │  ← Redundant
│ 123         │ │ 100         │ │ 1           │ │ 75          │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

┌───────────────────────────────┐ ┌───────────────────────────┐
│ Confidence Distribution       │ │ Recent Jobs              │
│ [Donut: High/Medium/Low]      │ │ ...                      │
│ High: 75  Medium: 20  Low: 5  │ │                          │  ← Same info here
└───────────────────────────────┘ └───────────────────────────┘
```

### Recommended Fix

**Option A: Remove High Confidence card, enhance Distribution section**

Keep 3 metric cards (Total, Processed, Active Jobs). Add a summary legend to the Confidence Distribution section:

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Total       │ │ Processed   │ │ Active Jobs │
│ 123         │ │ 100         │ │ 1           │
└─────────────┘ └─────────────┘ └─────────────┘

┌───────────────────────────────┐ ┌───────────────────────────┐
│ Confidence Distribution       │ │ Recent Jobs              │
│                               │ │                          │
│ [Donut Chart]                 │ │ ...                      │
│                               │ │                          │
│ ● High: 75 (61%)              │ │                          │
│ ● Medium: 20 (16%)            │ │                          │
│ ● Low: 5 (4%)                 │ │                          │
└───────────────────────────────┘ └───────────────────────────┘
```

**Option B: Replace card with "Match Rate" or similar**

Keep 4 cards but change the 4th to something unique:
- "Match Rate" (matched / total signatures)
- "Avg Confidence" (weighted average)
- "Voter List" (registered voters count)

### Files Affected

| File | Line | Change |
|------|------|--------|
| `src/routes/workspace/[id]/+page.svelte` | 106-112 | Remove or replace High Confidence card |
| `src/routes/workspace/[id]/+page.svelte` | 115-127 | Add legend/summary to Confidence Distribution |

### Recommended Approach: Voter List Count

Replace "High Confidence" card with "Voter List" showing registered voter count for the campaign's region.

**Backend changes:**

1. Update `CampaignMetricsResponse` (`campaign_router.py:185-194`):
```python
class CampaignMetricsResponse(BaseModel):
    total_signatures: int
    processed: int
    high_confidence: int
    medium_confidence: int
    low_confidence: int
    progress_percentage: float
    last_job: dict | None
    voter_list_count: int | None  # NEW: None if no voter list uploaded
```

2. Update `MetricsService.compute_campaign_metrics()` to query voter count:
```python
from app.data.database.model.registered_voter import RegisteredVoter

def _count_registered_voters(self, campaign_id: UUID) -> int | None:
    """Count registered voters for the campaign's region."""
    campaign = self.session.get(Campaign, campaign_id)
    if not campaign:
        return None

    count = self.session.exec(
        select(func.count())
        .select_from(RegisteredVoter)
        .where(RegisteredVoter.region_id == campaign.region_id)
    ).one()

    return count or None  # None = no voter list uploaded
```

**Frontend changes:**

```svelte
<!-- Replace High Confidence card -->
<div class="rounded-lg border border-slate-200 bg-white p-6">
  <h3 class="text-sm font-medium text-slate-600">Voter List</h3>
  <p class="mt-2 text-3xl font-bold {metrics.voterListCount ? 'text-slate-900' : 'text-slate-400'}">
    {metrics.voterListCount ?? 'N/A'}
  </p>
  {#if metrics.voterListCount}
    <p class="mt-1 text-sm text-slate-500">registered voters</p>
  {:else}
    <p class="mt-1 text-sm text-slate-500">
      <a href="/workspace/{campaignId}/upload" class="text-blue-600 hover:underline">Upload voter list</a>
    </p>
  {/if}
</div>
```

**Files Affected:**

| File | Change |
|------|--------|
| `backend/app/routers/campaign_router.py:185-194` | Add `voter_list_count` to response |
| `backend/app/services/metrics.py` | Add `_count_registered_voters()` method |
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | Replace card with Voter List |

---

## Issue #12: View Results Button Shows When No Match Results Exist

**Discovered:** 2026-03-17
**Severity:** Medium (Bug)
**Status:** ✅ Fixed (Phase 12 - 2026-03-17)

### Description
On `/workspace/[id]` (campaign dashboard), the "View Results" button in Quick Actions shows when petition files are uploaded but no jobs have been run. Clicking it leads to an empty results page.

### Root Cause
`hasResults` checks for signature crops, not processed match results:

```svelte
<!-- Line 28 -->
const hasResults = $derived(metrics.totalSignatures > 0);

<!-- Lines 171-173 -->
{#if hasResults}
  <Button variant="secondary" text="View Results" ... />
{/if}
```

- `totalSignatures` = count of petition crops (signatures extracted from uploads)
- This is > 0 as soon as files are uploaded
- But "View Results" should only show when matching has produced results

### Complexity: `hasResults` is Used in Multiple Contexts

The fix is not a simple replacement. `hasResults` controls 6 different UI elements with different semantics:

| Line | Usage | Should show when |
|------|-------|------------------|
| 93 | Total Signatures metric | Files uploaded (has crops) |
| 97 | Processed metric N/A | No match results |
| 98-100 | "% complete" subtitle | Has match results |
| 108 | High Confidence styling | Has match results |
| 121 | Confidence Donut | Has match results |
| 171-173 | View Results button | Has match results |

If we naively change `hasResults` to `processed > 0`, "Total Signatures" would incorrectly show "N/A" when files exist but no job has run.

### Correct Fix: Two Separate Flags

```typescript
// Line 28 - replace single flag with two
const hasCrops = $derived(metrics.totalSignatures > 0);
const hasMatchResults = $derived(metrics.processed > 0);
```

Then update each usage:

```svelte
<!-- Line 93: Total Signatures -->
<p class="mt-2 text-3xl font-bold text-slate-900">{formatMetric(metrics.totalSignatures, hasCrops)}</p>

<!-- Line 97: Processed -->
<p class="mt-2 text-3xl font-bold text-slate-900">{formatMetric(metrics.processed, hasMatchResults)}</p>

<!-- Lines 98-100: Progress subtitle -->
{#if hasMatchResults}
  <p class="mt-1 text-sm text-slate-500">{metrics.progressPercentage.toFixed(1)}% complete</p>
{/if}

<!-- Line 108: High Confidence styling -->
<p class="mt-2 text-3xl font-bold {hasMatchResults ? 'text-green-600' : 'text-slate-400'}">

<!-- Lines 109-111: High Confidence subtitle -->
{#if hasMatchResults}
  <p class="mt-1 text-sm text-slate-500">{highPercentage}% of total</p>
{/if}

<!-- Line 121: Confidence Donut -->
{#if hasMatchResults}
  <ConfidenceDonut ... />
{:else}
  <!-- Empty state -->
{/if}

<!-- Lines 171-173: View Results button -->
{#if hasMatchResults}
  <Button variant="secondary" text="View Results" ... />
{/if}
```

### Files Affected

| File | Line | Change |
|------|------|--------|
| `src/routes/workspace/[id]/+page.svelte` | 28 | Replace `hasResults` with two flags |
| `src/routes/workspace/[id]/+page.svelte` | 93 | Use `hasCrops` |
| `src/routes/workspace/[id]/+page.svelte` | 97-111 | Use `hasMatchResults` |
| `src/routes/workspace/[id]/+page.svelte` | 121 | Use `hasMatchResults` |
| `src/routes/workspace/[id]/+page.svelte` | 171-173 | Use `hasMatchResults` |

---

## Issue #13: OCR Batching Threshold and Always-Batch Setting

**Discovered:** 2026-03-17
**Severity:** Low (Enhancement)
**Status:** ✅ Fixed (2026-03-26)

### Resolution

1. Changed `BATCH_THRESHOLD` from 10 to 5
2. Added `always_batch_ocr` feature flag (default: `True`)
3. Updated worker to check both threshold and flag
4. Exposed flag via `/config/features` and `/config/settings` endpoints

### Files Changed

| File | Change |
|------|--------|
| `backend/app/jobs/worker.py` | Changed `BATCH_THRESHOLD` to 5, added flag check |
| `backend/app/settings/env_settings.py` | Added `always_batch_ocr` field |
| `backend/app/routers/config_router.py` | Added `alwaysBatchOcr` to responses |
| `backend/tests/unit/jobs/test_batch_threshold.py` | NEW: 5 tests for batch threshold |

### Description
The OCR batching feature currently uses a threshold of 10 items before switching to batch mode. Users want:
1. Lower the threshold to 5 items
2. Add a settings flag to always use batching (bypass threshold)

### Current Implementation

**Threshold check** (`backend/app/jobs/worker.py:40, 240-249`):
```python
BATCH_THRESHOLD = 10

# In _run_ocr_phase():
if len(crops_to_process) >= BATCH_THRESHOLD:
    await self._run_batch_ocr(...)
else:
    await self._run_real_ocr(...)
```

**Feature flags** (`backend/app/settings/env_settings.py:49-55`):
```python
enable_simulation: bool
enable_beta_features: bool
enable_debug_mode: bool
demo_mode: bool
demo_reset: bool
```

### Proposed Changes

**Part 1: Lower batch threshold to 5**

```python
# worker.py:40
BATCH_THRESHOLD = 5  # Changed from 10
```

**Part 2: Add `alwaysBatchOcr` feature flag**

Backend changes:

```python
# env_settings.py - Add new field
always_batch_ocr: bool = Field(alias="FEATURE_ALWAYS_BATCH_OCR", default=True)
```

```python
# config_router.py - Add to FeatureFlagsResponse
alwaysBatchOcr: bool  # noqa: N815
```

```python
# worker.py - Update threshold check
if self.settings.always_batch_ocr or len(crops_to_process) >= BATCH_THRESHOLD:
    await self._run_batch_ocr(...)
else:
    await self._run_real_ocr(...)
```

Frontend changes:

Add toggle in `/workspace/settings` under Feature Flags section:
```svelte
<ToggleSwitch
  label="Always Use Batch OCR"
  description="Use batch API for all OCR requests (slower but cheaper)"
  bind:value={features.alwaysBatchOcr}
/>
```

### Design Decisions

| Question | Decision |
|----------|----------|
| UI Placement | **Global feature flag** - affects all campaigns |
| Provider Support | **All providers** - visible for all, silently ignored for non-OpenAI |
| Default Value | **`True`** - always batch by default (50% cost savings) |

### Files Affected

| File | Change |
|------|--------|
| `backend/app/jobs/worker.py:40` | Change BATCH_THRESHOLD to 5 |
| `backend/app/jobs/worker.py:240-249` | Add `always_batch_ocr` check |
| `backend/app/settings/env_settings.py` | Add `always_batch_ocr` field |
| `backend/app/routers/config_router.py` | Add to FeatureFlagsResponse |
| `frontend-svelt/src/routes/workspace/settings/+page.svelte` | Add toggle UI |

### Trade-offs

| Mode | Speed | Cost | Best For |
|------|-------|------|----------|
| Real-time OCR | Fast (parallel) | Higher | Small batches, quick results |
| Batch OCR | Slow (5-24h queue) | 50% cheaper | Large batches, overnight jobs |

---

## Issue #14: OCR Unique Constraint Violations + Duplicate Results

**Discovered:** 2026-03-17
**Severity:** High (Data Loss/Corruption)
**Status:** ✅ Fixed (Phase 12 - 2026-03-17)

### Symptoms
- Batch OCR failed with `'list index out of range'` error
- Sequential OCR fallback worked but hit rate limits (429 errors)
- Every OCR insert shows UNIQUE constraint error: `UNIQUE constraint failed: ocr_results.crop_id`
- Only 1 entry per crop saved (entry at index 0)
- Results page shows duplicate names (20 results, but same name repeated)
- Re-running same job creates cumulative duplicates
- Confusion: Users expect 5 unique names per crop, see only 1
- Data loss: 4 out of 5 entries lost per signature
- Cumulative duplicates: 1 crop × 5 runs = 5 duplicate results

### Root Cause Analysis

**1. Batch OCR Failure**
```
Batch OCR failed, falling back to sequential error='list index out of range'
```
Batch OCR parses results file expecting specific format, but parsing fails. Fallback to sequential processing.

**2. UNIQUE Constraint Design Issue**
```python
# ocr_result.py:13
crop_id: int = Field(foreign_key="petition_crops.id", unique=True, nullable=False)
```
This enforces 1:1 relationship between crop and OCR result. However:
- Each petition page (crop) contains 5 signatures
- OCR model returns all 5 signatures: `{"data": [{"Name": "...", "Address": "..."}, ...x5]}`
- Worker tries to store each as separate `OcrResult` with same `crop_id`

**3. Worker Processing Bug** (`worker.py:372-414`)
```python
for _entry_idx, entry in enumerate(ocr_entries):
    extracted_text = {...}

    existing_result = session.exec(
        select(OcrResult).where(OcrResult.crop_id == crop.id)
    ).first()
    if existing_result:
        continue  # Skips if ANY result exists for this crop

    ocr_result = OcrResult(crop_id=crop.id, ...)
    session.add(ocr_result)
    session.commit()
```
- Entry 0: No existing result → inserts successfully
- Entries 1-4: Find entry 0's result → `continue` (silently dropped)
- No error logged for entries 1-4

**4. Results Page Duplicates**
Campaign-level results endpoint (`campaign_router.py:360`) fetches all results from all jobs:
- Job 1: Creates 20 OcrResults (1 per crop)
- Job 2 (re-run): Creates 20 MORE OcrResults (duplicates)
- Job 3 (re-run): Creates 20 MORE OcrResults
- Total: 60 OcrResults for 20 crops (3x duplicates)

UI shows all 60, grouped by crop, showing same name 3 times.

**5. Matching Returning Same Voters**
All match results show identical predictions with 0.0 similarity:
```
"voter_name": "Erica Massey",
"voter_address": "6071 Martin Island",
"similarity_score": 0.0,
"confidence": "LOW"
```
This suggests matching is running but returning default/placeholder results.

### Proposed Fix

Store all 5 OCR entries per crop with an index to differentiate entries for reprocessing.

**Backend Changes:**
1. Remove `unique=True` from `crop_id` constraint
2. Add `ocr_index` column to `OcrResult` model
3. Update worker to store all 5 entries with index 0-4
4. Update matching service to handle indexed results
5. Add unique constraint on `(crop_id, ocr_index)`
6. Add migration for existing data
7. Update results UI to show all entries per crop
8. Add deduplication in results API for re-runs

9. Update metrics to count unique `crop_id` values, not total rows
10. Fix batch OCR parsing (separate issue)

11. Add `force_reprocess` flag to jobs (clear cache)

12. Update worker to check existing before insert
13. Update frontend to display entry index in results
14. Add UI to show all 5 entries per crop (expandable)
15. Update confidence donut to group by `ocr_result_id`
   not just `totalSignatures`

16. Update metrics to handle indexed results

**Frontend Changes:**
1. Update results table to show all entries per crop
2. Add expandable row to show all 5 signatures
3. Update confidence donut to count unique crops
4. Add UI feedback when viewing duplicates

5. Deduplicate results when multiple jobs exist for same crop

**Database Migration:**
```sql
-- Remove unique constraint, add ocr_index
ALTER TABLE ocr_results DROP CONSTRAINT IF EXISTS ocr_results_crop_id_key;
ALTER TABLE ocr_results ADD COLUMN ocr_index INTEGER DEFAULT 0;
ALTER TABLE ocr_results ADD CONSTRAINT ocr_results_crop_id_ocr_index_unique
    UNIQUE (crop_id, ocr_index);
```

**Files Affected**

| File | Change |
|------|--------|
| `backend/app/data/database/model/ocr_result.py` | Remove `unique=True`, add `ocr_index` |
| `backend/app/jobs/worker.py` | Store all 5 entries with index |
| `backend/app/routers/results_router.py` | Add deduplication query |
| `frontend-svelt/src/routes/workspace/[id]/results/+page.svelte` | Show all entries per crop |
| `backend/app/services/metrics.py` | Count unique crops, not total results |

---

## Issue #19: Aggressive Frontend Polling Storm

**Discovered:** 2026-03-18
**Severity:** Medium (Performance)
**Status:** ✅ Fixed (2026-03-18)

### Description

The frontend aggressively polls `/jobs` endpoint during job matching, creating excessive HTTP requests and overwhelming the backend logs. Different ports in logs are normal ephemeral TCP behavior, but the sheer request volume (hundreds in 48 minutes) is problematic.

### Symptoms
- Job matching phase takes ~48 minutes (15:36:58 to 16:24:48)
- Hundreds of `GET /jobs` requests in backend logs
- Requests appear to happen continuously with no 10-second gap
- Multiple ports (63148, 63427, etc.) are normal HTTP behavior but excessive

### Root Cause Analysis

Two frontend pages poll `/jobs`:

1. **Dashboard page** (`/workspace/[id]/+page.svelte`):
   - Line 23, 61: Polls `fetchMetrics` every 10s
   - Line 58: Calls `jobs.fetchAll()` once on mount

2. **Jobs page** (`/workspace/[id]/jobs/+page.svelte`):
   - Line 160: Polls `jobs.fetchAll()` every 10s

When both pages are open simultaneously, they poll `jobs.fetchAll()` every 10 seconds, causing double polling for Additionally, the dashboard also polls metrics separately.

**Expected requests at 10-second intervals:**
- Single page: ~6 requests/minute
- Both pages open: ~12 requests/minute (for jobs.fetchAll)

**Actual behavior:**
Based on log volume, requests appear more be happen much faster than 10 seconds, suggesting possible interval leak or multiple polling mechanisms.

### Fix Applied (2026-03-18)

**Part 1: Increased polling interval from 10s to 30s**

Both pages now poll at 30-second intervals instead of 10 seconds.

**Part 2: Stop polling when no active jobs**

Jobs page now only polls when there are active jobs in progress:

```svelte
const ACTIVE_JOB_STATES = ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED', 'MATCHING_PENDING', 'MATCHING'];
const POLL_INTERVAL_MS = 30000;

pollInterval = setInterval(() => {
    const hasActiveJobs = $jobs.jobs.some(j => ACTIVE_JOB_STATES.includes(j.status));
    if (hasActiveJobs) {
        jobs.fetchAll();
    }
}, POLL_INTERVAL_MS);
```

**Result:** 3x reduction in request frequency, and no polling when jobs are complete.

### Files Changed

| File | Change |
|------|--------|
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | Increase poll interval to 30s |
| `frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte` | Increase poll interval, 30s, stop when no active jobs |
| `frontend-svelt/src/stores/jobs.ts` | Add SSE for job list updates (optional) |

---

## Issue #16: DEVELOPER.md Out of Sync with PROGRESS.md

**Discovered:** 2026-03-18
**Severity:** Low (Documentation)
**Status:** ✅ Fixed (2026-03-18)

### Description

`openspec/DEVELOPER.md` shows Phases 8-12 as "📋 Not Started" but `.agent-workspace/problem/PROGRESS.md` shows them as "✅ Complete". This creates confusion about the actual project state.

### Current State

**DEVELOPER.md (lines 80-87):**
```
| Phase | Focus                         | Status         |
| 7     | Quick Fixes & Cleanup         | ✅ Complete    |
| 8     | Campaign List & Dashboard     | 📋 Not Started |  ← Incorrect
| 9     | Job Creation Flow (/jobs/new) | 📋 Not Started |  ← Incorrect
...
```

**PROGRESS.md (lines 12-19):**
```
| Phase | Status | Completion | Notes |
| Phase 7: Quick Fixes | ✅ Complete | 100% | ... |
| Phase 8: Campaign UI | ✅ Complete | 100% | ... |
| Phase 9: Job Creation | ✅ Complete | 100% | ... |
...
```

### Fix Applied

Updated `openspec/DEVELOPER.md` to show Phases 7-12 as complete and current status as "Post-MVP Polish".

### Files Changed

| File | Change |
|------|--------|
| `openspec/DEVELOPER.md` | Updated Phase 8-12 status to ✅ Complete, updated current status |

---

## Issue #17: Uncommitted Fixes Need to be Committed

**Discovered:** 2026-03-18
**Severity:** Medium (Process)
**Status:** ✅ Fixed (2026-03-18)

Multiple files contain uncommitted fixes for Issues #1, #9, #12, #14, #15. These changes implement critical functionality but are not in version control.

### Uncommitted Files (from `git diff --stat`)

| File | Changes | Related Issue |
|------|---------|---------------|
| `backend/app/data/database/model/jobs.py` | +3 | #1 |
| `backend/app/data/database/model/ocr_result.py` | +7/-1 | #14 |
| `backend/app/jobs/worker.py` | +57/-0 | #1, #14 |
| `backend/app/routers/job_router.py` | +18 | #1 |
| `backend/app/services/metrics.py` | +37/-0 | #15 |
| `backend/tests/integration/api/test_campaign_metrics.py` | +177 | #15 |
| `backend/tests/integration/api/test_jobs.py` | +287 | #1 |
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | +46 | #12 |
| `frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte` | +? | #9 |

### Fix Applied

All uncommitted changes were committed in 9 logical commits:

1. `564a872` - fix(ocr): add ocr_index to support multi-entry OCR results (Issue #14)
2. `4b80322` - fix(jobs): orphan detection, expanded cancel states, OCR caching (Issues #1, #14)
3. `cc877e1` - fix(metrics): deduplicate confidence counts by ocr_result_id (Issue #15)
4. `5faf57e` - fix(frontend): dashboard metrics and job creation UX (Issues #9, #12)
5. `8b2ca07` - feat(frontend): campaigns list enhancements (Phase 8)
6. `f1980cc` - feat(frontend): job details and settings enhancements (Phase 10-12)
7. `f613020` - feat(frontend): auth and layout polish (Phase 7-12)
8. `0a4c2e6` - feat(backend): config reset endpoint and OCR improvements (Phase 12)
9. `9c403cb` - docs: update documentation post-MVP (Phase 7-12)

---

## Issue #18: Flaky Test - Provider List Order Dependency

**Discovered:** 2026-03-18
**Severity:** Low (Test Quality)
**Status:** ✅ Fixed (2026-03-18)

### Description

`test_list_providers_shows_unconfigured_state` fails intermittently when run with full test suite but passes in isolation. This indicates test order dependency.

### Symptoms

```
# Full integration test run:
FAILED tests/integration/api/test_providers.py::TestListProviders::test_list_providers_shows_unconfigured_state

# Isolated run:
tests/integration/api/test_providers.py::TestListProviders::test_list_providers_shows_unconfigured_state PASSED
```

### Root Cause

Likely one of:
1. **Database state not cleaned between tests** - Previous test configures providers
2. **Shared fixture state** - Session or client state bleeding between tests

### Fix Applied

Added `session` fixture to tests that were missing it, ensuring database cleanup runs before each test:

```python
class TestListProviders:
    def test_list_providers_returns_all_supported(self, client, session):  # Added session
        ...

    def test_list_providers_shows_unconfigured_state(self, client, session):  # Added session
        ...
```

The `session` fixture already performs cleanup:
```python
@pytest.fixture
def session():
    init_db()
    with Session(engine) as session:
        session.query(LlmProviderConfig).delete()
        session.commit()
        yield session
```

### Files Affected

| File | Change |
|------|--------|
| `backend/tests/integration/api/test_providers.py` | Add explicit cleanup at test start |

---

## Issue #20: Typed Event Bus for Real-Time Updates

**Discovered:** 2026-03-18
**Severity:** Medium (Architecture)
**Status:** Open (Proposal)

### Description

Current SSE implementation is per-job only. For campaign-scoped real-time updates (all jobs in a campaign), we'd need a new endpoint. This proposes a **typed event bus** architecture that supports any future event types with topic-based subscriptions.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PUBLISHERS                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Worker   │  │ OCR      │  │ Upload   │  │ Matching Service │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       │             │             │                  │          │
└───────┼─────────────┼─────────────┼──────────────────┼──────────┘
        │             │             │                  │
        ▼             ▼             ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EVENT BUS (Core)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Topic Router                                            │    │
│  │  • campaign:{id}  → all events for campaign              │    │
│  │  • job:{id}       → all events for job                   │    │
│  │  • global         → system-wide events                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Event Registry (typed events)                          │    │
│  │  • JobStatusChanged, JobProgress, JobError              │    │
│  │  • OcrProgress, OcrComplete                             │    │
│  │  • MatchFound, MatchingComplete                         │    │
│  │  • UploadProgress, UploadComplete                       │    │
│  │  • MetricsUpdated                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SUBSCRIBERS                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ SSE Endpoint │  │ WebSocket    │  │ Future: Webhooks,    │  │
│  │ /events/stream│  │ (optional)   │  │ Message Queue, etc.  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

**1. Event Types (Registry)**

```python
# backend/app/events/event_types.py
from enum import Enum
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class EventType(str, Enum):
    # Job lifecycle
    JOB_STATUS_CHANGED = "job:status_changed"
    JOB_PROGRESS = "job:progress"
    JOB_ERROR = "job:error"

    # OCR
    OCR_PROGRESS = "ocr:progress"
    OCR_COMPLETE = "ocr:complete"

    # Matching
    MATCH_FOUND = "match:found"
    MATCHING_COMPLETE = "matching:complete"

    # Upload
    UPLOAD_PROGRESS = "upload:progress"
    UPLOAD_COMPLETE = "upload:complete"

    # Metrics
    METRICS_UPDATED = "metrics:updated"


class BaseEvent(BaseModel):
    event_type: EventType
    timestamp: datetime
    campaign_id: str | None = None
    job_id: int | None = None


class JobStatusEvent(BaseEvent):
    event_type: Literal[EventType.JOB_STATUS_CHANGED]
    status: str
    previous_status: str | None


class JobProgressEvent(BaseEvent):
    event_type: Literal[EventType.JOB_PROGRESS]
    processed: int
    total: int
    percentage: float


class MatchFoundEvent(BaseEvent):
    event_type: Literal[EventType.MATCH_FOUND]
    ocr_result_id: int
    voter_name: str
    confidence: str
```

**2. Event Bus (Core)**

```python
# backend/app/events/event_bus.py
import asyncio
from collections import defaultdict
from typing import AsyncGenerator
from .event_types import BaseEvent

class EventBus:
    """Typed publish-subscribe event bus with topic routing."""

    def __init__(self):
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def _get_topics(self, event: BaseEvent) -> list[str]:
        """Derive topics from event."""
        topics = ["global"]
        if event.campaign_id:
            topics.append(f"campaign:{event.campaign_id}")
        if event.job_id:
            topics.append(f"job:{event.job_id}")
        return topics

    async def publish(self, event: BaseEvent) -> None:
        """Publish event to all relevant topics."""
        topics = self._get_topics(event)
        message = event.model_dump_json()

        for topic in topics:
            for queue in list(self._subscribers.get(topic, set())):
                try:
                    await queue.put(message)
                except asyncio.QueueFull:
                    pass

    def subscribe(self, topic: str) -> asyncio.Queue:
        """Subscribe to a specific topic."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers[topic].add(queue)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from topic."""
        self._subscribers[topic].discard(queue)


event_bus = EventBus()
```

**3. SSE Endpoint (Subscriber)**

```python
# backend/app/routers/events_router.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/campaigns/{campaign_id}/stream")
async def campaign_event_stream(campaign_id: str) -> StreamingResponse:
    """SSE stream for all events in a campaign."""

    async def generate():
        queue = event_bus.subscribe(f"campaign:{campaign_id}")
        try:
            while True:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(f"campaign:{campaign_id}", queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**4. Publishing from Worker**

```python
# backend/app/jobs/worker.py
from app.events.event_bus import event_bus
from app.events.event_types import JobProgressEvent, JobStatusEvent

class JobWorker:
    async def _run_matching_phase(self, ...):
        for i, ocr_result in enumerate(ocr_results):
            # ... do matching ...

            await event_bus.publish(JobProgressEvent(
                event_type=EventType.JOB_PROGRESS,
                campaign_id=str(job.campaign_id),
                job_id=job.id,
                processed=i + 1,
                total=len(ocr_results),
                percentage=((i + 1) / len(ocr_results)) * 100
            ))
```

**5. Frontend Integration**

```typescript
// frontend-svelt/src/lib/stores/events.ts
export function connectToCampaign(campaignId: string) {
  const baseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8080';
  const eventSource = new EventSource(
    `${baseUrl}/api/events/campaigns/${campaignId}/stream`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.event_type) {
      case 'job:status_changed':
        jobs.updateJobInList(data.job_id, { status: data.status });
        break;
      case 'job:progress':
        jobs.updateJobProgress(data.job_id, data.percentage);
        break;
      case 'metrics:updated':
        // Update dashboard metrics
        break;
    }
  };

  return () => eventSource.close();
}
```

### Effort Estimate

| Component | Effort |
|-----------|--------|
| Event types + registry | 1 hour |
| Event bus core | 1 hour |
| SSE endpoint refactor | 1 hour |
| Worker integration | 1 hour |
| Frontend store | 1 hour |
| Testing | 1 hour |
| **Total** | **~6 hours** |

### Benefits

1. **Extensible**: Add new event types without touching SSE code
2. **Decoupled**: Publishers don't know about subscribers
3. **Typed**: Pydantic models ensure schema consistency
4. **Future-proof**: Can add WebSocket, webhooks, message queue subscribers later
5. **Topic-based**: Subscribe to campaign, job, or global scope

### Migration Path

1. **Phase 1**: Implement event bus alongside existing SSE
2. **Phase 2**: Refactor worker to publish events
3. **Phase 3**: Add campaign-scoped SSE endpoint
4. **Phase 4**: Frontend adopts new event stream, removes polling
5. **Phase 5**: Deprecate old per-job SSE endpoint

### Files Affected

| File | Change |
|------|--------|
| `backend/app/events/event_types.py` | NEW: Typed event definitions |
| `backend/app/events/event_bus.py` | NEW: Core pub-sub implementation |
| `backend/app/routers/events_router.py` | NEW: SSE endpoints for topics |
| `backend/app/jobs/worker.py` | Publish events on progress |
| `frontend-svelt/src/lib/stores/events.ts` | NEW: Event stream store |

---

## Issue #21: Inconsistent Sort Icons in Table Headers

**Discovered:** 2026-03-18
**Severity:** Low (UI Polish)
**Status:** Open

### Description

The campaigns list table (and any table using the `Table` component) uses inconsistent icons for sort indicators:
- **Sorted ascending**: Single chevron up (↑)
- **Sorted descending**: Single chevron down (↓)
- **Not sorted**: Double arrows icon (↕) that looks different

### Current Implementation

`Table.svelte:157-172` uses three different SVG icons:

```svelte
{#if sortConfig && sortConfig.key === column.key}
    {#if sortConfig.direction === 'asc'}
        <!-- Single chevron up -->
        <path d="M5 15l7-7 7 7" />
    {:else}
        <!-- Single chevron down -->
        <path d="M19 9l-7 7-7-7" />
    {/if}
{:else}
    <!-- Double arrows (different style) -->
    <path d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
{/if}
```

### Visual Inconsistency

```
Current:
  Unsorted: ↕ (double arrows, thick)
  Ascending: ˄ (chevron, thin)
  Descending: ˅ (chevron, thin)

Expected (consistent chevrons):
  Unsorted: ⇅ (chevrons up-down)
  Ascending: ˄ (chevron up)
  Descending: ˅ (chevron down)
```

### Proposed Fix

Replace the unsorted icon with a chevrons-up-down icon to match the sorted state icons:

```svelte
{:else}
    <!-- Chevrons up-down to match sorted icon style -->
    <svg class="w-4 h-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5 5 5M7 13l5 5 5-5" />
    </svg>
{/if}
```

Or use Heroicons for consistency (if already using icon library):

```svelte
{:else}
    <svg class="w-4 h-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7l4-4 4 4m0 10l-4 4-4-4" />
    </svg>
{/if}
```

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/components/ui/Table.svelte` | Update unsorted sort icon to match chevron style |

---

## Issue #22: API Keys Exposed in Backend Logs

**Discovered:** 2026-03-18
**Severity:** High (Security)
**Status:** ✅ Fixed (2026-03-18)

### Description

Provider API keys were being logged in plaintext in backend logs, creating a security risk. API keys could appear in:
- Log statements during provider configuration
- Debug output when creating OCR clients
- Error messages that include configuration details

### Risk

- API keys in logs could be accessed by unauthorized users
- Logs may be shipped to external monitoring services
- Compliance violations (SOC2, PCI-DSS, etc.)

### Fix Applied

Added a `redact_api_keys` processor to structlog configuration that:

1. **Detects sensitive field names** using regex patterns:
   - `api_key`, `apiKey`, `api-key`
   - `secret`, `password`, `token`, `credential`

2. **Detects API key value patterns**:
   - OpenAI format: `sk-{20+ chars}`
   - Generic long alphanumeric strings (32+ chars)

3. **Obfuscates values** showing only first/last 4 characters:
   - `sk-abc123...` → `sk-ab***REDACTED***wxyz`
   - `32charkey...` → `32ch***REDACTED***1234`

### Files Changed

| File | Change |
|------|--------|
| `backend/app/logger_config/app_logger.py` | Added `redact_api_keys` processor and `SENSITIVE_FIELD_PATTERNS` |

### Example Output

**Before:**
```json
{"api_key": "sk-proj-abc123defghijklmnopqrstuvwxyz", "provider": "openai"}
```

**After:**
```json
{"api_key": "sk-p***REDACTED***wxyz", "provider": "openai"}
```

---

## Issue #23: Events Router Missing /api Prefix

**Discovered:** 2026-03-25 (Code Review)
**Severity:** High (Breaking Change)
**Status:** ✅ Not a Bug - By Design (2026-03-25)

### Description

The events router is mounted without the `/api` prefix, causing a mismatch with the design spec and breaking frontend integration.

### Resolution

This is intentional design, not a bug:

- **Backend**: Events mounted at `/events/...` (not under `/api`)
- **Frontend**: Connects to `/events/campaigns/{id}/stream` (events.ts:95)

Rationale: SSE endpoints are distinct from REST API endpoints and don't need the `/api` prefix. Both frontend and backend are consistent with this design.

---

## Issue #24: SSE Manager Deprecation Path Unclear

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Medium (Maintenance)
**Status:** 📝 Documented (2026-03-25)

### Description

Two SSE systems coexist in the codebase:
1. **Old**: `backend/app/events/sse_manager.py` - Per-job SSE with manual connection management
2. **New**: `backend/app/events/transports/sse.py` - Event bus backed SSE with topic routing

Both are exported from `__init__.py` with no deprecation warning or migration documentation.

### Resolution: Dual Architecture is Intentional

After analysis, the dual SSE architecture serves different purposes:

| System | Endpoint | Scope | Use Case |
|--------|----------|-------|----------|
| Event Bus | `/events/campaigns/{id}/stream` | Campaign-wide | Dashboard, jobs list, metrics |
| Per-Job SSE | `/api/jobs/{id}/status` | Single job | Job detail page (focused monitoring) |

**Frontend Usage:**
- `events.ts` → Campaign layout (connects on mount for all campaign pages)
- `jobs.connectToJob()` → Job detail page (`jobs/[job_id]/+page.svelte:14`)

Both systems remain because:
1. Job detail page needs focused SSE for detailed job monitoring
2. Campaign layout needs broad event stream for dashboard/jobs list

### Decision: Keep Both, Document Usage

No deprecation needed. Instead:
1. Add ADR documenting the dual architecture
2. Add comments to `jobs.ts` explaining when to use each
3. Update FEEDBACK.md #4 to close as "documented"

### Files Changed

| File | Change |
|------|--------|
| `openspec/adr/002-sse-architecture.md` | NEW: Document dual SSE architecture |
| `frontend-svelt/src/lib/stores/jobs.ts` | Add comment explaining connectToJob usage |

---

## Issue #25: Event Bus Integration Test Missing

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Medium (Test Coverage)
**Status:** ✅ Fixed (2026-03-25)

### Description

The implementation plan calls for `backend/tests/integration/api/test_events.py` but this file doesn't exist. Unit tests exist, but no integration test validates the full SSE endpoint flow.

### Resolution

Integration test file created at `backend/tests/integration/api/test_events.py` with tests for:
- Campaign stream endpoint returns correct headers
- Events published to bus appear in SSE stream

---

## Issue #26: PROGRESS.md Out of Sync with Implementation

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Low (Documentation)
**Status:** ✅ Fixed (2026-03-25)

### Description

`openspec/PROGRESS.md` task statuses don't reflect actual implementation state.

### Resolution

PROGRESS.md was updated on 2026-03-25 to reflect current state:
- Event Bus Phase marked as ✅ Complete
- All task statuses updated
- Current work section updated

---

## Issue #27: TypeScript Test Mocks Out of Sync with Store Types

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Medium (Test Quality)
**Status:** ✅ Fixed (2026-03-25)

### Description

Frontend TypeScript check fails with 87 errors, primarily in test files. The `CampaignsState` type was updated to include a `metrics` property, but test mocks weren't updated to match.

### Affected Files

- `frontend-svelt/tests/unit/routes/campaigns-page.test.ts` (formerly workspace-page.test.ts)

### Fix Applied

1. Fixed `vi.mock` pattern to use factory function correctly (was missing second argument)
2. Updated mock state to include `metrics: {}` property
3. Import mocked module after `vi.mock` call to enable proper hoisting

```typescript
vi.mock('$lib/stores/campaigns', () => ({
	campaigns: {
		subscribe: vi.fn(),
		create: vi.fn(),
		delete: vi.fn(),
		fetchAll: vi.fn(),
		clearError: vi.fn(),
		reset: vi.fn(),
		handleMetricsEvent: vi.fn()
	}
}));

import { campaigns } from '$lib/stores/campaigns';
```

### Result

- `bun run check`: 0 errors (was 87)
- Store unit tests: 27 passing

---

## Issue #28: SSE Transport Code Duplication

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Medium (Maintainability)
**Status:** Open

### Description

`sse.py` has two nearly identical methods (`subscribe_to_campaign` and `subscribe_to_job`) with duplicate `generate()` inner functions.

### Affected Files

- `backend/app/events/transports/sse.py` - lines 21-34, 51-63

### Current Code

Both methods contain identical generator logic:

```python
async def generate():
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {message}\n\n"
            except TimeoutError:
                yield ": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        event_bus.unsubscribe(topic, queue)
        self._active_queues.discard(queue)
```

### Recommended Fix

Extract to shared helper:

```python
def _create_stream_generator(self, topic: str, queue: asyncio.Queue):
    async def generate():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                except TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(topic, queue)
            self._active_queues.discard(queue)
    return generate()
```

---

## Issue #29: E2E Tests Fragile (Skip on Empty Data)

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Medium (Test Quality)
**Status:** Open

### Description

`event-stream.spec.ts` tests skip when no campaigns exist in the database. All 3 tests can silently skip, providing false confidence.

### Affected Files

- `frontend-svelt/tests/e2e/event-stream.spec.ts` - lines 11-14, 48-50, 73-76

### Current Behavior

```typescript
const isVisible = await campaignLink.isVisible({ timeout: 5000 }).catch(() => false);

if (!isVisible) {
    test.skip();  // Tests silently skip
    return;
}
```

### Problem

- Fresh database = all tests skip
- CI with clean state = no actual test coverage
- No indication that tests didn't run

### Recommended Fix

Seed test data before running tests, or use Playwright fixtures:

```typescript
test.describe('Event Stream Integration', () => {
    test.beforeEach(async ({ page }) => {
        // Seed a test campaign via API
        await page.request.post('/api/campaigns', { ... });
    });

    test('campaign page establishes SSE connection', async ({ page }) => {
        // Now test has guaranteed data
    });
});
```

---

## Issue #30: Inconsistent Event ID Types

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Low (Type Safety)
**Status:** 📝 By Design

### Description

`event_types.py` uses different types for `campaign_id` (str) and `job_id` (int), creating inconsistency in serialization and comparison.

### Affected Files

- `backend/app/events/event_types.py` - lines 21-22

### Current Code

```python
class BaseEvent(BaseModel):
    campaign_id: str | None = None  # UUID as string
    job_id: int | None = None       # Database integer
```

### Resolution: By Design

After review, this is **correct by design**:

1. **Campaign IDs are UUIDs** - Stored as 32-character strings without dashes in the database
2. **Job IDs are integers** - Auto-increment primary keys

The types correctly match the underlying data model:
- `campaigns.id` → UUID → Python `str`
- `matcher_job.id` → INTEGER → Python `int`

Changing job_id to str would require converting all integer IDs to strings, which would be inconsistent with the database schema and add unnecessary conversion overhead.

---

## Issue #31: Late Import in Worker

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Low (Code Style)
**Status:** Open

### Description

`worker.py` imports `MetricsService` inside `_compute_job_metrics()` method rather than at module level.

### Affected Files

- `backend/app/jobs/worker.py` - line 261

### Current Code

```python
def _compute_job_metrics(self, session: Session, job: MatcherJob) -> dict:
    from app.services.metrics import MetricsService  # ← Late import

    metrics_service = MetricsService(session)
    ...
```

### Concerns

- Unusual pattern in Python (common in JS to avoid circular deps)
- No obvious circular dependency issue here
- Slight runtime overhead on each call

### Recommended Fix

Move to top-level import:

```python
# At top of worker.py
from app.services.metrics import MetricsService
```

Or if there's a circular dependency, add a comment explaining why:

```python
# Late import to avoid circular dependency with services module
from app.services.metrics import MetricsService
```

---

## Issue #28: SSE Transport Code Duplication

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Medium (Code Quality)
**Status:** ✅ Fixed (2026-03-25)

### Description

`subscribe_to_campaign()` and `subscribe_to_job()` in `sse.py` had identical generator logic, creating code duplication.

### Affected Files

- `backend/app/events/transports/sse.py` - lines 21-34, 51-63

### Fix Applied

Extracted shared generator logic to `_create_stream_generator()` helper method:

```python
class SSETransport(EventTransport):
	SSE_HEADERS = {
		"Cache-Control": "no-cache",
		"Connection": "keep-alive",
		"X-Accel-Buffering": "no",
	}

	async def _create_stream_generator(self, topic: str, queue: asyncio.Queue):
		"""Create SSE generator for a topic subscription."""
		try:
			while True:
				try:
					message = await asyncio.wait_for(queue.get(), timeout=30.0)
					yield f"data: {message}\n\n"
				except TimeoutError:
					yield ": heartbeat\n\n"
		except asyncio.CancelledError:
			pass
		finally:
			event_bus.unsubscribe(topic, queue)
			self._active_queues.discard(queue)

	async def subscribe_to_campaign(self, campaign_id: str) -> StreamingResponse:
		topic = f"campaign:{campaign_id}"
		queue = event_bus.subscribe(topic)
		self._active_queues.add(queue)
		return StreamingResponse(
			self._create_stream_generator(topic, queue),
			media_type="text/event-stream",
			headers=self.SSE_HEADERS,
		)

	async def subscribe_to_job(self, job_id: int) -> StreamingResponse:
		topic = f"job:{job_id}"
		queue = event_bus.subscribe(topic)
		self._active_queues.add(queue)
		return StreamingResponse(
			self._create_stream_generator(topic, queue),
			media_type="text/event-stream",
			headers=self.SSE_HEADERS,
		)
```

### Files Changed

| File | Change |
|------|--------|
| `backend/app/events/transports/sse.py` | Extracted `_create_stream_generator()`, added `SSE_HEADERS` constant |

---

## Issue #29: E2E Tests Fragile (Skip on Empty)

**Discovered:** 2026-03-25 (Code Review Pass 2)
**Severity:** Medium (Test Quality)
**Status:** ✅ Fixed (2026-03-25)

### Description

E2E tests in `event-stream.spec.ts` skip when no campaigns exist, making tests unreliable in CI/CD environments with fresh databases.

### Affected Files

- `frontend-svelt/tests/e2e/event-stream.spec.ts`

### Fix Applied

Created test fixtures that seed a campaign before each test:

1. **New fixture file** (`tests/e2e/fixtures.ts`):
   - Creates API request context
   - Seeds test campaign via `POST /api/campaigns`
   - Cleans up campaign after test

2. **Updated event-stream.spec.ts**:
   - Uses `seededCampaign` fixture instead of searching for existing campaigns
   - Removed all `test.skip()` calls

### Files Changed

| File | Change |
|------|--------|
| `frontend-svelt/tests/e2e/fixtures.ts` | NEW: Test fixtures with seeded campaigns |
| `frontend-svelt/tests/e2e/event-stream.spec.ts` | Use fixtures instead of skipping on empty |

---

## Issue #32: No Event Validation Before Store Update

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Low (Type Safety)
**Status:** Open

### Description

In `events.ts:127-128`, the event handler parses JSON and passes it directly to `handleEvent()` without validating the event shape. Malformed or unexpected events could cause silent failures or incorrect state updates.

```typescript
eventSource.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data) as AppEvent;
        handleEvent(data);  // No validation of event shape
    } catch (e) {
        console.error('Failed to parse event:', e);
    }
};
```

### Proposed Fix

Add runtime validation before processing:

```typescript
function isValidAppEvent(data: unknown): data is AppEvent {
    if (typeof data !== 'object' || data === null) return false;
    const event = data as Record<string, unknown>;
    return (
        typeof event.event_id === 'string' &&
        typeof event.event_type === 'string' &&
        ['job:status_changed', 'job:progress', 'metrics:updated'].includes(event.event_type as string)
    );
}

eventSource.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (isValidAppEvent(data)) {
            handleEvent(data);
        } else {
            console.warn('Received malformed event:', data);
        }
    } catch (e) {
        console.error('Failed to parse event:', e);
    }
};
```

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/stores/events.ts` | Add `isValidAppEvent()` validation |

---

## Issue #33: Test Class Attribute Mutation

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Low (Test Quality)
**Status:** Open

### Description

In `test_event_bus.py:75-82`, the test mutates `EventBus.MAX_QUEUE_SIZE` directly on the class:

```python
def test_queue_full_drops_gracefully(self):
    bus = EventBus()
    bus.MAX_QUEUE_SIZE = 1  # Mutates instance, not class
    ...
```

While this happens to work (instance attribute shadows class attribute), it's fragile and could cause issues if tests run in parallel or if the implementation changes to use the class attribute directly.

### Proposed Fix

Use pytest fixture or mock to safely override the class attribute:

```python
def test_queue_full_drops_gracefully(self):
    with patch.object(EventBus, 'MAX_QUEUE_SIZE', 1):
        bus = EventBus()
        queue = bus.subscribe("global")
        queue.put_nowait("{}")
        asyncio.run(bus.publish(JobStatusEvent(job_id=1, status="MATCHING")))
```

### Files Affected

| File | Change |
|------|--------|
| `backend/tests/unit/events/test_event_bus.py` | Use `patch.object` for `MAX_QUEUE_SIZE` |

---

## Issue #34: E2E Tests Don't Verify Actual Job Events

**Discovered:** 2026-03-25 (Code Review)
**Severity:** Low (Test Coverage)
**Status:** ✅ Fixed (2026-03-26)

### Resolution

Added 2 new E2E tests to verify job event stream functionality:
1. `job status updates via SSE trigger UI refresh` - Verifies SSE connection status on jobs page
2. `job progress events update job details` - Verifies job page rendering and event handler registration

### Files Changed

| File | Change |
|------|--------|
| `frontend-svelt/tests/e2e/event-stream.spec.ts` | Added Job Event Stream test suite with 2 tests |

### Description

The E2E tests in `event-stream.spec.ts` only verify:
1. SSE connection is established
2. Jobs page loads
3. Event store status handling

They don't verify that actual job events (status changes, progress, metrics) are received and processed correctly.

### Current Test Coverage

```typescript
// Only checks if URL is requested, not event content
page.on('request', (request) => {
    if (request.url().includes('/events/campaigns/') && request.url().includes('/stream')) {
        eventSourceConnected = true;
    }
});
```

### Proposed Enhancement

Add test that triggers a job and verifies events:

```typescript
test('receives job status event when job starts', async ({ page, seededCampaign }) => {
    // Create a job via API
    const jobResponse = await page.request.post(`/api/jobs`, {
        data: { campaign_id: seededCampaign.id }
    });

    // Listen for event
    let receivedEvent: AppEvent | null = null;
    await page.exposeFunction('handleEvent', (event: AppEvent) => {
        receivedEvent = event;
    });

    await page.evaluate(() => {
        window.addEventListener('votecatcher:job:status', (e) => {
            (window as any).handleEvent(e.detail);
        });
    });

    // Start the job
    await page.request.post(`/api/jobs/${jobResponse.id}/start`);

    // Wait for event
    await page.waitForFunction(() => (window as any).receivedEvent !== null);

    expect(receivedEvent?.event_type).toBe('job:status_changed');
});
```

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/tests/e2e/event-stream.spec.ts` | Add job event verification tests |

---

## Issue #35: Race Condition in Event Store Disconnect

**Discovered:** 2026-03-25 (Code Review Pass 4)
**Severity:** Medium (Reliability)
**Status:** Open

### Domain Context

**Bounded Context:** Campaign Real-Time Updates

The Event Store aggregate manages the lifecycle of SSE connections for campaign-scoped real-time updates. When a user navigates away from a campaign workspace, the connection must be cleanly terminated to prevent resource leaks and spurious reconnection attempts.

### Behavior Specification (BDD)

```gherkin
Feature: Event Store Connection Lifecycle
  As a user navigating between campaigns
  I want my event connections to cleanly disconnect
  So that I don't receive stale events or waste resources

  Scenario: User navigates away from campaign during reconnection delay
    Given I am viewing campaign "abc-123"
    And the SSE connection has failed
    And a reconnection is scheduled in 2 seconds
    When I navigate to the campaigns list
    Then no reconnection attempt should occur
    And the event source should be null

  Scenario: Rapid navigation between campaigns
    Given I am viewing campaign "abc-123"
    And the SSE connection is active
    When I navigate to campaign "def-456" within 100ms
    Then the old connection for "abc-123" should be closed
    And a new connection for "def-456" should be established
    And no orphaned connections should remain
```

### Current Implementation Issue

**Location:** `frontend-svelt/src/lib/stores/events.ts:115-122` and `+layout.svelte:39-44`

```typescript
// events.ts:115-122 - Reconnection logic
reconnectTimeout = setTimeout(() => {
    if (currentCampaignId) {
        doConnect(currentCampaignId);
    }
}, delay);

// +layout.svelte:39-44 - Cleanup on unmount
return () => {
    events.disconnect();
    // But reconnectTimeout may still be pending!
};
```

**The Problem:**
1. `disconnect()` clears `currentCampaignId = null` and calls `eventSource.close()`
2. But `reconnectTimeout` is cleared ONLY if `eventSource` exists
3. If called during error state, `eventSource` is null but `reconnectTimeout` may be pending
4. The timeout callback checks `currentCampaignId` (now null) - safe, but relies on implicit check

### Root Cause Analysis

The `disconnect()` method has a subtle ordering issue:

```typescript
disconnect() {
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);  // ✓ Clears timeout
        reconnectTimeout = null;
    }
    if (eventSource) {
        eventSource.close();  // Only clears if exists
        eventSource = null;
    }
    currentCampaignId = null;  // ✓ Always cleared
    set({ status: 'disconnected', ... });
}
```

The implementation is actually correct - `reconnectTimeout` IS cleared. However, the code structure makes this hard to verify, and the `onerror` handler (lines 103-123) has complex state mutations that could race.

### Recommended Fix

**Option A: Add explicit cancelled flag (Defensive)**

```typescript
function createEventStore() {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let currentCampaignId: string | null = null;
    let isCancelled = false;  // NEW: Explicit cancellation flag

    function doConnect(campaignId: string) {
        isCancelled = false;  // Reset on new connection
        // ... existing code ...
    }

    eventSource.onerror = () => {
        // ... existing code ...
        reconnectTimeout = setTimeout(() => {
            if (currentCampaignId && !isCancelled) {  // CHECK: not cancelled
                doConnect(currentCampaignId);
            }
        }, delay);
    };

    disconnect() {
        isCancelled = true;  // Signal cancellation first
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
        // ... rest unchanged ...
    }
}
```

**Option B: Use AbortController pattern (Cleaner)**

```typescript
function createEventStore() {
    let abortController: AbortController | null = null;

    function doConnect(campaignId: string) {
        abortController = new AbortController();
        const signal = abortController.signal;

        eventSource = new EventSource(url);

        eventSource.onerror = () => {
            if (signal.aborted) return;  // Early exit if cancelled
            // ... reconnection logic ...
        };
    }

    disconnect() {
        abortController?.abort();  // Single cancellation point
        // ... cleanup ...
    }
}
```

### Impact on Domain

| Stakeholder | Impact |
|-------------|--------|
| **User** | Prevents confusing state where old campaign events arrive |
| **System** | Prevents connection leaks and memory growth |
| **Developer** | Easier to reason about connection lifecycle |

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/stores/events.ts` | Add `isCancelled` flag or use `AbortController` |
| `frontend-svelt/tests/unit/stores/events.test.ts` | NEW: Add lifecycle tests |

### Acceptance Criteria

- [ ] Given a pending reconnection, when disconnect is called, then no reconnection occurs
- [ ] Given rapid navigation, when switching campaigns, then only one active connection exists
- [ ] Unit tests verify connection lifecycle edge cases

---

## Issue #36: Event Source Inference Performance

**Discovered:** 2026-03-25 (Code Review Pass 4)
**Severity:** Low (Performance)
**Status:** Open

### Domain Context

**Bounded Context:** Event Publishing

Every domain event published to the Event Bus includes a `source` attribute identifying the originating component (e.g., `workers.JobWorker._run_matching_phase`). This is valuable for debugging and observability but has a performance cost.

### Behavior Specification (BDD)

```gherkin
Feature: Event Source Attribution
  As a developer debugging event flows
  I want each event to identify its source
  So that I can trace event origins in logs

  Scenario: Publishing events at high volume
    Given the system is processing 1000 OCR results
    When each result triggers a progress event
    Then source inference should not add significant latency
    And each event should have an accurate source attribute
```

### Current Implementation

**Location:** `backend/app/events/event_bus.py:19-36`

```python
def _infer_source(self, skip_frames: int = 2) -> str:
    """Derive source from callsite: 'module.function' or 'module.Class.method'"""
    frame = inspect.currentframe()
    for _ in range(skip_frames):
        frame = frame.f_back if frame else None

    if not frame:
        return "unknown"

    module = inspect.getmodule(frame)
    module_name = module.__name__.replace("app.", "") if module else "unknown"
    func_name = frame.f_code.co_name

    if "self" in frame.f_locals:
        class_name = frame.f_locals["self"].__class__.__name__
        return f"{module_name}.{class_name}.{func_name}"

    return f"{module_name}.{func_name}"
```

**Performance Characteristics:**
- `inspect.currentframe()` - Fast (C-level)
- `inspect.getmodule()` - Slower (filesystem lookup first call, cached after)
- String operations - Negligible

### Analysis

The actual impact is likely minimal because:
1. Events are published at most every few seconds during normal operation
2. Python's module cache speeds up subsequent `getmodule()` calls
3. The hot path (matching) doesn't publish per-result, only per-batch

However, during stress tests or batch processing, this could add up.

### Recommended Fix

**Option A: LRU Cache (Simple)**

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def _get_module_name(frame_code_id: int) -> str:
    # Cache by frame code object ID
    ...
```

**Option B: Memoize on First Call Per Module (Better)**

```python
class EventBus:
    _module_cache: dict[int, str] = {}

    def _infer_source(self, skip_frames: int = 2) -> str:
        frame = inspect.currentframe()
        for _ in range(skip_frames):
            frame = frame.f_back if frame else None

        if not frame:
            return "unknown"

        code_id = id(frame.f_code)
        if code_id in self._module_cache:
            return self._module_cache[code_id]

        # Compute and cache
        module = inspect.getmodule(frame)
        module_name = module.__name__.replace("app.", "") if module else "unknown"
        func_name = frame.f_code.co_name

        if "self" in frame.f_locals:
            class_name = frame.f_locals["self"].__class__.__name__
            source = f"{module_name}.{class_name}.{func_name}"
        else:
            source = f"{module_name}.{func_name}"

        self._module_cache[code_id] = source
        return source
```

**Option C: Accept Current Implementation (YAGNI)**

Given the low event volume, this optimization may be premature. Add a performance test first to verify if this is actually a bottleneck.

### Files Affected

| File | Change |
|------|--------|
| `backend/app/events/event_bus.py` | Add caching to `_infer_source()` |
| `backend/tests/performance/test_event_throughput.py` | NEW: Benchmark event publishing |

### Acceptance Criteria

- [ ] Given 10,000 events, when published in sequence, source inference adds < 100ms total
- [ ] Memory usage of cache is bounded
- [ ] Existing tests continue to pass

---

## Issue #37: Heartbeat Not Acknowledged by Client

**Discovered:** 2026-03-25 (Code Review Pass 4)
**Severity:** Low (Observability)
**Status:** 📝 By Design

### Domain Context

**Bounded Context:** SSE Transport Layer

The SSE transport sends heartbeat comments (`: heartbeat\n\n`) every 30 seconds to keep connections alive through proxies. However, the client never acknowledges or validates these heartbeats, missing an opportunity for health monitoring.

### Behavior Specification (BDD)

```gherkin
Feature: SSE Connection Health Monitoring
  As a system operator
  I want to know if SSE connections are healthy
  So that I can detect network issues proactively

  Scenario: Heartbeat received successfully
    Given an active SSE connection to campaign "abc-123"
    When the server sends a heartbeat comment
    Then the client should record the last heartbeat time
    And the connection status should remain "connected"

  Scenario: Heartbeat not received for 90 seconds
    Given an active SSE connection to campaign "abc-123"
    When no heartbeat is received for 90 seconds
    Then the client should log a warning
    And optionally attempt reconnection
```

### Current Implementation

**Server (Backend):** `backend/app/events/transports/sse.py:28-29`

```python
except TimeoutError:
    yield ": heartbeat\n\n"  # SSE comment - ignored by EventSource
```

**Client (Frontend):** `frontend-svelt/src/lib/stores/events.ts:125-132`

```typescript
eventSource.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data) as AppEvent;
        handleEvent(data);
    } catch (e) {
        console.error('Failed to parse event:', e);
    }
};
```

**The Gap:**
- SSE comments (`: heartbeat`) are ignored by `EventSource.onmessage`
- They can only be detected via `EventSource.onopen` (which fires once) or by monitoring `readyState`
- No timestamp tracking for last activity

### Recommended Fix

**Option A: Track last activity timestamp**

```typescript
function createEventStore() {
    let lastActivity: number = Date.now();

    const { subscribe, set, update } = writable<EventStoreState>({
        status: 'disconnected',
        lastEvent: null,
        reconnectAttempts: 0,
        lastHeartbeat: null  // NEW
    });

    eventSource.onmessage = (event) => {
        lastActivity = Date.now();
        // ... existing code ...
    };

    // Periodic health check
    setInterval(() => {
        const now = Date.now();
        const idleTime = now - lastActivity;

        if (idleTime > 90000 && eventSource?.readyState === EventSource.OPEN) {
            console.warn('No SSE activity for 90 seconds, connection may be stale');
            // Optionally trigger reconnect
        }
    }, 30000);
}
```

**Option B: Use named events for heartbeats (requires backend change)**

Backend sends:
```python
yield f"event: heartbeat\ndata: {timestamp}\n\n"
```

Frontend listens:
```typescript
eventSource.addEventListener('heartbeat', (event) => {
    update(s => ({ ...s, lastHeartbeat: new Date(event.data) }));
});
```

**Option C: Accept current implementation (YAGNI)**

The 30-second timeout with reconnection logic already handles stale connections. Heartbeat monitoring adds complexity without clear benefit.

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/stores/events.ts` | Add `lastActivity` tracking and health check |
| `backend/app/events/transports/sse.py` | (Option B only) Use named event for heartbeats |

### Acceptance Criteria

- [ ] Given an active connection, when 90 seconds pass without activity, then a warning is logged
- [ ] Connection status accurately reflects health state
- [ ] No spurious reconnections during normal operation

### Resolution: By Design

After review, the current implementation is **correct by design**:

1. **SSE Comments are Handled by Browser**: The `: heartbeat\n\n` format is an SSE comment that is automatically handled by the browser's EventSource implementation. Comments don't trigger `onmessage` events - they're processed internally as keep-alives.

2. **Existing Reconnection Logic is Sufficient**: The 30-second timeout with exponential backoff reconnection (max 5 attempts) already handles stale connections:
   - If no data received for 30 seconds, a heartbeat is sent
   - If connection drops, `onerror` triggers reconnection with backoff
   - Max reconnect attempts prevent infinite retry loops

3. **Option C (Accept Current Implementation) is Correct**: Adding explicit heartbeat acknowledgment would add complexity without clear benefit. The browser's EventSource already handles connection health monitoring through:
   - `readyState` property
   - `onerror` event for connection failures
   - Automatic reconnection by the browser

**No changes required.** The existing implementation correctly handles connection health through standard SSE mechanisms.

---

## Issue #38: SSE Transport Unit Tests Missing

**Discovered:** 2026-03-25 (Code Review Pass 4)
**Severity:** Medium (Test Coverage)
**Status:** ✅ Fixed (2026-03-26)

### Domain Context

**Bounded Context:** Event Transport Layer

The SSE Transport is a critical infrastructure component that bridges the Event Bus domain to HTTP clients. It handles:
- Connection lifecycle (subscribe, unsubscribe)
- Heartbeat generation
- Cleanup on client disconnect
- Active queue management

Currently, only the Event Bus core has unit tests. The SSE Transport layer is tested indirectly through E2E tests, leaving edge cases uncovered.

### Behavior Specification (BDD)

```gherkin
Feature: SSE Transport Unit Tests
  As a developer maintaining the event system
  I want comprehensive unit tests for SSE transport
  So that I can refactor confidently and catch regressions

  Scenario Outline: SSE Generator Behavior
    Given an SSE transport instance
    And a subscribed topic "<topic>"
    When <action>
    Then <expected_result>

    Examples:
      | topic          | action                          | expected_result              |
      | campaign:123   | event published to bus          | event appears in stream      |
      | campaign:123   | no events for 30 seconds        | heartbeat sent               |
      | campaign:123   | client disconnects (Cancelled)  | queue unsubscribed, cleaned  |
      | job:456        | queue is full                   | event dropped, warning logged|
      | campaign:123   | close() called                  | all queues signaled to close |

  Scenario: Active queues tracked correctly
    Given an SSE transport instance
    When subscribing to campaigns "123" and "456"
    Then 2 queues should be tracked
    When closing the transport
    Then 0 queues should remain
```

### Current Test Coverage

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|------------|-------------------|-----------|
| Event Bus Core | ✅ 10 tests | ✅ | - |
| Event Types | ✅ 7 tests | - | - |
| SSE Transport | ❌ None | ❌ | ⚠️ Connection only |
| Worker Publisher | - | ✅ | - |

### Missing Test Cases

**1. Heartbeat Generation**
```python
async def test_heartbeat_sent_on_timeout():
    """When no events arrive for 30s, heartbeat should be sent."""
    transport = SSETransport()
    response = await transport.subscribe_to_campaign("123")
    generator = response.body_iterator

    # Wait for timeout
    first = await asyncio.wait_for(generator.__anext__(), timeout=35.0)
    assert first == ": heartbeat\n\n"
```

**2. Cleanup on Cancellation**
```python
async def test_cleanup_on_cancellation():
    """When client disconnects, queue should be unsubscribed."""
    transport = SSETransport()
    response = await transport.subscribe_to_campaign("123")
    generator = response.body_iterator

    # Simulate client disconnect
    await generator.aclose()

    assert len(transport._active_queues) == 0
    assert "campaign:123" not in event_bus._subscribers
```

**3. Queue Full Handling**
```python
async def test_event_dropped_when_queue_full():
    """When queue is full, events should be dropped gracefully."""
    with patch.object(event_bus, 'MAX_QUEUE_SIZE', 1):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("123")

        # Fill queue
        await event_bus.publish(JobStatusEvent(...))
        await event_bus.publish(JobStatusEvent(...))  # Should be dropped
```

**4. Close Cleans All Queues**
```python
async def test_close_cleans_all_queues():
    """Calling close() should signal all active connections to terminate."""
    transport = SSETransport()
    await transport.subscribe_to_campaign("123")
    await transport.subscribe_to_campaign("456")

    await transport.close()

    assert len(transport._active_queues) == 0
```

### Recommended Implementation

Create `backend/tests/unit/events/transports/test_sse.py`:

```python
import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from app.events.transports.sse import SSETransport
from app.events.event_bus import event_bus
from app.events.event_types import JobStatusEvent


class TestSSETransport:
    @pytest.fixture
    def transport(self):
        return SSETransport()

    @pytest.mark.asyncio
    async def test_subscribe_to_campaign_returns_streaming_response(self, transport):
        response = await transport.subscribe_to_campaign("123")
        assert response.media_type == "text/event-stream"
        assert "Cache-Control" in response.headers

    @pytest.mark.asyncio
    async def test_heartbeat_sent_on_timeout(self, transport):
        response = await transport.subscribe_to_campaign("123")
        generator = response.body_iterator

        first = await asyncio.wait_for(generator.__anext__(), timeout=35.0)
        assert first == ": heartbeat\n\n"

        await generator.aclose()

    @pytest.mark.asyncio
    async def test_event_appears_in_stream(self, transport):
        response = await transport.subscribe_to_campaign("123")
        generator = response.body_iterator

        # Publish event after small delay
        async def publish_later():
            await asyncio.sleep(0.1)
            await event_bus.publish(JobStatusEvent(
                campaign_id="123",
                job_id=1,
                status="MATCHING"
            ))

        asyncio.create_task(publish_later())

        result = await generator.__anext__()
        assert "data:" in result
        assert "job:status_changed" in result

        await generator.aclose()

    @pytest.mark.asyncio
    async def test_cleanup_on_cancellation(self, transport):
        response = await transport.subscribe_to_campaign("123")
        generator = response.body_iterator

        assert len(transport._active_queues) == 1

        await generator.aclose()

        assert len(transport._active_queues) == 0

    @pytest.mark.asyncio
    async def test_close_terminates_all_connections(self, transport):
        await transport.subscribe_to_campaign("123")
        await transport.subscribe_to_campaign("456")

        assert len(transport._active_queues) == 2

        await transport.close()

        assert len(transport._active_queues) == 0
```

### Files Affected

| File | Change |
|------|--------|
| `backend/tests/unit/events/transports/__init__.py` | NEW: Package init |
| `backend/tests/unit/events/transports/test_sse.py` | NEW: SSE transport unit tests |

### Acceptance Criteria

- [ ] Given SSE transport tests, when running `pytest tests/unit/events/`, then all tests pass
- [ ] Test coverage for `sse.py` is > 90%
- [ ] Edge cases (timeout, cancellation, queue full) are covered
- [ ] Tests run in < 5 seconds (no real 30s waits in tests)

---

## Issue #39: SSE close() Doesn't Cancel Active Generators

**Discovered:** 2026-03-26 (Code Review Pass 5)
**Severity:** Medium (Resource Leak on Shutdown)
**Status:** Open

### Description

The `SSETransport.close()` method unsubscribes from the event bus but doesn't signal the running generators in `_create_stream_generator()` to terminate. The generators only exit when they try to get from an empty queue, which may not happen immediately.

### Current Implementation

```python
# sse.py:58-62
async def close(self):
    """Clean up all active connections."""
    for queue, topic in self._active_subscriptions.items():
        event_bus.unsubscribe(topic, queue)
    self._active_subscriptions.clear()
```

The generators continue running until:
1. They timeout waiting for a message (30s)
2. They try to get from the now-empty queue after unsubscribe

### Impact

- **Low** - Only affects graceful shutdown, not runtime behavior
- Generators will eventually exit on their own
- Brief resource leak during shutdown window

### Recommended Fix

**Option A: Sentinel Value**

```python
async def close(self):
    """Clean up all active connections."""
    for queue, topic in list(self._active_subscriptions.items()):
        event_bus.unsubscribe(topic, queue)
        await queue.put(None)  # Sentinel to unblock generator
    self._active_subscriptions.clear()
```

Update `_create_stream_generator()`:
```python
async def _create_stream_generator(self, topic: str, queue: asyncio.Queue):
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                if message is None:  # Shutdown sentinel
                    break
                yield f"data: {message}\n\n"
            except TimeoutError:
                yield ": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        event_bus.unsubscribe(topic, queue)
        self._active_subscriptions.pop(queue, None)
```

**Option B: Track and Cancel Tasks** (more complex)

Track the async generator tasks and explicitly cancel them in `close()`.

### Files Affected

| File | Change |
|------|--------|
| `backend/app/events/transports/sse.py` | Add sentinel handling in `close()` and generator |

### Effort

~10 minutes

### Acceptance Criteria

- [ ] Given active SSE connections, when `close()` is called, then generators exit immediately
- [ ] No 30-second timeout wait during shutdown
- [ ] All queues properly cleaned up

---

## Issue #40: E2E Event Flow Not Verified

**Discovered:** 2026-03-26 (Code Review Pass 7)
**Severity:** Medium (Test Coverage)
**Status:** Open

### Description

The E2E tests in `event-stream.spec.ts` verify SSE connection establishment but don't verify that actual job events are received and processed correctly. Tests check `typeof eventSourceConnected === 'boolean'` but never validate event content or UI updates.

### Current Test Coverage

```typescript
// event-stream.spec.ts:51-76 - Only checks connection status, not event flow
test('job status updates via SSE trigger UI refresh', async ({ page, seededCampaign }) => {
    const eventSourceConnected = await page.evaluate(() => {
        return new Promise<boolean>((resolve) => {
            const checkInterval = setInterval(() => {
                const statusEl = document.querySelector('[data-event-status]');
                if (statusEl?.textContent === 'connected') {
                    clearInterval(checkInterval);
                    resolve(true);
                }
            }, 100);
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve(false);
            }, 3000);
        });
    });
    expect(typeof eventSourceConnected).toBe('boolean');  // Weak assertion
});
```

### Recommended Fix

Add test that triggers a real job event and verifies UI update:

```typescript
test('job status event updates job list', async ({ page, seededCampaign }) => {
    await page.goto(`/workspace/${seededCampaign.id}/jobs`);

    // 1. Create a job via API
    const jobResponse = await page.request.post(`/api/jobs`, {
        data: { campaign_id: seededCampaign.id }
    });
    const job = await jobResponse.json();

    // 2. Listen for custom event dispatched by event store
    let receivedEvent: any = null;
    await page.exposeFunction('handleJobStatusEvent', (event: any) => {
        receivedEvent = event;
    });

    await page.evaluate(() => {
        document.addEventListener('votecatcher:job:status', (e) => {
            (window as any).handleJobStatusEvent((e as CustomEvent).detail);
        });
    });

    // 3. Start the job (triggers event)
    await page.request.post(`/api/jobs/${job.id}/start`);

    // 4. Wait for event to arrive
    await page.waitForFunction(() => (window as any).receivedEvent !== null, { timeout: 5000 });

    expect(receivedEvent.event_type).toBe('job:status_changed');
    expect(receivedEvent.status).toBeDefined();
});
```

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/tests/e2e/event-stream.spec.ts` | Add event flow verification test |

### Effort

~30 minutes

---

## Issue #41: Sidebar Redundant Campaign Fetches

**Discovered:** 2026-03-26 (Code Review Pass 7)
**Severity:** Medium (Performance)
**Status:** ✅ Fixed (2026-03-26)

### Resolution

Added `loaded` flag to `CampaignsState` interface and updated Sidebar to check `loaded` instead of array length:

1. **campaigns.ts** - Added `loaded: boolean` to state, set to `true` after successful fetch
2. **Sidebar.svelte** - Updated to check `!$campaigns.loaded && !$campaigns.loading`

### Files Changed

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/stores/campaigns.ts` | Added `loaded` flag to state, set on successful fetch |
| `frontend-svelt/src/lib/components/layout/Sidebar.svelte` | Check `loaded` instead of array length |
| `frontend-svelt/src/lib/stores/campaigns.test.ts` | Added tests for `loaded` flag behavior |

### Description (Original)

The `Sidebar.svelte` component fetches campaigns on every mount by checking `$campaigns.campaigns.length === 0`. If campaigns were loaded but the array is empty (legitimate empty state), it will re-fetch unnecessarily.

### Current Implementation

```svelte
<!-- Sidebar.svelte:37-41 -->
onMount(() => {
    if ($campaigns.campaigns.length === 0) {
        campaigns.fetchAll();
    }
});
```

### Problems

1. **Can't distinguish** between "not loaded" and "loaded but empty"
2. **Multiple fetches** if Sidebar is mounted/unmounted frequently
3. **Race conditions** if multiple components trigger fetch

### Recommended Fix

Add `loaded` flag to campaigns store:

```typescript
// campaigns.ts
interface CampaignsState {
    campaigns: Campaign[];
    loaded: boolean;  // NEW: Track if initial load completed
    loading: boolean;
    error: string | null;
}

function createCampaignsStore() {
    // ...
    async function fetchAll() {
        update(s => ({ ...s, loading: true, error: null }));
        try {
            const response = await fetch(`${apiUrl}/campaigns`);
            const data = await response.json();
            set({ campaigns: data, loaded: true, loading: false, error: null });
        } catch (e) {
            update(s => ({ ...s, loading: false, error: String(e) }));
        }
    }
    // ...
}

// Sidebar.svelte
onMount(() => {
    if (!$campaigns.loaded && !$campaigns.loading) {
        campaigns.fetchAll();
    }
});
```

### Files Affected

| File | Change |
|------|--------|
| `frontend-svelt/src/lib/stores/campaigns.ts` | Add `loaded` flag to state |
| `frontend-svelt/src/lib/components/layout/Sidebar.svelte` | Check `loaded` instead of array length |

### Effort

~15 minutes

---

## Issue #42: Test Assertion Unreachable

**Discovered:** 2026-03-26 (Code Review Pass 7)
**Severity:** Low (Test Quality)
**Status:** Open

### Description

In `test_sse_transport.py:179-181`, the assertion checking for `None` or empty string is unreachable because the generator breaks on `None` sentinel without yielding anything, causing `StopAsyncIteration` to be raised instead.

### Current Code

```python
# test_sse_transport.py:179-181
try:
    result = await asyncio.wait_for(read_task, timeout=1.0)
    assert result is None or result == "", (  # ← Never executed
        f"Expected None or empty, got {result!r}"
    )
except (StopAsyncIteration, asyncio.CancelledError):
    pass
```

### Analysis

The generator's sentinel handling:
```python
message = await asyncio.wait_for(queue.get(), timeout=30.0)
if message is None:
    break  # Exits without yielding
```

When `None` is received, the generator breaks cleanly, causing `StopAsyncIteration`. The `except` block catches this, so the assertion inside `try` is never reached.

### Recommended Fix

**Option A: Remove unreachable assertion**
```python
try:
    await asyncio.wait_for(read_task, timeout=1.0)
    # Generator exits via StopAsyncIteration, not by yielding
except (StopAsyncIteration, asyncio.CancelledError):
    pass  # Expected - generator terminated cleanly
```

**Option B: Document expected behavior**
```python
try:
    result = await asyncio.wait_for(read_task, timeout=1.0)
    # NOTE: This path is unreachable - generator breaks on None without yielding
    # StopAsyncIteration is the expected exit path
except (StopAsyncIteration, asyncio.CancelledError):
    pass  # Expected - generator terminated via sentinel
```

### Files Affected

| File | Change |
|------|--------|
| `backend/tests/unit/events/transports/test_sse_transport.py` | Remove or document unreachable assertion |

### Effort

~5 minutes

---

## Issue #43: Campaign/Job ID Type Inconsistency

**Discovered:** 2026-03-26 (Code Review Pass 7)
**Severity:** Low (Type Consistency)
**Status:** Open

### Description

In `event_types.py`, `campaign_id` is typed as `str | None` while `job_id` is `int | None`. This inconsistency could cause confusion when comparing or serializing IDs.

### Current Code

```python
# event_types.py:21-22
class BaseEvent(BaseModel):
    campaign_id: str | None = None  # UUID as string
    job_id: int | None = None       # Database integer
```

### Analysis

This reflects the underlying database schema:
- `campaigns.id` → UUID (stored as string in Python)
- `matcher_job.id` → INTEGER (auto-increment)

The types are **correct by design** but inconsistent for API consumers.

### Options

**Option A: Accept Current Design** (Recommended)

Document that IDs match their database types. This is the most accurate representation.

**Option B: Standardize to String**

Convert job_id to string in events:
```python
job_id: str | None = None  # Convert int to str for consistency
```

Trade-off: Requires conversion at publish time, adds overhead.

**Option C: Use Union Type**

```python
from uuid import UUID

campaign_id: UUID | str | None = None
job_id: int | str | None = None
```

Trade-off: More complex, harder to validate.

### Recommendation

**Option A** - Keep current design. The types correctly represent the underlying data model. Add a comment to clarify:

```python
class BaseEvent(BaseModel):
    # IDs match their database types:
    # - campaign_id: UUID (stored as string)
    # - job_id: INTEGER (auto-increment)
    campaign_id: str | None = None
    job_id: int | None = None
```

### Files Affected

| File | Change |
|------|--------|
| `backend/app/events/event_types.py` | Add clarifying comment |

### Effort

~5 minutes
