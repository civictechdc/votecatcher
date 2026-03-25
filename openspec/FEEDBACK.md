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
Voter list checkbox still not updating because `import_voter_list()` in `file_service.py` inserts voters into `registered_voters` table but **never creates a `VoterListUpload` record**. The `get_active_upload()` method checks `VoterListUpload` table which is always empty.

**Fix Required:**
Create `VoterListUpload` record after importing voters in `file_service.import_voter_list()`.

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
