# Session Handoff — Crops in Results Implementation

> **You are a fresh agent picking up this work. Read this file first.**
> It tells you: what to do, where the plan is, what skills to load, what decisions are locked.

## Branch

All work lives on **`feat/crops-in-results`** (branched from `origin/main` at `11cef67`). `main` is clean and even with origin.

## Current State

### Completed
- **EPIC-5 (Memory Hygiene)** — DONE, committed as `6b0d67b`
  - Bead 5a: `DemoMatchingTaskMonitor._cleanup_task()` clears `_events/_tasks/_providers` dicts in `monitor_job` finally block + `publish_updated_task_status` on terminal status
  - Bead 5b: `SupabaseEngine._get_engine()` passes `pool_recycle=300, pool_pre_ping=True`
  - Bead 5c: `SSETransport._create_stream_generator()` wrapped in `asyncio.timeout(3600)`
  - Tests: 7 + 2 + 1 new = 10 new tests, 840 total unit tests passing

- **Bead 6a (PredictionBuilder)** — DONE, committed as `638393a`
  - New `app/services/prediction_builder.py`: `PredictionData` (frozen dataclass), `PredictionBuilder` (stateless, pure `build()`, `format_voter_name()`, `format_voter_address()`)
  - `CampaignQueryService._build_campaign_predictions()` and `ResultsQueryService._build_predictions_from_match_results()` now delegate to `PredictionBuilder.build()`
  - Cross-service import (`ResultsQueryService` → `CampaignQueryService`) eliminated
  - `_format_voter_name`/`_format_voter_address` on `CampaignQueryService` now thin wrappers delegating to `PredictionBuilder`
  - 17 new tests + 2 parity tests. 860 total passing. Lint + typecheck clean.

- **Bead 6b (OcrTextParser)** — DONE, committed as `e1be4c4`
  - New `app/services/ocr_text_parser.py` with `format_text()` and `extract_name_and_address()`
  - 14 tests for OcrTextParser
  - All 3 call sites wired: `CampaignQueryService`, `ResultsQueryService.get_results()`, `ResultsQueryService.export_results_csv()`
  - Inline dict→string in `export_results_csv` replaced with `OcrTextParser.format_text()`
  - 874 total tests passing. Lint + typecheck clean.

- **Bead 6c (Shared Test Fixtures)** — DONE, committed as `da22b9c`
  - Removed duplicated `engine()`/`session()` fixtures from 8 service test files
  - All now use shared `tests/unit/services/conftest.py` fixture
  - Dead imports (`SQLModel`, `create_engine`, unused `Session`/`pytest`) cleaned up
  - Files: test_campaign_management_service, test_campaign_query_service, test_job_query_service, test_metrics_service, test_ocr_service, test_prediction_builder, test_results_query_service, test_session_service
  - 2 files kept custom fixtures (test_config_service: custom table SQL; test_matching_service: SqliteEngine class)
  - 874 tests passing. Lint clean. -112 lines.

- **Beads 6d+6e (Stream CSV + Extract HTTP)** — DONE, committed as `1a9227c`, tests refined as `c6f3d21`
  - `export_results_csv` returns `(Iterator[str], str)` — no `StreamingResponse` in service
  - Query uses `yield_per(1000)` with `order_by(ocr_result_id, rank)` for ordered streaming
  - OCR/voter lookups cached on-demand (no bulk `.all()`)
  - Router wraps result in `StreamingResponse`
  - New `tests/unit/routers/test_results_router.py` (2 integration tests)
  - 879 total tests passing. Lint clean.
  - Tests assert behavior (iterable+filename contract, no `.all()` called, incremental yield) not implementation details (no `yield_per(1000)` mock, no type repr checks)

- **Docs** — committed as `0bb9855`
  - `matching-algorithm.md` rewritten for spec-driven architecture (pluggable engines, field specs, parity data)
  - New `docs/development/results-performance.md`
  - `docs/development/README.md` index updated

### Next Work
- **EPIC-6 (Architecture Hygiene)** — remaining beads, all unblocked
  - Bead 6f: Remove dead _providers dict from DemoMatchingTaskMonitor (LOW)
  - Bead 6g: Add missing edge case tests for get_setup_status (MEDIUM)
  - Suggested order: 6f (quick), then 6g
- After EPIC-6: EPIC-1 (sort) + EPIC-3 (pagination) in parallel
- Then EPIC-2 (crop API), then EPIC-4 (frontend)

## Pickup Instructions

1. `git checkout feat/crops-in-results`
2. Load skills: `caveman` (lite mode), `tdd`, `vsdd`
3. Read plan: `.agent-workspace/implementation-plan.md`
4. **Start with bead 6f** (quick _providers removal), then 6g (edge case tests)
5. Begin TDD cycle (RED → DOMAIN → GREEN → DOMAIN → COMMIT) per bead

## What This Is About

Embedding OCR crop thumbnails into the match results table, fixing sort headers, and performance hardening for 10k+ results. GitHub issues: #38, #39, #40, #53.

## Execution Order

1. ~~EPIC-5 (memory hygiene)~~ + EPIC-6 (architecture refactor) — prerequisite for everything
2. EPIC-1 (sort fix) + EPIC-3 (SQL pagination) — can run in parallel
3. EPIC-2 (crop API endpoint) — depends on EPIC-5, EPIC-6
4. EPIC-4 (frontend thumbnails + accordion) — depends on EPIC-2, EPIC-3

## Key Decisions Made

- Pattern A: Accordion expand (not side panel)
- Client-side sort Phase 1, server-side Phase 2
- CropStorageAdapter pattern (LocalFileAdapter now, SupabaseStorageAdapter later)
- Sync query services + async router wrapping (not full async SQLModel migration)
- No formal proofs needed — property-based tests sufficient

## Required Skills

### Installed (global)
| Skill | Location | Purpose |
|---|---|---|
| `writing-svelte5` | `~/.agents/skills/writing-svelte5/SKILL.md` | Svelte 5 runes, prevents Svelte 4 patterns |
| `svelte-components` | `~/.agents/skills/svelte-components/SKILL.md` | Bits UI, Melt UI component library patterns |
| `tdd` | `~/.agents/skills/tdd/SKILL.md` | Red-green-refactor 5-step cycle, phase boundary enforcement |
| `vdd` | `.agents/skills/vdd/SKILL.md` (project) | Builder/Adversary loop, adversarial refinement |
| `vsdd` | `.agents/skills/vsdd/SKILL.md` (project) | Spec → TDD → Adversarial → Formal pipeline, crosslink integration |

### Project-level skills (in repo)
| Skill | Location | Purpose |
|---|---|---|
| `caveman` | `.agents/skills/caveman/SKILL.md` | Ultra-compressed comms (always-on lite per AGENTS.md) |
| `caveman-commit` | `.agents/skills/caveman-commit/SKILL.md` | Conventional commit messages |

### Load order per bead
1. `caveman` — auto-active per AGENTS.md. Full mode. All comms terse. Code/commits/PRs normal.
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
- Batch related beads in one session where dependencies allow (e.g., EPIC-5 beads 5a+5b+5c together).

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
| #6 | EPIC-6: Architecture hygiene | In progress |
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
