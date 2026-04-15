# VSDD Implementation Plan: Crops in Results + Sort Fix + Performance

**Issues:** #38, #39, #40, #53
**Stack:** FastAPI + SQLModel/SQLAlchemy + SQLite/Supabase Postgres + SvelteKit
**Pipeline:** VSDD (Spec → TDD → Adversarial → Formal) + VDD (Builder/Adversary loop)
**Tracker:** Crosslink (epic → bead decomposition, contract chain traceability)
**Labels:** `epic`, `bead`, `spec`, `test`, `adversarial-review`, `formal-proof`, `purity-boundary`, `refactor`, `hygiene`

---

## Phase 1 — Spec Crystallization

### 1a. Behavioral Contracts

#### EPIC-1: Sort Fix (#53)
**Given** a results page with 50 rows
**When** user clicks a sortable column header
**Then** rows reorder client-side by that column ascending; click again → descending
**Invariant:** Only one column sorted at a time. Only current page sorted (Phase 1).
**NFR:** Sort 50 rows < 5ms. No re-fetch from backend.

#### EPIC-2: Crop Image Serving (#39)
**Given** a `PetitionCrop` with `stored_path` pointing to an existing PNG
**When** client requests `GET /api/crops/{crop_id}/image`
**Then** response is 200 with `image/png`, `Cache-Control: public, max-age=86400, immutable`
**Given** a `crop_id` with no crop or missing file
**When** same endpoint hit
**Then** 404
**Invariant:** Each crop image is immutable. Cache lifetime = unlimited.
**NFR:** Response time < 50ms. Concurrent request limit = 50 (semaphore).

#### EPIC-3: SQL Pagination (#39 performance)
**Given** a job with N match_results (N = 250k for 50k petitions)
**When** client requests page P with page_size S
**Then** backend loads exactly S × (matches-per-ocr) rows from DB, not N rows
**And** `total` comes from SQL `COUNT(DISTINCT)`, not Python `len()`
**Invariant:** Memory per request ≤ O(S × 5). Never O(N).
**NFR:** Page request < 100ms with 10k results on SQLite.

#### EPIC-4: Thumbnail in Results (#38, #40)
**Given** campaign results page with N rows (N ≤ 50)
**When** rendered
**Then** each row shows 60×40px lazy-loaded crop thumbnail from `thumbnail_url`
**And** clicking row expands accordion showing enlarged crop + top-5 predictions
**And** clicking thumbnail opens lightbox modal with full-size image
**And** only 1 row expanded at a time
**Invariant:** Only visible thumbnails decode. Expanded row destroyed on collapse.
**NFR:** Page load with 50 thumbnails < 2s on broadband. Tab switching doesn't leak DOM.

#### EPIC-5: Memory Hygiene
**Given** a long-running server processing jobs over days
**When** tasks complete, connections idle, SSE clients disconnect
**Then** no unbounded dict growth, no stale connections, no leaked file handles
**Invariant:** `DemoMatchingTaskMonitor._events|_tasks` empty after terminal task. SSE max lifetime 1hr. DB pool recycles every 5min.

#### EPIC-6: Architecture Hygiene
**Given** existing code we touch
**When** we modify it
**Then** duplicated logic is consolidated, HTTP concerns extracted from services, test gaps filled
**Invariant:** No code touched without a test. No method > 30 lines. No service returns HTTP response objects.

### 1b. Verification Architecture

#### Purity Boundary Map

| Layer | Pure (verifiable) | Effectful (I/O shell) |
|---|---|---|
| **PredictionBuilder** | `build()`, `format_voter_name()`, `format_voter_address()` | DB query for voter lookup |
| **OcrTextParser** | `format_ocr_text()` | None — pure function |
| **SortConfig** | Validation, direction toggle | None |
| **CropStorageAdapter** | URL construction (`get_image_url()`) | File I/O (`get_image_path()`, existence check) |
| **PaginationQuery** | Offset/limit calculation | SQL execution |
| **MetricsAggregation** | Confidence counting from GROUP BY result | SQL GROUP BY execution |

#### Provable Properties (test-covered, not formally proved)

| Property | Layer | Verification |
|---|---|---|
| Page N and Page N+1 are disjoint | PaginationQuery | Property-based test (Hypothesis) |
| Total count invariant across pages | PaginationQuery | Assert |
| Sort is stable (equal keys preserve original order) | SortConfig | Property-based test |
| Prediction rank order matches DB | PredictionBuilder | Assert |
| Crop URL construction is injective (crop_id → unique URL) | CropStorageAdapter | Assert |
| `Cache-Control` header present on image responses | Crop endpoint | Assert |
| Task monitor dicts empty after terminal status | DemoMatchingTaskMonitor | Assert |
| Export CSV never loads > chunk_size rows at once | CSV export | Mock assertion |

#### Formal Verification Candidates
None at this tier — no financial/medical/infrastructure criticality. Property-based tests via Hypothesis are sufficient.

---

## Phase 2 — Crosslink Decomposition

### Initialize

```bash
crosslink init
crosslink session start
```

### Epic Creation (run these first, collect IDs)

```bash
# EPIC-1: Sort Fix
crosslink issue create "Sort results table column headers (#53)" -p high -l epic

# EPIC-2: Crop image serving endpoint
crosslink issue create "Crop image serving endpoint (#39)" -p high -l epic

# EPIC-3: SQL pagination rewrite for 10k+ results
crosslink issue create "SQL pagination rewrite for 10k+ results" -p critical -l epic

# EPIC-4: Frontend thumbnails + accordion expand (#38, #40)
crosslink issue create "Frontend crop thumbnails + accordion expand (#38, #40)" -p high -l epic

# EPIC-5: Memory hygiene fixes
crosslink issue create "Memory hygiene for long-running server" -p high -l epic

# EPIC-6: Architecture hygiene refactors
crosslink issue create "Architecture hygiene: DRY, extraction, test gaps" -p medium -l epic
```

### Bead Decomposition (subissues under epics)

Replace `<EPIC_N_ID>` with actual IDs from above.

---

#### EPIC-5 Beads (do first — prerequisite)

```bash
crosslink issue create "Bead 5a: DemoMatchingTaskMonitor cleanup after terminal tasks" --parent <EPIC_5_ID> -p high -l bead -l test
# Spec: _events, _tasks, _providers dicts empty after terminal task
# Test: seed task → set terminal status → assert dicts empty
# Files: demo_local_job_monitor.py
# Purity: dict mutation in effectful shell

crosslink issue create "Bead 5b: Supabase engine pool_recycle and pool_pre_ping" --parent <EPIC_5_ID> -p high -l bead -l test
# Spec: engine created with pool_recycle=300, pool_pre_ping=True
# Test: assert engine.pool.status().checkedout is bounded after 300s recycle
# Files: supabase.py
# Purity: connection pool config — effectful

crosslink issue create "Bead 5c: SSE max lifetime timeout" --parent <EPIC_5_ID> -p medium -l bead -l test
# Spec: SSE generator terminates after 3600s
# Test: mock asyncio.timeout, assert generator exits
# Files: sse.py
# Purity: asyncio timeout — effectful
```

---

#### EPIC-6 Beads (refactor before feature work)

```bash
crosslink issue create "Bead 6a: Extract PredictionBuilder from duplicated service logic" --parent <EPIC_6_ID> -p high -l bead -l refactor -l test
# Spec: PredictionBuilder.build() produces same output as both services' private methods
# Test: parameterized test — same input → same output for CampaignQueryService and ResultsQueryService
# Files: new app/services/prediction_builder.py, modify both query services
# Purity boundary: build() is pure once voter dict provided; voter lookup is effectful
# Traceability: HYGIENE-1

crosslink issue create "Bead 6b: Extract OcrTextParser for extracted_text dict→string" --parent <EPIC_6_ID> -p high -l bead -l refactor -l test
# Spec: format_ocr_text(ocr_result) handles dict, str, None inputs consistently
# Test: parametrize [dict→"name addr", str→str, None→"", empty dict→""]
# Files: new app/services/ocr_text_parser.py (or method on OcrResult model)
# Purity boundary: pure function — no I/O
# Traceability: HYGIENE-2

crosslink issue create "Bead 6c: Extract shared test fixtures from service tests" --parent <EPIC_6_ID> -p medium -l bead -l refactor -l test
# Spec: All service tests use shared engine/session/seed fixtures from conftest
# Test: existing tests pass without modification after fixture extraction
# Files: tests/unit/services/conftest.py, modify test files
# Traceability: HYGIENE-3

crosslink issue create "Bead 6d: Stream CSV export with yield_per" --parent <EPIC_6_ID> -p medium -l bead -l refactor -l test
# Spec: export_results_csv streams rows in chunks of 1000, never loads all at once
# Test: assert .all() never called on stream; assert incremental yield (behavioral, not yield_per mock)
# Files: results_query_service.py
# Traceability: HYGIENE-4
# REVIEW NOTE: _generate_csv_rows has on-demand caching with conditional fetches.
#   Watch for deeply nested if/else in loops — prefer ternary/early-return/guard patterns.
#   See commit c6f3d21 for the flatten pass. Re-check after EPIC-3 pagination changes.

crosslink issue create "Bead 6e: Extract HTTP concern from export_results_csv" --parent <EPIC_6_ID> -p medium -l bead -l refactor -l test
# Spec: Service returns (csv_lines_iterable, filename). Router wraps in StreamingResponse.
# Test: assert service returns unpackable (iterable, str), not StreamingResponse
# Files: results_query_service.py, results_router.py
# Purity boundary: CSV generation is pure; HTTP response wrapping is effectful (router)
# Traceability: HYGIENE-6

crosslink issue create "Bead 6f: Remove dead _providers dict from DemoMatchingTaskMonitor" --parent <EPIC_6_ID> -p low -l bead -l refactor
# Spec: _providers dict removed, no test change needed
# Files: demo_local_job_monitor.py
# Traceability: HYGIENE-9

crosslink issue create "Bead 6g: Add missing edge case tests for get_setup_status" --parent <EPIC_6_ID> -p medium -l bead -l test
# Spec: Tests cover: multiple scans, null region_key, OCR_PENDING job, invalid confidence filter
# Test: parameterized test for each edge case
# Files: test_campaign_query_service.py
# Traceability: HYGIENE-7
```

---

#### EPIC-1 Beads (sort fix)

```bash
crosslink issue create "Bead 1a: SortConfig value object in campaign-results.ts" --parent <EPIC_1_ID> -p high -l bead -l test
# Spec: SortConfig(column, direction) validates column name and direction
# Test: valid creation, invalid column throws, invalid direction throws, toggle direction
# Files: campaign-results.ts
# Purity: pure value object

crosslink issue create "Bead 1b: Client-side sort handler for 50-row page" --parent <EPIC_1_ID> -p high -l bead -l test
# Spec: sortResults(results, sortConfig) returns new array sorted by column/direction
# Test: sort by name asc, desc, stable sort with equal keys, empty results
# Files: new sort-utils.ts or in campaign-results.ts
# Purity: pure function

crosslink issue create "Bead 1c: Wire onSortChange to Table component in results page" --parent <EPIC_1_ID> -p high -l bead -l test
# Spec: clicking column header updates sortConfig state, table re-renders sorted
# Test: click handler sets config, Table receives sortConfig + onSortChange props
# Files: +page.svelte
```

---

#### EPIC-3 Beads (SQL pagination — before EPIC-2/4)

```bash
crosslink issue create "Bead 3a: Add indexes on match_results and ocr_results FK columns" --parent <EPIC_3_ID> -p critical -l bead -l test
# Spec: match_results.matcher_job_id, match_results.ocr_result_id, ocr_results.crop_id have index=True
# Test: introspect SQLAlchemy metadata, assert indexes exist
# Files: match_result.py, ocr_result.py, new Alembic migration

crosslink issue create "Bead 3b: SQL pagination — CampaignQueryService" --parent <EPIC_3_ID> -p critical -l bead -l test
# Spec: get_campaign_results uses COUNT(DISTINCT) for total + LIMIT/OFFSET subquery for page
# Test: seed 1000 rows, assert page 1 loads only page_size, pages are disjoint, total correct
# Files: campaign_query_service.py
# Purity: offset/limit calc is pure; SQL execution is effectful

crosslink issue create "Bead 3c: SQL pagination — ResultsQueryService" --parent <EPIC_3_ID> -p critical -l bead -l test
# Spec: same pattern as 3b for job-level results
# Test: same test pattern
# Files: results_query_service.py

crosslink issue create "Bead 3d: SQL GROUP BY for metrics confidence counts" --parent <EPIC_3_ID> -p high -l bead -l test
# Spec: metrics uses select(confidence, count).group_by() instead of loading all rows
# Test: seed 100 results, assert GROUP BY query called, assert correct counts
# Files: metrics.py

crosslink issue create "Bead 3e: Scale benchmark — pagination with 10k results" --parent <EPIC_3_ID> -p medium -l bead -l test
# Spec: page request completes in < 100ms with 10k results
# Test: @pytest.mark.slow + pytest-benchmark
# Files: tests/benchmarks/test_pagination_performance.py
```

---

#### EPIC-2 Beads (crop endpoint)

```bash
crosslink issue create "Bead 2a: CropStorageAdapter protocol + LocalFileAdapter" --parent <EPIC_2_ID> -p high -l bead -l test
# Spec: get_image_url(crop_id) returns "/api/crops/{crop_id}/image". get_image_path returns Path or None.
# Test: valid crop_id → correct URL. Missing crop → None path.
# Files: new app/storage/crop_storage.py
# Purity: URL construction is pure. File existence check is effectful.

crosslink issue create "Bead 2b: GET /api/crops/{crop_id}/image endpoint" --parent <EPIC_2_ID> -p high -l bead -l test
# Spec: 200 + image/png + Cache-Control for existing crop. 404 for missing.
# Test: create temp PNG, hit endpoint, assert status/content-type/cache-control. Test 404.
# Files: new app/routers/crop_router.py, register in app/routers/__init__.py
# Effectful: FileResponse

crosslink issue create "Bead 2c: Add thumbnail_url to CampaignResultResponse" --parent <EPIC_2_ID> -p high -l bead -l test
# Spec: each result includes thumbnailUrl field resolved via CropStorageAdapter
# Test: assert response includes thumbnailUrl for each result
# Files: campaign_router.py, campaign_query_service.py

crosslink issue create "Bead 2d: Add thumbnail_url to ResultResponse (job-level)" --parent <EPIC_2_ID> -p medium -l bead -l test
# Spec: same as 2c for job-level results
# Test: same pattern
# Files: results_router.py, results_query_service.py
```

---

#### EPIC-4 Beads (frontend)

```bash
crosslink issue create "Bead 4a: Update CampaignResultResponse interface with thumbnailUrl" --parent <EPIC_4_ID> -p high -l bead -l test
# Spec: TypeScript interface includes thumbnailUrl: string
# Test: type-check passes, mock data includes field
# Files: campaign-results.ts

crosslink issue create "Bead 4b: Thumbnail column with loading=lazy in results table" --parent <EPIC_4_ID> -p high -l bead -l test
# Spec: each row renders <img src={thumbnailUrl} loading="lazy" width=60 height=40>
# Test: render table, assert img elements present with correct attributes
# Files: +page.svelte

crosslink issue create "Bead 4c: Accordion expand row with top-5 predictions" --parent <EPIC_4_ID> -p high -l bead -l test
# Spec: click row → expanded inline with enlarged crop + mini predictions table. Only 1 expanded at a time.
# Test: click row 1 → expanded. click row 2 → row 1 collapsed, row 2 expanded. click row 2 → collapsed.
# Files: +page.svelte (or extract ResultRowExpand.svelte)

crosslink issue create "Bead 4d: CropLightbox modal component" --parent <EPIC_4_ID> -p medium -l bead -l test
# Spec: click thumbnail → modal with full-size image. Escape/overlay click closes.
# Test: click thumbnail → modal visible. Press Escape → modal hidden. Click overlay → modal hidden.
# Files: new CropLightbox.svelte

crosslink issue create "Bead 4e: Image endpoint concurrency semaphore" --parent <EPIC_4_ID> -p medium -l bead -l test
# Spec: max 50 concurrent crop image requests
# Test: semaphore blocks request 51 until slot frees
# Files: crop_router.py
```

---

### Dependency Graph (block relationships)

```
EPIC-5 (hygiene) ──────────────────┐
EPIC-6 (refactor) ─────────────────┤
                                    ├── EPIC-1 (sort) ─── independent
                                    ├── EPIC-3 (pagination) ──┐
                                    │                         ├── EPIC-4 (frontend)
                                    └── EPIC-2 (crop API) ───┘
```

Set blocks in crosslink:
```bash
# EPIC-2 and EPIC-3 block EPIC-4
crosslink issue block <EPIC_4_ID> <EPIC_2_ID>
crosslink issue block <EPIC_4_ID> <EPIC_3_ID>

# EPIC-5 and EPIC-6 are prerequisites
crosslink issue block <EPIC_1_ID> <EPIC_5_ID>
crosslink issue block <EPIC_2_ID> <EPIC_5_ID>
crosslink issue block <EPIC_3_ID> <EPIC_5_ID>
crosslink issue block <EPIC_2_ID> <EPIC_6_ID>
crosslink issue block <EPIC_3_ID> <EPIC_6_ID>
```

---

### Relate to GitHub Issues

```bash
crosslink issue relate <EPIC_1_ID> <gh_issue_53_id>
crosslink issue relate <EPIC_2_ID> <gh_issue_39_id>
crosslink issue relate <EPIC_3_ID> <gh_issue_39_id>
crosslink issue relate <EPIC_4_ID> <gh_issue_38_id>
crosslink issue relate <EPIC_4_ID> <gh_issue_40_id>
```

---

## Phase 2 — TDD Execution Per Bead

For each bead, follow the TDD red-green-refactor cycle:

### RED
1. `crosslink session work <bead_id>`
2. `crosslink session action "RED: <bead title>"`
3. Write ONE failing test asserting the spec contract
4. Run test — confirm FAILURE
5. Commit: `test(<scope>): add failing test for <bead>`

### DOMAIN (after RED)
1. Review test for primitive obsession
2. Create type stubs if needed (interfaces, protocols, value objects)
3. Confirm test still fails (compiles but assertion wrong)
4. `crosslink session action "DOMAIN: reviewed <bead>"`

### GREEN
1. Write minimum code to pass the failing test
2. Run full test suite — nothing else breaks
3. Commit: `feat(<scope>): implement <bead>`

### DOMAIN (after GREEN)
1. Review implementation for domain violations
2. Check purity boundaries maintained
3. Check no HTTP leaks in services
4. `crosslink session action "DOMAIN-REVIEW: <bead> clean"`

### COMMIT
1. Run full suite + lint + typecheck
2. Commit with conventional commit message
3. `crosslink issue tested <bead_id>`
4. Verify clean working tree
5. `crosslink session action "COMMITTED: <bead>"`

---

## Phase 3 — Adversarial Review (VDD Roast)

After all beads in an epic pass GREEN:

```bash
crosslink issue create "Roast: <Epic title>" -l adversarial-review
crosslink issue relate <roast_id> <epic_id>
```

### Review Dimensions

1. **Spec Fidelity:** Does implementation satisfy the behavioral contract?
2. **Test Quality:** Tautological tests? Over-mocking? Missing edge cases?
3. **Purity Boundaries:** Side effects in pure core? HTTP leaks in services?
4. **Concurrency:** Race conditions in accordion state? Semaphore correctness?
5. **Performance:** Any N+1 queries? Unbounded collections? Missing indexes?
6. **Security:** Path traversal in crop endpoint? SQL injection via sort params?

### For each finding:
```bash
crosslink issue comment <roast_id> "FINDING: <location> | <problem> | <fix>"
# Create fix bead if legitimate:
crosslink issue create "Fix: <finding description>" --parent <epic_id> -p high -l bead
crosslink issue block <fix_id> <roast_id>
```

### Convergence signal
Adversary invents fictional problems → close roast, close epic.

---

## Phase 4 — Session Handoff Protocol

End every session with:
```bash
crosslink session end --notes "
Phase: <current phase>
Completed beads: <list>
Current work: <bead_id and status>
Adversary findings: <count and status>
Blockers: <any>
Next: <what to pick up>
"
```

Resume next session:
```bash
crosslink session start
crosslink session last-handoff
crosslink issue next
```

---

## Async Strategy (Reiterated)

| Layer | Pattern | Why |
|---|---|---|
| Router endpoints | `async def` + `asyncio.to_thread()` for sync service calls | Non-blocking event loop |
| Crop image endpoint | `async def` + semaphore(50) | Concurrent file I/O bounded |
| SSE streams | Already async + max lifetime 1hr | Prevent abandoned connections |
| Query services | Stay sync (SQLModel sync sessions) | Async SQLModel is immature |
| Matching pipeline | Background tasks (existing) | Not in request path |
| Frontend thumbnails | `loading="lazy"` native browser | No JS overhead |

---

## Commit Convention

```
test(<scope>): add failing test for <bead>           # RED
feat(<scope>): implement <bead>                       # GREEN
refactor(<scope>): extract <thing> for <reason>       # REFACTOR
fix(<scope>): address adversarial finding <id>        # ADVERSARIAL FIX
perf(<scope>): <optimization>                         # PERFORMANCE
test(<scope>): add scale benchmark for <thing>        # SCALE TEST
chore(<scope>): cleanup <thing>                       # HYGIENE
```
