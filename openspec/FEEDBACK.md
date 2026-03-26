# User Feedback Items

Tracking user-reported issues and enhancement requests.

---

## 2026-03-19

### 1. Dashboard Setup Checkboxes Not Updating After Upload

**Severity:** High
**Status:** Fixed
**Reported:** 2026-03-19

**Description:**
After uploading voter list and signatures from the upload page, returning to the dashboard shows the setup progress stepper checkboxes still unchecked, even though uploads succeeded.

**Steps to Reproduce:**
1. Create new campaign
2. Navigate to dashboard
3. Click "Upload Files" → upload petitions
4. Click "Upload Files" → upload voter list
5. Return to dashboard
6. Expected: Both checkboxes should be checked
7. Actual: Checkboxes remain unchecked

**Backend Logs Confirm Success:**
```
Petition uploaded and cropped  campaign_id=e5bcfb69-... scan_id=1
Voter list uploaded and imported file_name=fake_voter_records.csv imported_count=100000
```

**Root Cause:**
Dashboard `fetchSetupStatus()` only called in `onMount()`. When user navigates away and returns, the component may be cached or the status isn't refreshed.

**Location:**
- `frontend-svelt/src/routes/workspace/[id]/+page.svelte:94-101`

**Fix Options:**
1. Add `afterNavigate` lifecycle to refresh setup status
2. Use Svelte's `navigating` store to detect page focus
3. Invalidate cache on upload completion (broadcast via store/event)
4. Poll setup-status like metrics (already polling every 30s)

**Recommended Fix:**
Add `afterNavigate` from `$app/navigation` to refresh setup status when returning to the dashboard.

**Fix Applied:**
Added `afterNavigate` hook in `+page.svelte` to call `fetchSetupStatus()` when navigating back to the dashboard from another page.

**Additional Issue Found:**
~~Voter list checkbox still not updating because `import_voter_list()` in `file_service.py` inserts voters into `registered_voters` table but **never creates a `VoterListUpload` record**.~~

**Status:** ✅ Verified (2026-03-25) - `VoterListUpload` record created at `file_service.py:301-308`. Integration test added at `tests/integration/api/test_setup_status.py`.

---

## 2026-03-25

### 2. Verify Voter List Checkbox Fix

**Severity:** Medium
**Status:** ✅ Verified (2026-03-25)
**Reported:** 2026-03-25 (Code Review)

**Description:**
The `VoterListUpload` record is now being created in `file_service.py:301-308`. Verified via integration test that dashboard checkbox updates correctly after voter list upload.

**Verification:**
Added integration test `test_setup_status_after_voter_list_upload` that:
1. Uploads voter list via `POST /api/upload/voter-list`
2. Checks `GET /api/campaigns/{id}/setup-status`
3. Asserts `voter_list.exists === true`

**Location:**
- `backend/app/files/file_service.py:301-308` (fix applied)
- `frontend-svelt/src/routes/workspace/[id]/+page.svelte` (setup status display)
- `backend/tests/integration/api/test_setup_status.py` (verification test)

---

### 3. E2E Test Coverage for Event Stream

**Severity:** Low
**Status:** Open
**Reported:** 2026-03-25 (Code Review)

**Description:**
Current E2E tests (`event-stream.spec.ts`) only verify SSE connection is established. Missing coverage for:
- Event delivery triggers UI updates (job status changes, progress bars)
- Reconnection after simulated disconnect
- Metrics event updates dashboard stats

**Location:**
- `frontend-svelt/tests/e2e/event-stream.spec.ts`

**Suggested Tests:**
```typescript
// Test job status update reflects in UI
test('job status event updates jobs list', async ({ page }) => {
  // Navigate to jobs page
  // Trigger job via API
  // Verify status changes without page refresh
});

// Test reconnection
test('event stream reconnects after network failure', async ({ page }) => {
  // Simulate offline
  // Verify reconnection attempts in store
  // Verify events received after reconnect
});
```

---

### 4. Clarify Dual SSE Architecture

**Severity:** Low
**Status:** ✅ Documented (2026-03-25)
**Reported:** 2026-03-25 (Code Review)

**Description:**
Two SSE mechanisms exist:
1. New event bus: `/events/campaigns/{id}/stream` (used by `events.ts`, connected in layout)
2. Old job SSE: `/api/jobs/{id}/status` (in `jobs.ts:210-250`, `connectToJob()`)

**Resolution:**
Both systems are intentional and serve different purposes (see ADR-0001):
- Event bus: Campaign-scoped updates for dashboard, jobs list, metrics
- Per-job SSE: Focused monitoring for job detail page

`connectToJob()` is actively used in `jobs/[job_id]/+page.svelte:14`.

**Documentation:**
- ADR: `openspec/adr/0001-dual-sse-architecture.md`
- Comment added to `jobs.ts` explaining usage

---

### 5. Type Safety in Job Status Handler

**Severity:** Low
**Status:** ✅ Fixed (2026-03-25)
**Reported:** 2026-03-25 (Code Review)

**Description:**
`jobs.ts:188` uses `status as any` type assertion instead of proper union type.

**Location:**
- `frontend-svelt/src/lib/stores/jobs.ts:188`

**Fix Applied:**
Imported `JobStatusEnum` type and updated `handleStatusEvent` to use proper typing:

```typescript
import type { JobStatusEnum } from '$lib/api/generated/models/Job';

handleStatusEvent(event: { job_id: number; status: JobStatusEnum }) {
  // ... now properly typed, no 'as any'
}
```

---

## Template for New Items

```markdown
### N. [Title]

**Severity:** High | Medium | Low
**Status:** Open | In Progress | Fixed | Won't Fix
**Reported:** YYYY-MM-DD

**Description:**
[What the user reported]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Expected vs Actual

**Root Cause:**
[Analysis if known]

**Location:**
[File paths and line numbers]

**Fix:**
[Solution or PR reference]
```
