# Session Handoff — Crops in Results Implementation

> **You are a fresh agent picking up this work. Read this file first.**
> It tells you: what to do, where the plan is, what skills to load, what decisions are locked.

## Branch

All work lives on **`feat/crops-in-results`** (branched from `origin/main` at `11cef67`). `main` is clean and even with origin.

## Current State

### Completed

- **EPIC-5 (Memory Hygiene)** — DONE, committed as `6b0d67b`
  - Bead 5a: `DemoMatchingTaskMonitor._cleanup_task()` clears dicts in `monitor_job` finally block + `publish_updated_task_status` on terminal status
  - Bead 5b: `SupabaseEngine._get_engine()` passes `pool_recycle=300, pool_pre_ping=True`
  - Bead 5c: `SSETransport._create_stream_generator()` wrapped in `asyncio.timeout(3600)`
  - 10 new tests

- **EPIC-6 (Architecture Hygiene)** — DONE (7/7 beads, roasted), committed as `6070def`
  - Bead 6a (PredictionBuilder) — `638393a`. 19 tests.
  - Bead 6b (OcrTextParser) — `e1be4c4`. 14 tests.
  - Bead 6c (Shared Test Fixtures) — `da22b9c`. -112 lines.
  - Bead 6d+6e (Stream CSV + Extract HTTP) — `1a9227c`, `c6f3d21`
  - Readability pass — `f511b8e`
  - Bead 6f (Remove _providers) + Bead 6g (Edge case tests) + roast fix — `6070def`
  - VDD Roast: 9 findings. 1 fix applied (structlog lazy formatting). 8 deferred (known tech debt → EPIC-3, cosmetic).

- **EPIC-1 (Sort Fix)** — DONE, committed as `d076d56`
  - `sortResults` pure function in `campaign-results.ts` — sorts by confidence, name, address, score
  - `sortConfig` state + `onSortChange` wired to Table component in results page
  - Follows campaigns page pattern exactly (import SortConfig from Table.svelte)
  - 14 unit tests in `campaign-results.test.ts`: ascending, descending, stable sort, null config, no predictions, empty array, unknown column

- **EPIC-3 (SQL Pagination)** — DONE, committed as `0c81f50`
  - `CampaignQueryService.get_campaign_results`: replaced `.all()` + Python pagination with `COUNT(DISTINCT)` + `LIMIT/OFFSET` subqueries. Memory O(N) → O(page_size).
  - `ResultsQueryService.get_results`: same SQL pagination rewrite.
  - `MetricsService._count_processed_results`: SQL `GROUP BY confidence_level` + `COUNT(DISTINCT ocr_result_id)` replaces Python grouping.
  - Indexes on `match_results(ocr_result_id, matcher_job_id, voter_id)` and `ocr_results(crop_id, ocr_job_id)`.
  - Supabase migration: `20250827234500_add_pagination_indexes.sql`
  - New test: `test_pages_are_disjoint_by_ocr_result_id`

- **Docs** — `0bb9855`. `matching-algorithm.md` rewritten. New `results-performance.md`.
- **Code quality standards** — moved to `AGENTS.md → Code Quality` (`e8582c6`)

### EPIC-2 (Crop API endpoint) — DONE, committed as `722763a`

- **Bead 2a (CropStorageAdapter protocol + LocalFileAdapter)** — DONE
  - New `app/storage/__init__.py`, `app/storage/crop_storage.py`
  - `CropStorageAdapter`: `runtime_checkable` Protocol with `get_image_url(crop_id) -> str` (pure) and `get_image_path(crop_id) -> Path | None` (effectful — DB + filesystem)
  - `LocalFileAdapter(session, storage_base=...)`: implements protocol. URL = `/api/crops/{crop_id}/image`. Path resolves via `PetitionCrop.stored_path` + `Path.resolve()` + `is_relative_to(storage_base)` + `Path.is_file()` check.
  - 8 tests in `tests/unit/storage/test_crop_storage.py`: URL generation, injectivity, idempotency, path found, path None for missing crop, path None for missing file, path traversal rejection, protocol conformance

- **Bead 2b (GET /api/crops/{crop_id}/image endpoint)** — DONE
  - New `app/routers/crop_router.py`, registered in `app/routers/__init__.py` + `app/api.py`
  - Sync endpoint: looks up crop via `LocalFileAdapter.get_image_path()`, returns `FileResponse` with `media_type="image/png"` + `Cache-Control: public, max-age=86400, immutable`. 404 if crop missing or file deleted.
  - 6 tests in `tests/unit/routers/test_crop_router.py`: 200 + content-type, cache-control headers, 404 missing crop, 404 missing file, response bytes match disk, path traversal 404

- **Bead 2c (thumbnail_url in CampaignResultResponse)** — DONE
  - `thumbnail_url: str` field on `CampaignResultResponse` in `campaign_router.py`
  - Populated inline in `campaign_query_service.py:151`: `f"/api/crops/{crop_id}/image" if crop_id else ""`
  - Test: `test_campaign_query_service.py::test_results_include_thumbnail_url`

- **Bead 2d (thumbnail_url in ResultResponse)** — DONE
  - `thumbnail_url: str` field on `ResultResponse` in `results_router.py`
  - Populated inline in `results_query_service.py:124`: same pattern as 2c
  - Test: `test_results_query_service.py::test_results_include_thumbnail_url`
  - Fixed unused imports in `test_crop_storage.py` (Path, JobStatus, MatcherJob, OcrResult)

- **VDD Roast EPIC-2** — DONE, fix committed as `7632e93`
  - 6 findings. 1 fixed (path traversal — `get_image_path` now validates `is_relative_to(storage_base)`). 5 deferred (URL triplication deliberate, dead method cosmetic, test DRY LOW, missing edge case LOW).
  - `LocalFileAdapter.__init__` now accepts `storage_base: Path | None` param, defaults to `os.getenv("UPLOAD_DIR", "./uploads")`.
  - Router tests set `UPLOAD_DIR` via `monkeypatch.setenv` to `tmp_path` for file-based tests.

### EPIC-4 (Frontend thumbnails + accordion) — IN PROGRESS

- **Bead 4a (thumbnailUrl on CampaignResultResponse)** — DONE, `7d21c59`
  - Added `thumbnailUrl: string` to `CampaignResultResponse` interface in `campaign-results.ts`
  - Updated `makeResult` default + type-contract test
  - 2 new tests (field present, default empty string)

- **Bead 4b (Thumbnail column)** — DONE, `dee56ff`
  - `renderThumbnailCell(thumbnailUrl)` pure function — `<img loading="lazy" width="60" height="40">` or `—` placeholder
  - Added `{ key: 'thumbnail', label: 'Crop', sortable: false }` column to results page
  - Wired via `getTableRows` → `renderThumbnailCell(result.thumbnailUrl)`
  - 2 new tests (img attributes, empty placeholder)

- **Bead 4c (Accordion expand)** — PARTIAL, `toggleAccordion` committed as `6631ccb`
  - `toggleAccordion(currentExpanded, clickedId)` pure function — expand/collapse/switch logic
  - 4 new tests (expand null→id, collapse id→null, switch id→other, arbitrary ids)
  - **Still needed**: Table.svelte row expansion support + results page wiring + predictions mini-table

### Test count: ~1133 backend, 48 frontend (22 campaign-results + 26 existing in lib). Lint + typecheck clean.

### Next Work

1. **EPIC-4 (continued)** — remaining beads:
   - Bead 4c (cont): Add expandable row support to `Table.svelte` (`onRowClick`, `expandedRowId`, expanded row snippet). Wire into results `+page.svelte` — click row toggles panel with enlarged crop + top-5 predictions mini-table.
   - Bead 4d: CropLightbox modal — click thumbnail → full-size image modal. Escape/overlay closes.
   - Bead 4e: Backend semaphore — `asyncio.Semaphore(50)` in `crop_router.py`.
   - VDD Roast EPIC-4

## Pickup Instructions

1. `git checkout feat/crops-in-results`
2. Read **`AGENTS.md → Code Quality`** — project-wide standards
3. Load skills: `caveman` (lite), `vdd`/`vsdd`, `writing-svelte5` + `svelte-components` (for EPIC-4)
4. Read plan: `.agent-workspace/implementation-plan.md`
5. **EPIC-4** is next — frontend thumbnails + accordion. See plan for bead breakdown.
6. TDD cycle (RED → DOMAIN → GREEN → DOMAIN → COMMIT) per bead

## What This Is About

Embedding OCR crop thumbnails into the match results table, fixing sort headers, and performance hardening for 10k+ results. GitHub issues: #38, #39, #40, #53.

## Execution Order

1. ~~EPIC-5 (memory hygiene)~~ + ~~EPIC-6 (architecture refactor)~~ — **DONE**
2. ~~EPIC-1 (sort fix)~~ + ~~EPIC-3 (SQL pagination)~~ — **DONE**
3. ~~EPIC-2 (crop API endpoint)~~ — **DONE** (4/4 beads, committed `722763a`, roasted + path traversal fix `7632e93`)
4. EPIC-4 (frontend thumbnails + accordion) — IN PROGRESS (4a/4b done, 4c partial)

## Key Decisions Made

- Pattern A: Accordion expand (not side panel)
- Client-side sort Phase 1 (DONE), server-side Phase 2 (future)
- CropStorageAdapter pattern (LocalFileAdapter now, SupabaseStorageAdapter later)
- Sync query services + async router wrapping (not full async SQLModel migration)
- No formal proofs needed — property-based tests sufficient
- CSV export: service returns `(iterable, filename)`, router wraps in `StreamingResponse` (purity boundary enforced)
- CSV streaming: `yield_per(1000)` + on-demand OCR/voter caching, never `.all()`
- SQL pagination: `COUNT(DISTINCT)` + `DISTINCT ... ORDER BY ... LIMIT/OFFSET` subquery pattern. Never loads all rows.
- Metrics GROUP BY: `SELECT confidence_level, COUNT(DISTINCT ocr_result_id) ... GROUP BY confidence_level WHERE rank=1`
- Crop URL pattern: `/api/crops/{crop_id}/image` — immutable, cached 24hr
- CropStorageAdapter.get_image_url is pure (no I/O). get_image_path is effectful (DB + filesystem + path validation).
- LocalFileAdapter validates resolved path against storage_base via `is_relative_to`. Prevents path traversal.
- Crop router is sync — no async needed for file serving at current scale. Concurrency semaphore deferred to EPIC-4 Bead 4e.

## Code Quality Notes

Project-wide standards live in **`AGENTS.md → Code Quality`** section. Read it. It covers readability patterns (PEP 20), legacy refactoring rules, test discipline, and nesting watch.

Session-specific notes:

- **EPIC-3 SQL pattern**: Both query services use identical 3-query pattern: (1) COUNT subquery for total, (2) DISTINCT+ORDER BY+LIMIT/OFFSET for page IDs, (3) SELECT WHERE id IN (page_ids) for match results. See `campaign_query_service.py:75-104` and `results_query_service.py:63-91`.
- **Nesting watch**: `_generate_csv_rows` in `results_query_service.py` had deeply nested ifs flattened to ternary/guard patterns. Unchanged by EPIC-3. See commit `c6f3d21`.
- **Test discipline reference**: See `TestCsvExport` in `test_results_query_behavior.py` for behavioral-contract testing pattern. See `campaign-results.test.ts` for pure-function sort testing.
- **basedpyright**: 2 false positives on `order_by()` args (SQLModel type stub limitation). Pre-existing errors unchanged.
- **In-codebase examples of AGENTS.md patterns**: `PredictionBuilder.format_voter_name` (filter+join), `OcrTextParser.format_text` (extracted helper), `ResultsQueryService.CSV_HEADER` (class constant), `sortResults` in `campaign-results.ts` (pure sort function with switch/case value extraction).
- **SQLite yield_per limitation**: `yield_per(chunk_size)` on SQLite dialect buffers full result set. Streaming benefit is aspirational on SQLite; real benefit on Supabase Postgres. SQL pagination (EPIC-3) solves the memory problem differently via LIMIT/OFFSET.
- **Frontend sort pattern**: Results page follows campaigns page pattern exactly. Import `SortConfig` from `Table.svelte`, add `$state<SortConfig | null>`, define sort function, pass `sortConfig` + `onSortChange` to Table.
- **Frontend thumbnail column**: First column `{ key: 'thumbnail', sortable: false }`. Cell HTML from `renderThumbnailCell(result.thumbnailUrl)` pure function. `loading="lazy"` + 60x40px + rounded.
- **Frontend accordion state**: `toggleAccordion(expandedId, clickedId)` pure function. Returns `null` if same row clicked, else `clickedId`. Used via `$state<number | null>(null)` in results page.
- **Backend thumbnailUrl**: Backend returns `thumbnailUrl` (camelCase via `ApiModel` alias generator in `app/api_models/__init__.py`). Field is `thumbnail_url: str` in Python → `thumbnailUrl` in JSON. Always present (empty string when no crop).
- **Table.svelte extension needed**: For Bead 4c, Table needs `onRowClick`, `expandedRowId`, and expanded row content snippet. This is the key architectural decision for next session. Keep it minimal — don't over-generalize.
- **EPIC-2 new files**: `app/storage/crop_storage.py` (CropStorageAdapter protocol + LocalFileAdapter), `app/routers/crop_router.py` (GET image endpoint), `tests/unit/storage/test_crop_storage.py` (8 tests), `tests/unit/routers/test_crop_router.py` (6 tests).
- **thumbnail_url approach**: Inline `f"/api/crops/{crop_id}/image"` in service layer. Don't inject adapter — keeps service pure of storage concerns. URL is a stable convention, not a lookup.
- **Crop router test pattern**: Uses same `StaticPool` + `dependency_overrides` pattern as `test_results_router.py`. File-based tests use `monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))`.
- **Path traversal guard**: `LocalFileAdapter.get_image_path()` calls `Path.resolve()` + `is_relative_to(storage_base)`. `storage_base` defaults to `UPLOAD_DIR` env var or `./uploads`. Tests pass explicit `storage_base`.

## Required Skills

### Installed (global)
| Skill | Location | Purpose |
|---|---|---|
| `writing-svelte5` | `~/.agents/skills/writing-svelte5/SKILL.md` | Svelte 5 runes, prevents Svelte 4 patterns |
| `svelte-components` | `~/.agents/skills/svelte-components/SKILL.md` | Bits UI, Melt UI component library patterns |
| `tdd` | `~/.agents/skills/tdd/SKILL.md` | Red-green-refactor 5-step cycle, phase boundary enforcement |
| `vdd` | `.agents/skills/vdd/SKILL.md` (project) | Builder/Adversary loop, adversarial refinement |
| `vsdd` | `.agents/skills/vsdd/SKILL.md` (project) | Spec → TDD → Adversary → Formal pipeline |

### Project-level skills (in repo)
| Skill | Location | Purpose |
|---|---|---|
| `caveman` | `.agents/skills/caveman/SKILL.md` | Ultra-compressed comms (always-on lite per AGENTS.md) |
| `caveman-commit` | `.agents/skills/caveman-commit/SKILL.md` | Conventional commit messages |

### Load order per bead
1. `caveman` — auto-active per AGENTS.md. Lite mode. Drop filler only.
2. `tdd` — for the red-green-refactor cycle
3. `vdd` or `vsdd` — for adversarial review after epic completion
4. `writing-svelte5` + `svelte-components` — for EPIC-4 frontend beads only

### Token efficiency rules (mandatory)
- Caveman **lite** mode active. `/caveman lite` if not already set.
- Keep articles + full sentences. Drop filler/hedging/pleasantries only.
- Switch to `full` only for crosslink breadcrumbs and session actions.
- Switch to `normal mode` for: security warnings, destructive ops, multi-step sequences where fragment order risks misread, domain review escalations.
- Commit messages: use `caveman-commit` skill — subject ≤50 chars, body only when "why" non-obvious
- Adversarial findings: one line each — `location | problem | fix`
- Crosslink session actions: `RED: bead 2a`, `GREEN: bead 2a`
- Session handoff: terse bullet list, full sentences
- Code: no comments unless asked. No docstrings unless public API.
- Tests: BDD-style `"""Scenario: ..."""` docstrings on test methods only (matches existing pattern)
- Plan updates: edit existing plan file, don't rewrite entire it

### Document hygiene (per epic completion)
- Remove `.agent-workspace/crop-ui-prototypes.html` after EPIC-4 completes (prototype served its purpose)
- Update `docs/architecture/c4-components.md` — add CropRouter, CropStorageAdapter, PredictionBuilder after EPIC-2 and EPIC-6
- Update `docs/architecture/project-structure.md` — add `app/storage/` module after EPIC-2
- Write ADR for SQL pagination pattern in `docs/architecture/decisions/` after EPIC-3
- Write ADR for CropStorageAdapter pattern after EPIC-2
- Amend `docs/development/results-performance.md` if benchmarks reveal different characteristics than expected
- Remove this `.agent-workspace/` directory when all epics close — plans/handoffs are session artifacts, not permanent docs
- Stale doc check: before closing each epic, `grep -r` for any references to old pagination/metrics patterns in docs and update

### Automation without quality sacrifice
- `crosslink next` — auto-suggests next bead. Follow it.
- `crosslink session action` — log progress after every phase. Survives context compression.
- Run lint + typecheck after every GREEN phase. No exceptions.
- Run `pytest-benchmark` for EPIC-3 scale tests. Capture numbers in crosslink comments.
- Frontend: run `svelte-check --tsconfig ./tsconfig.json` after every Svelte file change.
- Use parallel tool calls where possible — read files in parallel, run independent tests in parallel.
- Batch related beads in one session where dependencies allow.

### Pre-commit note
- `PRE_COMMIT_ALLOW_NO_CONFIG=1` needed for crosslink session/lock git commits (no .pre-commit-config.yaml)
- detect-secrets flags test URLs with `user:pass@host` — use `# pragma: allowlist secret`

### Stack-specific skills (available via `bunx skills read`)
| Skill | Trigger |
|---|---|
| `python-core` | Any backend Python work |
| `python-pytest` | Writing test fixtures, parametrize, mocking |
| `python-type-checking` | basedpyright config, type hints |
| `python-performance-optimization` | EPIC-3 pagination benchmarks |
| `sql-optimization-patterns` | EPIC-3 SQL rewrite |
| `fastapi-templates` | EPIC-2 crop router |
| `postgresql` | Supabase Postgres index/migration work |
| `security-best-practices` | Crop endpoint path traversal prevention |

## Crosslink Issue Map

| Crosslink ID | Epic/Bead | Status |
|---|---|---|
| #5 | EPIC-5: Memory hygiene | **DONE** |
| #7 | Bead 5a: Monitor cleanup | **DONE** |
| #8 | Bead 5b: Pool recycle | **DONE** |
| #9 | Bead 5c: SSE max lifetime | **DONE** |
| #6 | EPIC-6: Architecture hygiene | **DONE** (7/7 beads, roasted) |
| #10 | Bead 6a: PredictionBuilder | **DONE** |
| #11 | Bead 6b: OcrTextParser | **DONE** |
| #12 | Bead 6c: Shared test fixtures | **DONE** |
| #13 | Bead 6d: Stream CSV export | **DONE** |
| #14 | Bead 6e: Extract HTTP concern | **DONE** |
| #15 | Bead 6f: Remove _providers | **DONE** |
| #16 | Bead 6g: Edge case tests | **DONE** |
| #1 | EPIC-1: Sort fix | **DONE** |
| #3 | EPIC-3: SQL pagination | **DONE** |
| #2 | EPIC-2: Crop API endpoint | **DONE** (4/4 beads, roasted, fix `7632e93`) |
| #4 | EPIC-4: Frontend thumbnails | **IN PROGRESS** (4a/4b done, 4c partial) |
