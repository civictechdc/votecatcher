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
  - 10 new tests, 840 total passing

- **EPIC-6 (Architecture Hygiene)** — 5 of 7 beads done
  - Bead 6a (PredictionBuilder) — `638393a`. Extracted `PredictionBuilder.build()` from both query services. Cross-service import eliminated. 19 tests.
  - Bead 6b (OcrTextParser) — `e1be4c4`. `format_text()` + `extract_name_and_address()`. 14 tests. All 3 call sites wired.
  - Bead 6c (Shared Test Fixtures) — `da22b9c`. Consolidated `engine()`/`session()` into `conftest.py`. -112 lines.
  - Bead 6d+6e (Stream CSV + Extract HTTP) — `1a9227c`, tests refined `c6f3d21`
    - `export_results_csv` returns `(Iterator[str], str)` — no `StreamingResponse` in service
    - Query uses `yield_per(1000)` with `order_by(ocr_result_id, rank)` for ordered streaming
    - OCR/voter lookups cached on-demand in generator, no bulk `.all()`
    - Router wraps result in `StreamingResponse`
    - New `tests/unit/routers/test_results_router.py` (2 integration tests)
    - Tests assert behavior: iterable+filename contract, `.all()` never called, incremental yield
    - Nested ifs flattened to ternary/guard patterns (commit `c6f3d21`)

- **Docs** — `0bb9855`. `matching-algorithm.md` rewritten. New `results-performance.md`.

### Test count: 879 passing. Lint clean.

### Next Work

1. **Bead 6f**: Remove dead `_providers` dict from `DemoMatchingTaskMonitor` (LOW, quick)
2. **Bead 6g**: Add missing edge case tests for `get_setup_status` in `CampaignQueryService` (MEDIUM)
3. **EPIC-6 VDD Roast**: Adversarial review of all EPIC-6 beads after 6f+6g complete
4. After EPIC-6 closes: **EPIC-1 (sort) + EPIC-3 (pagination)** in parallel
5. Then EPIC-2 (crop API), then EPIC-4 (frontend)

## Pickup Instructions

1. `git checkout feat/crops-in-results`
2. Load skills: `caveman` (lite), `tdd`, `vsdd`
3. Read plan: `.agent-workspace/implementation-plan.md`
4. **Start with bead 6f** (quick `_providers` removal), then 6g
5. After both: run VDD adversarial roast on EPIC-6, then close it
6. TDD cycle (RED → DOMAIN → GREEN → DOMAIN → COMMIT) per bead

## What This Is About

Embedding OCR crop thumbnails into the match results table, fixing sort headers, and performance hardening for 10k+ results. GitHub issues: #38, #39, #40, #53.

## Execution Order

1. ~~EPIC-5 (memory hygiene)~~ + ~~EPIC-6 (architecture refactor)~~ — nearly done
2. EPIC-1 (sort fix) + EPIC-3 (SQL pagination) — can run in parallel
3. EPIC-2 (crop API endpoint) — depends on EPIC-5, EPIC-6
4. EPIC-4 (frontend thumbnails + accordion) — depends on EPIC-2, EPIC-3

## Key Decisions Made

- Pattern A: Accordion expand (not side panel)
- Client-side sort Phase 1, server-side Phase 2
- CropStorageAdapter pattern (LocalFileAdapter now, SupabaseStorageAdapter later)
- Sync query services + async router wrapping (not full async SQLModel migration)
- No formal proofs needed — property-based tests sufficient
- CSV export: service returns `(iterable, filename)`, router wraps in `StreamingResponse` (purity boundary enforced)
- CSV streaming: `yield_per(1000)` + on-demand OCR/voter caching, never `.all()`

## Code Quality Notes

- **Nesting watch**: `_generate_csv_rows` in `results_query_service.py` had deeply nested ifs flattened to ternary/guard patterns. Re-check after EPIC-3 pagination changes. See commit `c6f3d21`.
- **Test discipline**: Tests assert behavioral contracts (what), not implementation details (how). No `yield_per(1000)` mock, no `repr(type(...))` checks. See `TestCsvExport` in `test_results_query_behavior.py` as reference pattern.
- **basedpyright**: 2 new false positives on `order_by()` args (SQLModel type stub limitation). Pre-existing errors unchanged.
- **Legacy refactoring**: When touching existing code, apply small safe cleanups in the same commit: flatten nested ifs to guards/ternary, replace `isinstance` chains with dispatched helpers, extract repeated conditionals. Don't expand scope — only refactor what's already being modified. Leave the neighbourhood cleaner than you found it.

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
- Plan updates: edit existing plan file, don't rewrite entire thing

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
| #6 | EPIC-6: Architecture hygiene | In progress (5/7 beads) |
| #10 | Bead 6a: PredictionBuilder | **DONE** |
| #11 | Bead 6b: OcrTextParser | **DONE** |
| #12 | Bead 6c: Shared test fixtures | **DONE** |
| #13 | Bead 6d: Stream CSV export | **DONE** |
| #14 | Bead 6e: Extract HTTP concern | **DONE** |
| #15 | Bead 6f: Remove _providers | Open |
| #16 | Bead 6g: Edge case tests | Open |
| #1 | EPIC-1: Sort fix | Open |
| #2 | EPIC-2: Crop API endpoint | Open |
| #3 | EPIC-3: SQL pagination | Open |
| #4 | EPIC-4: Frontend thumbnails | Open |
