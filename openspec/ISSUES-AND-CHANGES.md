# Issues and Changes Log

Tracking issues discovered during implementation walkthroughs and proposed changes.

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
**Status:** Open

### Description
The SSE "connected" indicator shown in job status UI is development/debug information that shouldn't be visible in production.

### Proposed Fix
- Make "connected" indicator debug-only (hidden by default)
- Could use a feature flag or check for dev mode
- Alternative: Remove entirely if not useful to end users

### Files Affected
- Frontend job status component (SSE connection indicator)

---

## Issue #3: Status Filter Looks Like a Button

**Discovered:** 2026-03-17
**Severity:** Low
**Status:** Open

### Description
On `/workspace/[id]/jobs`, the status filter dropdown:
1. Styled like a button, unclear it's a dropdown
2. Width too small for text content (text gets cramped/truncated)

### Proposed Fix
- Add dropdown arrow indicator (chevron)
- Increase min-width to accommodate status text comfortably
- Apply consistent dropdown styling (border, background)
- Consider using native `<select>` or a clearer custom dropdown component

### Files Affected
- Frontend jobs list page (status filter component)

---

## Issue #5: Voter List Tab Missing "Existing Uploads" Display

**Discovered:** 2026-03-17
**Severity:** Medium
**Status:** Open

### Description
On `/workspace/[id]/upload`, the **Petitions** tab shows existing petition files with metadata (filename, size, pages, upload date). The **Voter List** tab has no equivalent - user can't see if a voter list was already uploaded for this campaign/region.

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
**Status:** Open

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

---

## Issue #7: Campaign Context Lost When Navigating to Settings

**Discovered:** 2026-03-17
**Severity:** Low (UX Polish)
**Status:** Open

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

---

## Issue #8: Model Selector Dropdown Clipped by Container

**Discovered:** 2026-03-17
**Severity:** Medium (Broken UX)
**Status:** Open

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

### Proposed Fixes

**Option A: Remove `overflow-hidden` from card**

```html
<!-- ProviderConfigCard.svelte:94 -->
<div class="rounded-lg border border-slate-200 bg-white">
```

Simple fix, but may affect rounded corners rendering on nested content.

**Option B: Increase dropdown z-index**

```html
<!-- Select.svelte:233 -->
<div class="absolute z-50 w-full mt-1 bg-white ...">
```

Higher z-index, but won't help if parent has `overflow-hidden`.

**Option C: Portal dropdown to body**

Render the dropdown in a portal attached to `<body>`, escaping container constraints entirely:

```svelte
{#if open}
  {#snippet dropdown()}
    <div class="fixed ..." style="position: absolute; top: {top}px; left: {left}px;">
      <!-- dropdown content -->
    </div>
  {/snippet}
  <Portal target="body">{dropdown()}</Portal>
{/if}
```

Most robust solution, commonly used in design systems.

### Recommendation

**Combine Option A + B** for quick fix:
1. Remove `overflow-hidden` from `ProviderConfigCard.svelte:94`
2. Increase z-index to `z-50` in `Select.svelte:233`

Consider Option C (portal) for a more robust long-term solution.

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
**Status:** Open

### Description
On `/workspace/[id]` (campaign dashboard), when a user has uploaded petition files but hasn't run any jobs, the dashboard shows "N/A" for all metrics without explaining *why* or what to do next. Users lose context about their campaign state.

### Current Behavior
- Dashboard only distinguishes: `hasResults` (metrics > 0) vs "N/A"
- No indication of intermediate states:
  1. No uploads at all
  2. Uploads exist, no job run ← **missing**
  3. Job run but no matches

### User Journey Affected
1. User uploads 3 petition files
2. Navigates to dashboard
3. Sees "N/A" everywhere with no guidance
4. Confusion: "Did my upload work? What do I do next?"

### Recommended UX

**1. Add call-to-action banner when uploads exist but no jobs:**

```
┌─────────────────────────────────────────────────────────┐
│ 📁 3 petition files ready to process                    │
│     Start a job to match signatures.  [Create Job]      │
└─────────────────────────────────────────────────────────┘
```

**2. State-aware metric card subtitles:**

| State | Total Signatures | Processed | Subtitle |
|-------|------------------|-----------|----------|
| No uploads | N/A | N/A | "Upload files to begin" |
| Uploads, no job | — | — | "Run a job to see results" |
| Has results | 123 | 100 | "X% complete" |

**3. Optional: Progress stepper in dashboard header:**

```
[✓ Upload] → [○ Process] → [○ Results]
              ↑ current
```

### Implementation

**Backend:** No changes needed (existing endpoints cover it)

**Frontend state detection:**

```typescript
// Add new state variables
let hasScans = $state<boolean | null>(null);

// Derive campaign state
const campaignState = $derived(() => {
  if (hasScans === null) return 'loading';
  if (!hasScans) return 'no_uploads';
  if (campaignJobs.length === 0) return 'ready_to_process';
  if (!hasResults) return 'processing';
  return 'has_results';
});
```

**Fetch scan status:**

```typescript
async function checkScans() {
  const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/scans`);
  if (response.ok) {
    const data = await response.json();
    hasScans = data.total > 0;
    scanCount = data.total;  // for banner
  }
}
```

**UI changes:**

```svelte
<!-- Banner after metric cards -->
{#if campaignState() === 'ready_to_process'}
  <div class="rounded-md bg-blue-50 p-4 mb-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <svg>...</svg>
        <div>
          <p class="font-medium text-blue-800">{scanCount} petition files ready</p>
          <p class="text-sm text-blue-700">Start a job to match signatures against the voter list.</p>
        </div>
      </div>
      <Button variant="primary" text="Create Job" onclick={() => window.location.href = `/workspace/${campaignId}/jobs`} />
    </div>
  </div>
{/if}
```

### Files Affected

| File | Change |
|------|--------|
| `src/routes/workspace/[id]/+page.svelte` | Add state detection, banner, metric subtitles |

### Related Issues
- Issue #9: Create Job button should also be disabled when no uploads

---

## Issue #11: Redundant High Confidence Metric Card

**Discovered:** 2026-03-17
**Severity:** Low (UX Polish)
**Status:** Open

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
**Status:** Open

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
