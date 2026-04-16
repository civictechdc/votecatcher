# Session Handoff — Frontend URL Architecture Fix: IN PROGRESS

> **You are a fresh agent picking up this work. Read this file first.**

## Branch

**`feat/crops-in-results`** — PR #59 open. All changes below are **uncommitted** on this branch.

## What Happened

Smoke testing revealed two categories of bugs with the same root cause: **no single source of truth for the backend API URL**. Each store/page independently resolved `PUBLIC_API_URL` with its own fallback — half used `localhost:8000` (stale), half used `localhost:8080` (correct).

### Bug 1: Wrong port (8000 vs 8080) — FIXED, uncommitted
Multiple stores/pages hardcoded `localhost:8000` as fallback. Backend runs on `8080`.

### Bug 2: Relative URLs from backend hit SvelteKit origin — NOT FIXED
Backend returns relative URLs like `/api/crops/1/image` in response data. Browser resolves these against the page origin (`localhost:5173`) instead of the backend (`localhost:8080`). Crop thumbnails 404.

## Changes Made (uncommitted, 22 files)

### New file
- `frontend/src/lib/api/base-url.ts` — single source of truth for `API_BASE_URL`

### Refactored to import from `base-url.ts`
All of these now import `API_BASE_URL` instead of doing their own `import.meta.env` resolution:

| File | Before |
|---|---|
| `frontend/src/lib/api/client.ts` | own `BASE_URL` with 8080 |
| `frontend/src/lib/api/auth.ts` | weird `BASE` with empty fallback |
| `frontend/src/lib/api/openapi-client.ts` | `VITE_API_BASE_URL` (different env var!) |
| `frontend/src/lib/stores/api-client.ts` | `PUBLIC_API_URL \|\| localhost:8000` |
| `frontend/src/lib/stores/featureFlags.ts` | empty string fallback → hit 5173 |
| `frontend/src/lib/stores/settings.ts` | `localhost:8000/api` |
| `frontend/src/lib/stores/campaign-results.ts` | `localhost:8000` |
| `frontend/src/lib/stores/uploads.ts` | `localhost:8000` (2 places) |
| `frontend/src/lib/stores/auth.svelte.ts` | hardcoded `localhost:8000` |
| `frontend/src/lib/stores/jobs.ts` | `PUBLIC_API_URL \|\| localhost:8080` |
| `frontend/src/lib/stores/events.ts` | `PUBLIC_API_URL \|\| localhost:8080` |
| `frontend/src/routes/.../match-status/[job_id]/+server.ts` | own `PUBLIC_API_URL` |
| `frontend/src/routes/.../[id]/+page.svelte` | own inline resolution |
| `frontend/src/routes/.../[id]/upload/+page.svelte` | own inline resolution |
| `frontend/src/routes/.../[id]/jobs/+page.svelte` | own inline resolution |
| `frontend/src/routes/.../[id]/jobs/new/+page.svelte` | own inline resolution |
| `frontend/src/routes/.../settings/+page.svelte` | own inline resolution |

### Tests updated
- `frontend/src/lib/stores/api-client.test.ts`
- `frontend/src/lib/stores/demo.test.ts`
- `frontend/src/lib/stores/sessions.test.ts`

### Env typing
- `frontend/src/app.d.ts` — added `ImportMetaEnv` interface for all env vars

### Settings store path fix
- `frontend/src/lib/stores/settings.ts` — changed `/config/settings` → `/api/config/settings`
- Backend endpoint confirmed: `GET http://localhost:8080/api/config/settings` returns 200

## What Still Needs Fixing

### 1. Relative URL problem (crop images 404) — HIGH

Backend returns `thumbnailUrl: "/api/crops/1/image"`. These are rendered as `<img src="/api/crops/1/image">` in `campaign-results.ts`. Browser resolves against page origin (5173).

**Fix needed in `frontend/src/lib/stores/campaign-results.ts`:**
- `renderThumbnailCell()` (line ~186)
- `renderExpandedCropImage()` (line ~142)
- Both inject relative URLs into `<img src="">`. Need to prepend `API_BASE_URL` when URL starts with `/`.

**Also check the results page directly:**
- `frontend/src/routes/(app)/workspace/[id]/results/+page.svelte` — line 143 uses `renderExpandedCropImage(result.thumbnailUrl)`, line 38 uses `renderThumbnailCell(result.thumbnailUrl)`

**Pattern to apply:**
```typescript
function toAbsoluteUrl(url: string): string {
  if (!url || url.startsWith('http')) return url;
  return `${API_BASE_URL}${url}`;
}
```

Use this in both render functions before passing to `escapeHtml()`.

**Also audit ALL places where backend response data contains URLs** — any relative URL from the backend used as `src`, `href`, or `fetch()` target has this bug. Check:
- Upload URLs in `uploads.ts`
- SSE URLs in `events.ts` and `jobs.ts`
- Any other API response fields that contain paths

### 2. Broader relative URL audit

Search the entire codebase for patterns where backend response data is used as `src=` or `href=` without the backend origin. The backend should ideally return absolute URLs, but the frontend needs to be defensive.

Check if the backend has any other response fields with relative paths:
```bash
curl -s 'http://localhost:8080/api/campaigns/<id>/results?page=1&page_size=1' | python3 -m json.tool
```

### 3. Run tests

Tests were not verified due to vitest timeout issues. Run before committing:
```bash
cd frontend && npx vitest run
```

### 4. Verify settings page loads

`http://localhost:5173/workspace/settings` — the `settings.ts` store now fetches from `${API_BASE_URL}/api/config/settings`. Confirm this works in browser.

### 5. Commit

Once all fixes verified:
```
git add -A
git commit  # use caveman-commit
```

Single commit covering the URL architecture fix is appropriate — it's one coherent change.

## Decisions Made

- **One canonical `API_BASE_URL`** in `$lib/api/base-url.ts` — no more scattered env resolution
- **Default port is 8080** — matching actual backend
- **`app.d.ts` typed env vars** — helps CI and IDE autocomplete
- **`openapi-client.ts` uses `/api` suffix** via `${API_BASE_URL}/api` — backend OpenAPI endpoints are under `/api`
- **`settings.ts` uses `/api/config/settings`** — backend route is `/api/config/settings`, not `/config/settings`
- **`auth.ts` empty string fallback removed** — was causing auth requests to hit SvelteKit origin

## Files to Not Touch

- `frontend/.env`, `.env.test`, `.env.example` — already correct (`PUBLIC_API_URL=http://localhost:8080`)
- Test files that mock `api-client` — already updated to use `API_BASE_URL`
- Backend code — no changes needed, backend returns correct data

## Key Architecture Insight

The frontend has **two classes of API consumers**:

1. **Code that constructs URLs** (stores, pages) — these now all use `API_BASE_URL`. Fixed.
2. **Code that receives URLs from backend responses** (`thumbnailUrl` in results) — these are relative. NOT fixed.

Class 2 is the remaining work. Options:
- **Option A (recommended):** Backend returns absolute URLs — backend knows its own origin
- **Option B:** Frontend normalizes all backend-returned URLs through `toAbsoluteUrl()` helper
- **Option C:** Both — backend returns absolute, frontend normalizes defensively

## Required Skills

| Skill | Location | When to Use |
|---|---|---|
| `vdd` | `.agents/skills/vdd/SKILL.md` | After fixing — adversarial review of the URL architecture |
| `caveman-commit` | `.agents/skills/caveman-commit/SKILL.md` | For the commit message |
| `verification-before-completion` | Project skills | Before marking done — run tests, verify in browser |

## Backlog / Follow-up Ideas

### Crop Coordinates in Results Table

Show users where each crop came from in the source documents:

- **Entry number** — position within the document (1-based for display, 0-based internally)
- **Document index** — which document in the upload (1-based display, 0-based internal)
- **Document name** — original filename from upload (e.g., `petition_pack_page_3.pdf`)

These fields likely map to existing `PetitionCrop` and `PetitionScan` columns:
- `crop_index` (0-based) → display as `Entry {crop_index + 1}`
- `scan_id` → join to `PetitionScan` for document info
- `PetitionScan.original_filename` → document name
- Need a document sequence number (scan order within campaign) → display as `Document {order + 1}`

**Pixel coordinates:** `crop_coordinates` stores `{"top": float, "bottom": float}` — relative
vertical bounds (fraction of page height), not pixel coords. These define the horizontal
strip where the signature appears on the page.

### Crop Coordinate Strip Highlight — Progressive Reveal

**Chosen approach:** Progressive reveal — crop + predictions shown first in accordion row,
"Show on source page" button expands the source page below with highlighted strip. No
second lightbox needed. Preview at `.agent-workspace/preview-progressive-reveal.html`.

**Spec-based cropping compatibility:**

Current state: `file_service.py` uses hardcoded `DC_CROP_REGION = {"top": 0.385, "bottom": 0.725}`
for both `crop_petition()` (line 91) and the upload flow (line 384). Meanwhile, `CropConfig`
in the field spec system has `top_crop` / `bottom_crop` (same relative 0-1 format) and is
used by `ocr_config.py::get_current_crop_config()`. The two are currently **not connected** —
the file service doesn't read from the spec.

What `crop_coordinates` actually stores: `{"top": 0.385, "bottom": 0.725}` — always top/bottom
relative vertical bounds, full page width. No left/right, no pixel coords.

**Impact on progressive reveal:**
- Highlight strip is straightforward — draw a div from `top%` to `bottom%` of the source page
- Works with any region's crop config since it's always top/bottom relative coords
- When spec-based cropping is connected to file_service, the coordinates will vary per region
  but the format stays the same — progressive reveal is agnostic

**Backend changes needed:**
- `CampaignResultResponse` needs new fields: `crop_coordinates`, `page_number`,
  `document_name` (from PetitionScan), `crop_index`
- Join OcrResult → PetitionCrop → PetitionScan to get these
- Add endpoint to serve original page image (or derive from existing stored_path)

**Frontend changes needed:**
- Add "Show on source page" button in expanded accordion row
- Load source page image, overlay highlight strip using `crop_coordinates`
- Smooth expand/collapse animation

Open questions:
- Does the backend already return scan/document info in the results API, or does it need to be added?
- Should this be columns in the table, or shown in the expanded accordion row?
- How to handle multi-page PDFs — is a "document" a file or a page?

### Smart Prediction Truncation (confidence-aware display)

Currently `renderPredictionsTable` shows top 5 predictions unconditionally. Should instead show only predictions that are meaningfully close to the top match.

**Problem:** If top pick is 97% and #2 is 12%, showing both implies they're comparable matches. Misleading UX.

**Open questions:**
- What's a well-established approach? (e.g., relative threshold like "within 20pp of top", absolute floor like "≥30% confidence", or statistical gap detection like "show all until a gap > X")
- How many to cap at? 3-5?
- Should the threshold vary by confidence tier (HIGH/MEDIUM/LOW)?
- Does Elasticsearch/fuzzy matching literature have a standard for this? (e.g., cutoff at score dropoff, max ratio between #1 and #N)

**References to explore:** Lucene score normalization, MinHash/Jaccard threshold practices, deduplication literature, voter matching best practices.

## Previous Session Context

The original crops-in-results work (PR #59) is complete and all VDD findings resolved. This URL architecture fix is a follow-up from smoke testing that PR. See the git log on the branch for the full commit history of the original work.
