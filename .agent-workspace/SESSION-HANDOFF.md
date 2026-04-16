# Session Handoff — Entry-Level Highlight

> **You are a fresh agent picking up this work. Read this file first.**

## Branch

**`feat/crops-in-results`** — PR #59 open. Latest commit `4ca7468` (uncommitted changes for entry-level highlight).

## CI/CD Status

- `d76e123` — progressive reveal (scan_router, Svelte fixes, CVE bump). CI green.
- `4ca7468` — campaign endpoint fix. CI green.
- **Uncommitted** — entry-level highlight implementation (this session). Not yet pushed.

## Critical Lesson Learned

**The frontend calls `/api/campaigns/{id}/results`, NOT `/api/jobs/{id}/results`.**

The first commit (`d76e123`) added crop metadata only to the jobs endpoint. The campaign endpoint has its own response model (`CampaignResultResponse`) and service (`CampaignQueryService`). Fixed in `4ca7468`.

**Mitigation: trace before you code.** Before modifying any endpoint:
```bash
grep -r "results" frontend/src/lib/stores/campaign-results.ts  # find the URL
grep -rn "campaigns.*results" backend/app/routers/              # find the handler
```

## What Was Done This Session (Session C)

1. **Step 0: Visual validation** — generated annotated preview images with colored per-row bounding boxes overlaid on crop images. Saved to `.agent-workspace/preview-entry-division/`.
2. **Calibrated entry positions** — equal division didn't align. User measured actual positions: header=245px, stride=320px, box=370px (50px overlap) on 4723x2078 crop images.
3. **Created `entry_coordinates.py`** — pure function `compute_entry_coordinates(crop_coordinates, ocr_index)` returns `{"top": float, "bottom": float}` in page-fraction space.
4. **Updated both response models** — added `entry_coordinates: dict[str, float] | None = None` to `CampaignResultResponse` and `ResultResponse`.
5. **Wired both services** — `CampaignQueryService` and `ResultsQueryService` now compute entry coordinates per result.
6. **Updated frontend** — `entryCoordinates` in interface, `getHighlightCoords()` prefers entry over crop coords, highlight strip uses it.
7. **VDD adversarial review** — found 6 issues, addressed 2 (documentation, bounds guard). All findings documented.
8. **GitHub spike #61** — created for edge/line detection research to handle scan/form variance.
9. **All tests pass** — backend 1136 passed, frontend 383 passed, lint clean.

## Entry Coordinates Design

### Constants (calibrated for DC petition demo data)
```
crop image: 4723x2078px
header: 245px (top padding before first row)
stride: 320px (distance between row starts)
box: 370px (highlight height, includes 50px overlap with adjacent rows)
```

### Formula (page-fraction space)
```
header_frac = 245/2078 ≈ 0.1179
stride_frac = 320/2078 ≈ 0.1540
box_frac    = 370/2078 ≈ 0.1781

crop_height = crop_bottom - crop_top
entry_top   = crop_top + (header_frac + ocr_index * stride_frac) * crop_height
entry_bottom = entry_top + box_frac * crop_height
```

### Example output (crop_coordinates top=0.385, bottom=0.725)
```
idx=0: top=0.4251, bottom=0.4856  (Alexis Walter)
idx=1: top=0.4774, bottom=0.5380  (Jenny Jones)
idx=2: top=0.5298, bottom=0.5903  (Jack Stewart)
idx=3: top=0.5822, bottom=0.6427  (Brady Herrera)
idx=4: top=0.6345, bottom=0.6951  (Robert Ayala)
```

### Key Files
```
backend/app/services/entry_coordinates.py          (pure computation function)
backend/app/routers/campaign_router.py             (CampaignResultResponse.entry_coordinates)
backend/app/routers/results_router.py              (ResultResponse.entry_coordinates)
backend/app/services/campaign_query_service.py     (wired into result building)
backend/app/services/results_query_service.py      (wired into result building)
frontend/src/lib/stores/campaign-results.ts        (entryCoordinates in interface)
frontend/src/routes/(app)/workspace/[id]/results/+page.svelte (getHighlightCoords + highlight strip)
backend/tests/unit/schemas/test_dict_field_audit.py (allowlisted coordinate dict fields)
```

## Verification Status

| Check | Status |
|-------|--------|
| Backend ruff lint | Passed |
| Frontend svelte-check | 0 errors, 4 warnings |
| Frontend vitest | 383/383 passed |
| Backend pytest | 1136/1136 passed |
| Project lint (`just lint`) | Clean (pre-existing empty-file warnings only) |
| Dict field audit test | Passed (allowlisted 4 coordinate fields) |
| **CI green (after push)** | **NOT YET VERIFIED** |
| **Smoke test in browser** | **NOT YET DONE** |

## Next: Smoke Test

Start backend + frontend, verify in browser:
1. "Show on source page" button appears on expanded results
2. Highlight strip shows **per-entry** bounds (narrower strip, ~6% of page vs 34% for full block)
3. Strip aligns with actual entry position
4. Different entries within same crop show different highlight positions
5. Error state works for missing PDFs
6. CI green after push

## Then: Nice-to-have

- **Backend tests for scan_router** — 404/200/semaphore
- **Smart prediction truncation** — see Backlog
- **Scan page image caching** — on-the-fly PDF conversion is slow on first hit
- **Edge detection spike (#61)** — research line detection for automatic row boundary calibration

## Architecture Notes

### Two Parallel Results Endpoints (IMPORTANT)
```
/api/jobs/{job_id}/results       → results_router.py    → ResultResponse           → ResultsQueryService
/api/campaigns/{campaign_id}/results → campaign_router.py → CampaignResultResponse → CampaignQueryService
```
The frontend uses the **campaign** endpoint. Both must be updated in parallel for any response field changes.

### Data Model: Crop → OCR → Entry
```
PetitionScan (1) ← PetitionCrop (N) ← OcrResult (N)
  scan_id            crop_coordinates     ocr_index (0..4)
  original_filename  page_number          extracted_text
  stored_path        crop_index
```
One scan → multiple crops (one per page) → multiple OCR results (one per entry per page).

### Entry Coordinates Flow
```
Frontend clicks "Show on source page"
  → loads scan page image via /api/scans/{scan_id}/pages/{page_number}/image
  → overlays highlight strip using entryCoordinates (or cropCoordinates fallback)
  → entry_coordinates computed from: crop_coordinates + ocr_index + calibrated constants
```

## Preview Files (CLEAN UP WHEN DONE)

These are temporary prototyping/preview tools in `.agent-workspace/`. **Delete all of them once the entry highlight feature is smoke-tested in the actual app.**

| File | Purpose | Safe to delete after |
|------|---------|---------------------|
| `preview-progressive-reveal.html` | Original progressive reveal prototype | Smoke test passes |
| `preview-annotated-view.html` | Annotated crop view | Smoke test passes |
| `preview-split-view.html` | Split view prototype | Smoke test passes |
| `preview-entry-measurer.html` | Interactive tool for measuring entry positions | Smoke test passes |
| `preview-entry-division/` | Annotated crop images with colored row boxes | Smoke test passes |
| `generate_preview.py` | Script that generates preview-entry-division images | Smoke test passes |
| `query_crop_data.py` | Script to query crop/OCR data from DB | Smoke test passes |
| `compute_entry_coords.py` | Script to compute/verify page-fraction coordinates | Smoke test passes |

## Required Skills

| Skill | Location | When to Use |
|---|---|---|
| `vdd` | `.agents/skills/vdd/SKILL.md` | Adversarial review of new code |
| `vsdd` | `.agents/skills/vsdd/SKILL.md` | Full spec traceability if formal verification needed |
| `caveman-commit` | `.agents/skills/caveman-commit/SKILL.md` | For commit messages |

## Backlog

### Edge Detection for Entry Boundaries (#61)
Current approach uses hardcoded pixel constants calibrated for DC demo data. Real scans will vary. Research Hough line transform, horizontal projection profiling, tesseract bounding boxes, run-length encoding. Must be sub-200ms per crop.

### Smart Prediction Truncation
Currently shows top 5 unconditionally. If top is 97% and #2 is 12%, misleading. Research: relative threshold, absolute floor, statistical gap detection.

### Scan Page Image Caching
On-the-fly conversion ~200-500ms per page. Cache rendered pages to disk on first hit.

### Spec-based Cropping Connection
`file_service.py` uses hardcoded `DC_CROP_REGION`. `CropConfig` in field spec system has `top_crop`/`bottom_crop`. Not connected yet.

## Related Issues

- **#59** — PR: crops-in-results (this branch)
- **#60** — Spike: highlight individual petition entry on source page (IMPLEMENTED, not yet committed)
- **#61** — Spike: line/edge detection for entry boundary calibration

## Session History

1. Original crops-in-results work (PR #59) — complete, all VDD findings resolved
2. URL architecture fix (centralized `API_BASE_URL`) — follow-up from smoke testing
3. Progressive reveal feature — scan_router + frontend UI + CVE bump (`d76e123`)
4. Campaign endpoint fix — response model + service (`4ca7468`)
5. Entry-level highlight — visual calibration + backend + frontend (this session, uncommitted)
6. Next: commit + smoke test
