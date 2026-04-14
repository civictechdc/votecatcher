# Configurable Field Specs — Gated Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Skill Discovery:** Use `bunx openskills read <name>` to load skills. NOT `npx`. See `plans/configurable-field-specs.md` → "Agent Skills & Tools Reference" for the full per-gate skill map.
>
> **MCP Tools:** Use `utcp-code-mode_*` tools for batch operations, Svelte docs, Playwright browser automation, and tool chaining.

**Goal:** Replace hardcoded region-specific field handling with a spec-driven system loaded from JSON5 source files.

**Architecture:** Hexagonal (outside-in). Domain layer is pure Pydantic — no DB, no framework. Adapters implement Protocol contracts. Each gate requires all tests green + automated checks pass before proceeding.

**Tech Stack:** Python 3.13+, Pydantic v2, SQLModel, FastAPI, json5, ApprovalTests, rapidfuzz

**TDD Discipline:** Every task follows red-green-refactor. Write ONE test → verify it fails → write minimal code → verify it passes → commit. No horizontal slicing (no "write all tests first"). Vertical tracer bullets only.

**Spec Document:** `plans/configurable-field-specs.md` (full architecture, domain models, BDD scenarios)

---

## Branch & Worktree Strategy

**Methodology:** [Trunk-Based Development](https://trunkbaseddevelopment.com/) with gate-scoped feature flags for safe incremental integration.

### Feature Flags (Gate Integration Guards)

Each gate has a feature flag that guards its integration point. **Flag `False` = old code path (no behavior change). Flag `True` = new spec-driven code path active.** This enables merging to `main` after each gate without breaking the running app.

Flags live in `FeatureConfig` (Pydantic model) and are sourced from `FEATURE_*` env vars via `pydantic-settings`. They're internal-only — not exposed in the API response (unlike `simulation_mode`, `demo_mode`).

#### Flag Definitions

| Flag | Env Var | Default | Guards | Flipped `True` in | Removed in |
|------|---------|---------|--------|-------------------|------------|
| `field_spec_domain` | `FEATURE_FIELD_SPEC_DOMAIN` | `False` | Domain types available for import (no runtime effect — pure types) | G1 | G10 (flag deleted) |
| `field_spec_persistence` | `FEATURE_FIELD_SPEC_PERSISTENCE` | `False` | `region_field_specs` table exists, repo available | G4 | G10 |
| `field_spec_loading` | `FEATURE_FIELD_SPEC_LOADING` | `False` | `load_all_specs()` runs at startup, specs in DB | G6 | G10 |
| `field_spec_matching` | `FEATURE_FIELD_SPEC_MATCHING` | `False` | `MatchingService` uses spec-driven weights/templates instead of hardcoded keys | G7 | G10 |
| `field_spec_voter_list` | `FEATURE_FIELD_SPEC_VOTER_LIST` | `False` | `VoterListService` uses spec-driven CSV parsing and hash fields | G8 | G10 |
| `field_spec_api` | `FEATURE_FIELD_SPEC_API` | `False` | `GET /regions` endpoint + region selector in frontend | G9 | G10 |
| `field_spec_cleanup` | `FEATURE_FIELD_SPEC_CLEANUP` | `False` | Old `RegionSchema`, `WashingtonDCRegisteredVoter`, hardcoded paths removed | G10 | G10 (immediately) |

#### Pydantic Settings Implementation

**File:** `backend/app/settings/providers/feature_config.py`

```python
from pydantic import BaseModel, Field, computed_field


class FieldSpecFlags(BaseModel):
    """Gate-scoped flags for configurable field specs feature.

    Each flag guards an integration boundary. False = old code path.
    All flags are removed in G10 once the feature is fully integrated.
    """

    domain: bool = Field(default=False)
    persistence: bool = Field(default=False)
    loading: bool = Field(default=False)
    matching: bool = Field(default=False)
    voter_list: bool = Field(default=False)
    api: bool = Field(default=False)
    cleanup: bool = Field(default=False)

    @computed_field
    @property
    def is_complete(self) -> bool:
        """All gates integrated — feature is fully active."""
        return all([
            self.domain, self.persistence, self.loading,
            self.matching, self.voter_list, self.api, self.cleanup,
        ])


class FeatureConfig(BaseModel):
    """Application-wide feature flags."""

    simulation: bool = Field(default=False)
    beta_features: bool = Field(default=False)
    debug_mode: bool = Field(default=False)
    demo_mode: bool = Field(default=False)
    field_specs: FieldSpecFlags = Field(default_factory=FieldSpecFlags)
```

**File:** `backend/app/settings/settings.py` — add env var sources:

```python
# In Settings class, add alongside existing feature_* fields:
feature_field_spec_domain: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_DOMAIN")
feature_field_spec_persistence: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_PERSISTENCE")
feature_field_spec_loading: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_LOADING")
feature_field_spec_matching: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_MATCHING")
feature_field_spec_voter_list: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_VOTER_LIST")
feature_field_spec_api: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_API")
feature_field_spec_cleanup: bool = Field(default=False, alias="FEATURE_FIELD_SPEC_CLEANUP")
```

#### Integration Point Guards

Each guard is a simple `if` check at the boundary between old and new code:

```python
# startup.py — G6
async def startup(self) -> None:
    self._db_initializer()
    if settings.features.field_specs.loading:
        self._spec_loader()
    self._config_validator()
    self._worker_task = asyncio.create_task(self._worker_starter())

# matching_service.py — G7
def calculate_similarity(self, ...):
    if settings.features.field_specs.matching:
        return self._spec_driven_similarity(spec, ocr, voter)
    return self._hardcoded_similarity(ocr, voter)

# voter_list_service.py — G8
def merge_voter_list(self, ...):
    if settings.features.field_specs.voter_list:
        return self._spec_driven_parse(spec, csv_data)
    return self._hardcoded_parse(csv_data)
```

#### Flag Lifecycle

```
G0: Add flag fields (all default False). No behavior change.
G1: domain=True — types importable, no runtime effect.
G2: Template renderer tested. domain already True.
G3: dc.json5 created. No runtime effect yet.
G4: persistence=True — table created, repo available. Old code still runs.
G5: Service implemented. persistence already True.
G6: loading=True — startup loads specs into DB. Old code paths still active.
G7: matching=True — MatchingService switches to spec-driven.
G8: voter_list=True — VoterListService switches to spec-driven.
G9: api=True — /regions endpoint active, frontend shows selector.
G10: cleanup=True — old code removed. All flags hardcoded True, then flags deleted.
```

After G10, `FieldSpecFlags` class and all `FEATURE_FIELD_SPEC_*` env vars are removed. The feature is no longer a feature — it's just how the app works.

#### Testing with Flags

Each gate's tests should include:

1. **Flag False test** — verify old behavior preserved (regression guard)
2. **Flag True test** — verify new spec-driven behavior
3. **Flag transition test** — verify data created under old path works under new path

```python
# Example: G7 matching test
def test_matching_uses_hardcoded_keys_when_flag_off(self):
    settings.features.field_specs.matching = False
    result = matching_service.match_ocr_result(ocr, voter)
    assert "name" in result.field_scores  # old hardcoded key

def test_matching_uses_spec_weights_when_flag_on(self):
    settings.features.field_specs.matching = True
    result = matching_service.match_ocr_result(spec, ocr, voter)
    assert len(result.field_scores) == len(spec.matchable_fields())
```

### Short-Lived Feature Branch

All G0–G10 work lands on one short-lived branch:

```
git checkout main && git pull
git checkout -b feat/configurable-field-specs
git push -u origin feat/configurable-field-specs
```

- **One PR** at the end (squash merge to `main`)
- **No per-gate branches** — gates enforced by commit prefix
- **Rebase on `main` frequently** — minimum before each gate entrance check

### Worktrees for Parallel Gates

G0–G2 (domain layer only) can run in an isolated worktree if parallel agents are available. G4+ must be sequential.

```bash
# Create worktree for G0–G2 domain work
git worktree add ../votecatcher-domain feat/configurable-field-specs
# ... work in ../votecatcher-domain ...
# Merge back when done
git worktree remove ../votecatcher-domain
```

**Load skill:** `bunx openskills read using-git-worktrees`

### Commit Convention

```
feat(field-spec): G<n> <description>
refactor(field-spec): G<n> <description>   # for G7, G8
chore(field-spec): G<n> <description>       # for G10
```

### Incremental Commits Within Gates

Do NOT accumulate all changes for a single gate into one large commit. Instead, make **regular commits grouping stable and logically related changes** as work progresses through a gate's tasks:

1. **Commit after each stable milestone** — each completed sub-task (e.g., G1.2, G1.4, G1.6) that leaves all tests green deserves its own commit
2. **Group related changes** — if two sub-tasks are tightly coupled (e.g., G4.2 DB model + G4.3 Protocol contract), commit them together
3. **Never commit red tests** — only commit when `uv run pytest tests/ -v` passes. If mid-refactor and tests are temporarily broken, keep working locally until green
4. **Use the gate commit prefix** — all commits within a gate use that gate's prefix (e.g., `feat(field-spec): G1 implement BallotField value object`)
5. **The final gate commit** — the last commit in a gate should reference the full gate name (e.g., `feat(field-spec): G1 domain value objects`) and is the one listed in the gate's exit checks

Example commit cadence for G1:
```
feat(field-spec): G1 implement BallotField value object          # after G1.2
feat(field-spec): G1 implement VoterRegField value object        # after G1.4
feat(field-spec): G1 implement FieldMapping and CropConfig       # after G1.6
feat(field-spec): G1 implement RegionFieldSpecConfig aggregate   # after G1.8
feat(field-spec): G1 domain value objects                        # final gate commit (G1.9+exit)
```

### Version Bump (before opening PR)

After G10 passes all exit checks and before opening the PR, bump app versions to reflect the new feature:

**Files to update:**
- `backend/pyproject.toml` — `version` field (currently `1.0.0-alpha.1`)
- `frontend/package.json` — `version` field (currently `1.0.0-alpha.1`)
- `supabase/functions/process-voter-file/package.json` — `version` field (currently `1.0.0`) — only if the edge function's interface or behavior changed

**Version bump rules:**
- If any API endpoints changed (new `GET /regions`, `create_campaign` region param), bump minor (e.g., `1.0.0-alpha.1` → `1.0.0-alpha.2` or `1.0.0` depending on release readiness)
- If only internal architecture changed (no API surface changes), bump patch or alpha suffix
- All three packages should share the same version if they're released together

**Commit:**
```
chore(field-spec): bump app versions for configurable field specs
```

**Verification:**
- [ ] `backend/pyproject.toml` version updated
- [ ] `frontend/package.json` version updated
- [ ] Edge function version updated (if affected)
- [ ] All versions consistent
- [ ] `uv sync` succeeds after version bump

---

## Related Issues & PRs

| # | Type | Title | Alignment | Status | Notes |
|---|------|-------|-----------|--------|-------|
| [#12](https://github.com/civictechdc/votecatcher/pull/12) | PR | Add configurable voter region specifications | **Direct predecessor** — same intent (configurable voter name/address components per region). Branch `voter_specs` is stale (769 files diverged, pre-SvelteKit codebase). Do NOT merge. Superseded by this plan. | OPEN (stale) | Contains early matching/OCR refactoring work — useful for reference but code is outdated |
| [#11](https://github.com/civictechdc/votecatcher/pull/11) | PR | Migration fixes and refactoring | Partial — subset of PR #12 (all commits included in `voter_specs`). FastAPI migration fixes. | OPEN (stale) | Superseded by PR #18 and this plan |
| [#21](https://github.com/civictechdc/votecatcher/issues/21) | Issue | Refactor: DDD restructuring of app/matching/ | **Overlaps G7** — proposes DDD value objects (`OcrCandidate`, `VoterCandidate`, `MatchScore`), unified scoring, dead code removal in matching module. Coordinate: this plan's G7 should be compatible with or subsume #21's matching changes. | OPEN | Contains detailed 30-commit plan for matching DDD. Consider implementing #21's Phase 2-4 alongside or after G7 to avoid conflicting refactors |
| [#18](https://github.com/civictechdc/votecatcher/pull/18) | PR | Backend hardening, brand updates, deploy fix | **Interacts with G6** — introduced `ApplicationStartup` class with DI-based startup lifecycle. G6.3 wires into this same startup flow. | MERGED | G6.3 must use the `ApplicationStartup` DI pattern from this PR |
| [#16](https://github.com/civictechdc/votecatcher/issues/16) | Issue | Address OS-level CVEs in Docker base image | Unrelated — Docker base image CVEs | OPEN | No coordination needed |

**Coordination strategy:**
- **PR #12 / #11:** Closed as superseded. The intent is preserved in this plan.
- **Issue #21:** **Deferred until after G10 completes.** #21 proposes matching DDD value objects that would need rewriting against the spec-driven architecture anyway. After this plan ships, open a new issue scoped to the post-spec matching layer. Close #21 at that point.
- **PR #18:** Already merged. G6 startup integration builds on its `ApplicationStartup` pattern.

---

## Progress Tracker

| Gate | Status | Tests | Notes |
|------|--------|-------|-------|
| G0: Dependencies & Editor Config | ✅ Complete | 924 pass | Fixed `PydanticUndefinedType` crash in settings.py (model_fields.default undefined for default_factory); hygiene tests phase-aware (DEFINED flags exempt); Pydantic v2.11 deprecation fixes |
| G1: Domain Value Objects | ✅ Complete | 34 pass | BallotField, VoterRegField, FieldMapping, CropConfig, RegionFieldSpecConfig aggregate root with validate_integrity (9 rules). Pure Pydantic, zero infra deps. ADR-0006 created. |
| G2: Template Renderer | ✅ Complete | 16 pass (14 BDD + 2 approval) | `render_template` + `_extract_placeholders` in domain layer. N/A sentinel handling, trailing punctuation cleanup, Apt label removal. Approval golden masters for DC address/name variants. ADR-0008 created. Approval testing how-to in docs/development/testing.md. Also fixed G0 gap: added json5/approvaltests deps to pyproject.toml. |
| G3: DC Spec Source File | ✅ Complete | 2 pass (approval + integrity) | `dc.json5` with 4 ballot fields, 21 voter reg fields, 4 mappings, 5 hash fields. Approval snapshot + integrity validation pass. `docs/development/field-spec-schema.md` reference doc created. `backend/app/regions/README.md` created. |
| G4: Persistence Layer | ✅ Complete | 11 pass | `RegionFieldSpecModel` with JSON columns, `FieldSpecRepository` Protocol in contracts.py, `FieldSpecRepositoryImpl` with upsert/findByRegionKey/listRegions/findByRegion/save/delete. Model registered in model_imports.py + data/models.py. Alembic migration created. `region_key` case-normalized (uppercase). Upsert auto-creates Region rows for G6.8. |
| G5: Application Service | ✅ Complete | 9 pass | `FieldSpecService` with `get_spec`, `get_spec_by_key`, `map_voter_to_ballot`, `validate_spec`. Uses mock repo (no DB). `FieldSpecNotFoundError` added to domain. Service imports only from `app/domain` and `app/persistence/contracts`. |
| G6: Spec Loading & Startup | ✅ Complete | 13 pass | `load_all_specs` in FieldSpecService with fail-fast. `SpecLoadingError` exception. Startup wired via `spec_loader` DI param in `ApplicationStartup`. Feature flag guard on `fieldspec.service.enabled`. `get_field_spec_service` DI provider in dependencies.py. region_key normalization (uppercase) and Region auto-creation covered by repo (G4) with loading tests confirming behavior. DC spec loads end-to-end via service. |
| G7: Matching Service Refactor | 🔄 In progress | 18 pass (5 adapter + 6 spec-driven + 1 approval + 5 pre_filter domain + 5 pre_filter integration — 3 overlap with spec-driven count) | **G7.0 DONE:** `flatten_voter_data` in `app/matching/voter_data_adapter.py` — flattens voter JSON blobs to flat dict keyed by voter_reg_field.id, category→blob mapping. **G7.1 DONE:** Baseline approval test captured in `test_matching_regression_approval.py` — 5 OCR inputs × 4 voters score matrix. **G7.2+G7.3 DONE:** `calculate_spec_driven_similarity` added to MatchingService — uses spec weights, render_template, flatten_voter_data. field_scores keyed by ballot_field.id. **G7.3a DONE:** `pre_filter_field_id` on RegionFieldSpecConfig + dc.json5. `pre_filter_voters_with_spec` method on MatchingService. Domain tests for `pre_filter_field()`. Integration tests with SQLite for pre-filter by address/name/geography category. **G7.4 DONE:** Baseline approval unchanged. **Remaining:** G7.5 cleanup, G7.6 doc full_name defaults, G7.7 worker.py consolidation, G7.8 matching-process.md, G7.9 C4 update. 1031 total tests pass. G5+G6 code committed (was previously uncommitted). |
| G8: Voter List Service Refactor | ⬜ Not started | — | Fixed: expanded with category→blob mapping (#8), G8.3/G8.4 for schema replacement; G8.2 expanded compute_data_hash to cover all categories (#19); noted 3 conflicting key schemas (#15) |
| G9: API & Frontend | ⬜ Not started | — | Fixed: added G9.5 create_campaign refactor (#14) |
| G10: Cleanup & Migration | ⬜ Not started | — | Fixed: added G10.5 data migration (#9); G10.6 rapidfuzz pin (#11); G10.7 JSON blob key migration (#15); clarified G10.1/G10.2 file scope (#8,#21); G10.8 demo code (#22); match_columns deferred (#23) |

### Status Key
- ⬜ Not started
- 🔄 In progress
- ✅ Complete (all gate checks pass)
- 🚫 Blocked

---

## Blockers / Issues / Questions

> **Log any blocker, unexpected issue, or design question here.** Include timestamp, gate, and resolution.

| # | Gate | Type | Description | Raised | Resolved |
|---|------|------|-------------|--------|----------|
| 1 | G0 | fix | G0.1 used Poetry syntax but project uses `uv` — use `[project.dependencies]` not `[tool.poetry.dependencies]` | 2025-04-13 | ✅ Fixed in plan |
| 2 | G4 | gap | `FieldSpecRepository` Protocol missing `list_regions()` — needed by G9 `GET /regions`. Added to G4.3 | 2025-04-13 | ✅ Fixed in plan |
| 3 | G4 | gap | `RegionFieldSpecModel.name` column exists in DB but not in domain `RegionFieldSpecConfig`. Need to source name during `upsert` | 2025-04-13 | ✅ Noted in G3/G4 |
| 4 | G6 | gap | No DI wiring gate — `FieldSpecService`/`FieldSpecRepository` never registered in FastAPI DI. Added G6.5 | 2025-04-13 | ✅ Fixed in plan |
| 5 | G6 | question | Startup spec loading: should app fail to start if a spec is invalid, or log and continue? Decision: fail-fast | 2025-04-13 | ✅ Decided: fail-fast |
| 6 | G7 | gap | `RegisteredVoter.name_data/address_data` are nested JSON blobs — no plan for how `render_template` gets a flat dict. Added G7.0 | 2025-04-13 | ✅ Fixed in plan |
| 7 | G7 | gap | `field_scores` in match results currently hardcoded `{name, address}`. Dynamic spec fields change this shape. Added note in G7.3 | 2025-04-13 | ✅ Noted |
| 8 | G8 | gap | `VoterListService.merge_voter_list()` hardcodes `name_data`/`address_data` field extraction. Spec categories must map to these blobs. Added G8.4 | 2025-04-13 | ✅ Fixed in plan |
| 9 | G10 | gap | No data migration plan for existing `region_schemas` rows in production DBs. Added G10.5 | 2025-04-13 | ✅ Fixed in plan |
| 10 | G2 | gap | `render_template` doesn't handle "N/A" values — spec approval test shows N/A street numbers but no test case for it | 2025-04-13 | ✅ Fixed: added test #11 + sentinel treatment |
| 11 | G7 | risk | `rapidfuzz` version changes may cause non-deterministic approval test failures. Pin version in `pyproject.toml` | 2025-04-13 | ✅ Fixed: G10.6 pins rapidfuzz |
| 12 | G3 | risk | `spec_path` uses 4-level relative navigation — fragile if test dir structure changes | 2025-04-13 | ✅ Noted in G3 |
| 13 | G6 | gap | `region_key` casing: `spec_file.stem.upper()` → `"DC"` but existing `Region.region_key` may differ. Need normalization convention | 2025-04-13 | ✅ Fixed: G6.7 normalization convention |
| 14 | G9 | gap | `CampaignManagementService._ensure_default_region()` hardcodes DC — `create_campaign` ignores `region` param, always uses DC. Blocks multi-region | 2025-04-13 | ✅ Fixed: G9.5 |
| 15 | G10 | gap | No migration for existing `RegisteredVoter` JSON blob keys (`street` → `street_number`, `zip` → `zip_code`, etc.). 3 conflicting key schemas across codebase: `VoterListService` uses `street`/`city`/`zip`, `MatchingService` uses `street_number`/`street_name`, `worker.py` uses `street`/`city`/`zip` | 2025-04-13 | ✅ Fixed: G10.7 |
| 16 | G6 | gap | `load_all_specs` FK failure if `Region` row doesn't exist — spec upsert needs `Region` row but none created at startup | 2025-04-13 | ✅ Fixed: G6.8 |
| 17 | G4 | gap | `model_imports.py` and `data/models.py` must be updated to register `RegionFieldSpecModel` for Alembic autogenerate | 2025-04-13 | ✅ Fixed: G4.5a |
| 18 | G7 | gap | `RegisteredVoter.full_name`/`is_matchable()` hardcode field keys (`first_name`, `last_name`) — need spec-awareness or deprecation note | 2025-04-13 | ✅ Noted in G7.6 |
| 19 | G8 | gap | `compute_data_hash` only searches `name_data`/`address_data` — misses hash fields in `other_field_data` (e.g., `ward`, `party`) | 2025-04-13 | ✅ Fixed: G8.2 expanded |
| 20 | G7 | gap | `pre_filter_voters` hardcodes `address_data["zip"]` — wrong key after spec refactor (spec uses `zip_code`) | 2025-04-13 | ✅ Fixed: G7.3a |
| 21 | G10 | gap | `test_region_schema.py` not listed for deletion when `RegionSchema` is removed | 2025-04-13 | ✅ Fixed: G10.1 |
| 22 | G10 | gap | `voter_processor.py` and `voter_schema.py` demo code not addressed — hardcodes DC columns | 2025-04-13 | ✅ Noted in G10.8 |
| 23 | G10 | gap | `match_columns.py` has no concrete refactor task — display constants only, low impact | 2025-04-13 | ✅ Noted: deferred |
| 24 | G7 | gap | `worker.py:950-963` has duplicate matching logic using old key schema (`street`/`city`/`zip`) — will silently break after spec refactor. Must consolidate into `MatchingService` | 2025-04-13 | ✅ Fixed: G7.7 |

---

## Gate Check Protocol

Every gate has **compulsory exit checks**. You MAY NOT proceed to the next gate until ALL checks pass.

### Automated Exit Checks (run every time)

```bash
# From backend/ directory
cd backend

# 1. All tests pass
uv run pytest tests/ -v --tb=short

# 2. Linter clean
uv run ruff check app/ tests/

# 3. Type check clean
uv run basedpyright app/
```

### Agent Exit Checks (manual verification)

After automated checks pass, the implementing agent MUST:

1. Confirm all tests introduced in this gate pass (not just existing tests)
2. Confirm no test was skipped or marked `xfail` to "pass" the gate
3. Confirm the code matches the spec in `plans/configurable-field-specs.md`
4. **Update the Progress Tracker** — change gate status to ✅ Complete, record test count, and write a concise summary of what was implemented, any design decisions made, and any deviations from the plan. If any notes are stale or inaccurate, correct them
5. Log any design decisions or deviations in the Questions section above
6. Commit with message: `feat(field-spec): G<n> <gate name>`

### Gate Entrance Checks (before starting a gate)

Before starting ANY gate:

1. Verify all previous gates are ✅ in the Progress Tracker
2. **Update the Progress Tracker** — confirm the current gate shows 🔄 In progress with an accurate summary of what's about to begin. Update any stale notes on prior gates if circumstances changed since they were completed
3. Run automated exit checks from the PREVIOUS gate to confirm still green
4. Read any new blockers/issues logged since last gate
5. If blocked → stop, log it, ask for resolution

---

## G0: Dependencies & Editor Config

**Purpose:** Install dependencies and set up editor configs so all subsequent work has tooling support.

**Load skills:** `bunx openskills read uv-package-manager python-core`

**Files:**
- Modify: `backend/pyproject.toml` (add json5, approvaltests, pytest-approvaltests)
- Create: `.vscode/settings.json`, `.vscode/extensions.json`, `.vscode/launch.json`, `.vscode/tasks.json`
- Modify: `.zed/settings.json` (add JSON5 association)
- Modify: `.zed/tasks.json` (add spec validation task)

### Tasks

#### G0.1: Add Python dependencies

**Step 1:** Edit `backend/pyproject.toml` to add dependencies

```toml
# In [project.dependencies] (uv format — this project does NOT use Poetry):
json5 = ">=0.14.0"

# In [project.optional-dependencies] or dev group:
approvaltests = "*"
pytest-approvaltests = "*"
```

> **Note:** This project uses `uv`, not Poetry. Use `[project.dependencies]` and `[project.optional-dependencies]` / dependency groups, NOT `[tool.poetry.dependencies]`.

**Step 2:** Install

```bash
cd backend && uv sync
```

**Step 3:** Verify imports work

```bash
uv run python -c "import json5; print(json5.__version__)"
uv run python -c "from approvaltests import verify; print('approvaltests OK')"
```

#### G0.2: Create VS Code config files

Create `.vscode/extensions.json`, `.vscode/settings.json`, `.vscode/launch.json`, `.vscode/tasks.json` per the spec document "Editor Configuration Review" section.

#### G0.3: Update Zed config

Add JSON5 language association to `.zed/settings.json` and spec validation task to `.zed/tasks.json`.

#### G0.4: Implement feature flag framework

**Purpose:** Refactor `FeatureConfig` into a structured, enforceable flag system with automated hygiene.

**Files:**
- Create: `backend/app/settings/providers/features/_base.py` (FeatureFlag, FlagMeta, FlagLifecycle)
- Create: `backend/app/settings/providers/features/runtime.py` (RuntimeFlags — permanent toggles)
- Create: `backend/app/settings/providers/features/fieldspec.py` (FieldSpecFlags — transitional gate flags)
- Create: `backend/app/settings/providers/features/__init__.py` (AllFeatures registry)
- Modify: `backend/app/settings/settings.py` (wire AllFeatures, add FEATURE_FIELDSPEC_* env vars)
- Modify: `backend/app/settings/providers/__init__.py` (export AllFeatures instead of FeatureConfig)
- Modify: `backend/app/settings/contracts.py` (ProvidesFeatureConfig → returns AllFeatures)
- Modify: `backend/app/routers/config_router.py` (FeatureFlagsResponse includes fieldspec flags)
- Keep: `backend/app/settings/providers/feature_config.py` (deprecated, remove in G10)

**Test files:**
- Create: `backend/tests/unit/settings/test_feature_flag_framework.py`
- Create: `backend/tests/unit/settings/test_feature_flag_hygiene.py`
- Create: `backend/tests/unit/settings/test_feature_flag_lifecycle.py`

**Framework architecture:**

```
app/settings/providers/features/
├── _base.py          # FeatureFlag, FlagMeta, FlagLifecycle
├── runtime.py        # permanent toggles (simulation, demo, debug)
├── fieldspec.py      # transitional: one flag per gate (G4–G9)
└── __init__.py       # AllFeatures registry + all_transitional()
```

**Transitional flags for this plan:**

| Flag | Env var | Default | Gate | Meaning |
|------|---------|---------|------|---------|
| `fieldspec.persistence` | `FEATURE_FIELDSPEC_PERSISTENCE` | false | G4 | region_field_specs table + repo |
| `fieldspec.service` | `FEATURE_FIELDSPEC_SERVICE` | false | G5-G6 | FieldSpecService wired, specs load at startup |
| `fieldspec.matching` | `FEATURE_FIELDSPEC_MATCHING` | false | G7 | MatchingService uses spec-driven weights |
| `fieldspec.voter_list` | `FEATURE_FIELDSPEC_VOTER_LIST` | false | G8 | VoterListService uses spec for parsing |
| `fieldspec.api` | `FEATURE_FIELDSPEC_API` | false | G9 | Region selector API + campaign region |

**Usage pattern in code (each gate adds an if/else):**

```python
if settings.features.fieldspec.matching.enabled:
    score = spec_driven_matching(spec, ocr, voter_data)
else:
    score = hardcoded_matching(ocr_name, ocr_address, voter_name, voter_address)
```

**Automated hygiene (3 CI checks):**

| Check | Detects | Enforcement |
|-------|---------|-------------|
| `test_no_dead_transitional_flags` | Flag defined but no code references `.enabled` | Fail CI: remove the flag |
| `test_no_ossified_transitional_flags` | Flag checked but no `else` branch | Fail CI: add fallback or remove flag |
| `test_domain_files_match_registry` | File on disk but not in AllFeatures, or vice versa | Fail CI: sync registry |

**Testing strategy for the framework (reusable for future domains):**

| Test file | What it covers | When to extend |
|-----------|---------------|----------------|
| `test_feature_flag_framework.py` | Base types, domain models, registry | When adding a new domain or flag |
| `test_feature_flag_hygiene.py` | Dead/ossified/orphan detection | Runs on every CI — no extension needed |
| `test_feature_flag_lifecycle.py` | Full add→use→cleanup simulation | Reference for how to add a new domain |

Adding a new domain (future features):
1. Create `app/settings/providers/features/newdomain.py` with `NewDomainFlags(BaseModel)`
2. Add `NewDomain` field to `AllFeatures` in `__init__.py`
3. Update `test_domain_files_match_registry` expected set
4. The hygiene test automatically picks up new transitional flags

**G10 cleanup for this plan:**
1. Delete `fieldspec.py` and `feature_config.py`
2. Remove `fieldspec` from `AllFeatures`
3. Remove all `if/else` branches, keeping only spec-driven paths
4. Hygiene test confirms zero transitional flags remain

#### G0.5: Create ADR-0007 — Feature flag lifecycle framework

**File:** `docs/architecture/decisions/0007-feature-flag-lifecycle-framework.md`

Document the decision to use transitional vs permanent feature flags with automated CI hygiene. Covers:
- Two flag lifecycles (`permanent` for runtime toggles, `transitional` for gate-scoped rollout)
- The `if/else` integration guard pattern
- Automated hygiene checks (dead flags, ossified flags, registry/file sync)
- G10 cleanup lifecycle (flags deleted after feature ships)

Update ADR index: `docs/architecture/decisions/README.md` — add row for ADR-0007.

### G0 Exit Checks

- [ ] `uv run python -c "import json5"` succeeds
- [ ] `uv run python -c "from approvaltests import verify"` succeeds
- [ ] `.vscode/` files created and valid JSON
- [ ] `.zed/settings.json` includes JSON5 config
- [ ] `uv run pytest tests/ -v` still passes (no regressions)
- [ ] `uv run pytest tests/unit/settings/test_feature_flag_framework.py -v` — all framework tests pass
- [ ] `uv run pytest tests/unit/settings/test_feature_flag_hygiene.py -v` — hygiene checks pass (fieldspec flags dead initially, which is expected — no code references yet)
- [ ] `uv run pytest tests/unit/settings/test_feature_flag_lifecycle.py -v` — lifecycle tests pass
- [ ] `GET /config/features` returns fieldspec flags in response
- [ ] `uv run ruff check app/ tests/` clean
- [ ] ADR-0007 committed to `docs/architecture/decisions/`
- [ ] ADR index in `docs/architecture/decisions/README.md` updated
- [ ] Commit: `chore(field-spec): add dependencies and editor config`

---

## G1: Domain Value Objects

**Purpose:** Create the core domain types. Zero infrastructure dependencies. Pure Pydantic models.

**Load skills:** `bunx openskills read tdd python-core python-type-checking`

**Files:**
- Create: `backend/app/domain/field_spec.py`
- Modify: `backend/app/domain/__init__.py` (export new types)
- Create: `backend/tests/unit/domain/test_field_spec.py`

**Reference:** `plans/configurable-field-specs.md` → "Domain Layer" section

### Tasks

#### G1.1: RED — Write failing test for BallotField

**File:** `backend/tests/unit/domain/test_field_spec.py`

```python
class TestBallotField:
    def test_create_ballot_field(self):
        from app.domain.field_spec import BallotField
        f = BallotField(
            id="name",
            label="Full Name",
            field_type="text",
            required_for_matching=True,
            match_weight=1.0,
        )
        assert f.id == "name"
        assert f.match_weight == 1.0

    def test_ballot_field_is_frozen(self):
        from app.domain.field_spec import BallotField
        f = BallotField(id="name", label="Name", field_type="text", required_for_matching=True)
        from pydantic import ValidationError
        try:
            f.id = "changed"
            assert False, "Should be frozen"
        except ValidationError:
            pass

    def test_match_weight_must_be_non_negative(self):
        from app.domain.field_spec import BallotField
        from pydantic import ValidationError
        try:
            BallotField(id="x", label="X", field_type="text", required_for_matching=True, match_weight=-1.0)
            assert False, "Should reject negative weight"
        except ValidationError:
            pass
```

**Verify RED:** `cd backend && uv run pytest tests/unit/domain/test_field_spec.py -v` → FAIL (import error)

#### G1.2: GREEN — Implement BallotField

**File:** `backend/app/domain/field_spec.py`

Create the `BallotField` class per spec (Pydantic BaseModel, frozen=True).

**Verify GREEN:** `uv run pytest tests/unit/domain/test_field_spec.py::TestBallotField -v` → PASS

#### G1.3: RED — Write failing tests for VoterRegField

Add `TestVoterRegField` class to the test file.

**Verify RED:** `uv run pytest tests/unit/domain/test_field_spec.py::TestVoterRegField -v` → FAIL

#### G1.4: GREEN — Implement VoterRegField

**Verify GREEN:** Tests pass.

#### G1.5: RED — Write failing tests for FieldMapping, CropConfig

Add `TestFieldMapping`, `TestCropConfig` classes.

**Verify RED:** Tests fail.

#### G1.6: GREEN — Implement FieldMapping, CropConfig

**Verify GREEN:** Tests pass.

#### G1.7: RED — Write failing tests for RegionFieldSpecConfig

Add `TestRegionFieldSpecConfig` with tests for:
- `create_full_spec`
- `get_mapping_for_existing_field` / `get_mapping_for_missing_field_returns_none`
- `matchable_fields_excludes_zero_weight`
- `total_match_weight`
- `validate_integrity` (at least 3-4 validation rules)

**Verify RED:** Tests fail.

#### G1.8: GREEN — Implement RegionFieldSpecConfig

Implement the aggregate root with domain queries (`get_mapping_for`, `matchable_fields`, `total_match_weight`) and `validate_integrity()`.

**Verify GREEN:** All `TestRegionFieldSpecConfig` tests pass.

#### G1.9: REFACTOR — Clean up domain module

- Export types from `app/domain/__init__.py`
- Check for any extracted helpers needed

**Verify:** All tests still pass.

#### G1.10: Create ADR-0006 — Spec-driven field configuration

**File:** `docs/architecture/decisions/0006-spec-driven-field-configuration.md`

Document the architectural decision to replace hardcoded region field handling with a spec-driven system loaded from JSON5 source files. Covers:
- Why JSON5 source files over per-region Alembic migrations (specs are config, not user data; PR-reviewable, diffable)
- Hexagonal outside-in architecture: domain → services → adapters dependency direction
- DDD aggregate root (`RegionFieldSpecConfig`) and value objects
- Why pure Pydantic domain layer with zero infrastructure imports

Update ADR index: `docs/architecture/decisions/README.md` — add row for ADR-0006.

### G1 Exit Checks

- [ ] `uv run pytest tests/unit/domain/test_field_spec.py -v` — all pass
- [ ] No imports from `app/data`, `app/services`, `app/routers` in `app/domain/field_spec.py`
- [ ] `uv run ruff check app/domain/field_spec.py` clean
- [ ] `uv run basedpyright app/domain/field_spec.py` clean
- [ ] ADR-0006 committed to `docs/architecture/decisions/`
- [ ] ADR index in `docs/architecture/decisions/README.md` updated
- [ ] Commit: `feat(field-spec): G1 domain value objects`

---

## G2: Template Renderer

**Purpose:** Implement the pure `render_template` function that combines voter data into ballot field values.

**Load skills:** `bunx openskills read tdd python-pytest python-core`

**Files:**
- Modify: `backend/app/domain/field_spec.py` (add `render_template`, `_extract_placeholders`)
- Create: `backend/tests/unit/domain/test_template_renderer.py`
- Create: `backend/tests/unit/domain/test_template_renderer_approval.py`

**Reference:** `plans/configurable-field-specs.md` → "Domain Service" and "BDD Test Scenarios" sections

### Tasks

#### G2.1: RED — Write failing BDD tests for render_template

**File:** `backend/tests/unit/domain/test_template_renderer.py`

Write ONE test at a time (vertical slice):

1. `test_concatenates_fields` — simple name template
2. `test_drops_empty_placeholder` — empty middle name
3. `test_address_without_apartment` — "Apt" label dropped when empty
4. `test_address_with_apartment` — apartment included
5. `test_empty_template_returns_empty`
6. `test_all_fields_empty_returns_empty`
7. `test_single_field` — ward template
8. `test_missing_field_treated_as_empty`
9. `test_collapses_multiple_spaces`
10. `test_handles_special_characters`
11. `test_na_values_treated_as_empty` — `"N/A"` values in voter data are treated as empty strings and dropped (DC voter rolls use `"N/A"` for missing street numbers, etc.)

**Sentinel value convention:** `render_template` should treat `"N/A"` (case-insensitive, after stripping whitespace) as equivalent to empty. This avoids `"N/A"` appearing in rendered ballot fields like addresses. Define a set of sentinel values: `{"N/A", "NA", "n/a", "na"}` — any placeholder value matching these after `strip().upper()` is replaced with `""`.

**Process:** Write test 1 → verify RED → implement → verify GREEN → write test 2 → repeat.

#### G2.2: GREEN — Implement render_template and _extract_placeholders

After each RED test, write minimal code to pass. Build up incrementally.

**Reference implementation** in spec document under "Domain Service" section.

#### G2.3: RED — Write approval tests

**File:** `backend/tests/unit/domain/test_template_renderer_approval.py`

Write:
- `test_dc_address_variants` — golden master for DC address patterns
- `test_dc_name_variants` — golden master for DC name patterns
- `test_dc_full_ballot_mapping` — end-to-end voter → ballot

**First run:** Creates `.received.` files → inspect → approve by renaming to `.approved.`

#### G2.4: REFACTOR — Clean up renderer

- Check edge case handling
- Ensure no regex over-matching

#### G2.5: Create ADR-0008 — Template-based field rendering

**File:** `docs/architecture/decisions/0008-template-based-field-rendering.md`

Document the decision to use string templates for composing ballot fields from voter registration fields. Covers:
- Why templates over code-based composition (declarative, spec-defined, no per-region logic)
- Sentinel value convention (`N/A` treated as empty)
- The `_extract_placeholders` pure function approach
- Why co-located in domain layer (no infrastructure dependency)

Update ADR index: `docs/architecture/decisions/README.md` — add row for ADR-0008.

#### G2.6: Add approval testing how-to to development docs

**File:** `docs/development/testing.md` (create if not exists, or add section)

Add a Diátaxis *How-To* section covering approval testing in this project:
- When to use approval tests vs assertion tests (reference the table in `configurable-field-specs.md`)
- The `.received.` → `.approved.` workflow
- How to run approval tests: `pytest --approvaltests-use-reporter='PythonNativeReporter'`
- Where approved files live (alongside test files, committed to git)
- How to re-approve after intentional changes

### G2 Exit Checks

- [ ] `uv run pytest tests/unit/domain/test_template_renderer.py -v` — all pass
- [ ] `uv run pytest tests/unit/domain/test_template_renderer_approval.py -v` — all pass
- [ ] `.approved.txt` files committed for approval tests
- [ ] `render_template` is a pure function (no I/O, no side effects)
- [ ] `uv run ruff check app/domain/field_spec.py` clean
- [ ] ADR-0008 committed to `docs/architecture/decisions/`
- [ ] ADR index updated
- [ ] Approval testing how-to committed to `docs/development/testing.md`
- [ ] Commit: `feat(field-spec): G2 template renderer`

---

## G3: DC Spec Source File

**Purpose:** Create the DC JSON5 spec file and its approval test snapshot.

**Load skills:** `bunx openskills read python-core tdd`

**Files:**
- Create: `backend/app/regions/dc.json5`
- Create: `backend/app/regions/README.md`
- Create: `backend/tests/unit/domain/test_dc_spec_approval.py`

### Tasks

#### G3.1: Create DC spec file

**File:** `backend/app/regions/dc.json5`

Copy the DC Default Spec JSON from the spec document. Use JSON5 features (comments, trailing commas).

#### G3.2: RED — Write approval test for DC spec snapshot

**File:** `backend/tests/unit/domain/test_dc_spec_approval.py`

```python
class TestDcDefaultSpecApproval:
    def test_dc_seed_spec(self):
        from app.domain.field_spec import RegionFieldSpecConfig
        import json5
        from pathlib import Path
        spec_path = Path(__file__).resolve().parents[3] / "app" / "regions" / "dc.json5"
        assert spec_path.exists(), f"Spec file not found at {spec_path}"
        raw = spec_path.read_text()
        data = json5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)
        verify(spec.model_dump_json(indent=2))
```

> **Note:** Using `.resolve().parents[3]` with an existence check instead of 4 chained `.parent` calls. If test dir structure changes, the assertion gives a clear error.

**First run:** Creates `.received.json` → inspect → approve.

#### G3.3: Verify spec passes validation

```python
def test_dc_spec_passes_integrity_validation(self):
    # load dc.json5 → validate → assert no errors
```

#### G3.4: Create regions README

Brief: how to add a new region spec (copy from spec document).

#### G3.5: Create JSON5 spec schema reference doc

**File:** `docs/development/field-spec-schema.md` (new)

Diátaxis *Reference* document for the JSON5 regional spec file format. Covers:
- Top-level fields: `region_name`, `country_code`, `ballot_fields`, `voter_reg_fields`, `field_mappings`, `hash_fields`, `crop_config`
- `ballot_fields` schema: `id`, `label`, `field_type` (text|address|integer|date), `required_for_matching`, `match_weight`
- `voter_reg_fields` schema: `id`, `csv_column_name`, `data_type`, `category` (name|address|registration|geography)
- `field_mappings` schema: `ballot_field_id`, `template` (placeholder syntax `{field_id}`)
- `crop_config` schema: `top_crop`, `bottom_crop`, `base_threshold`
- Validation rules enforced by `validate_integrity()` (9 rules)
- Example: minimal valid spec
- Region key convention: filename stem → uppercase in DB (`dc.json5` → `"DC"`)

### G3 Exit Checks

- [ ] `uv run pytest tests/unit/domain/test_dc_spec_approval.py -v` — all pass
- [ ] `.approved.json` file committed
- [ ] DC spec passes `validate_integrity()` with zero errors
- [ ] `backend/app/regions/dc.json5` is valid JSON5 (comments + trailing commas)
- [ ] `docs/development/field-spec-schema.md` committed — JSON5 schema reference
- [ ] Commit: `feat(field-spec): G3 DC region spec source file`

---

## G4: Persistence Layer

**Purpose:** Create the DB model, Protocol contract, and repository implementation.

**Load skills:** `bunx openskills read tdd python-pytest architecture-patterns`

**Files:**
- Create: `backend/app/data/database/model/region_field_spec.py`
- Modify: `backend/app/persistence/contracts.py` (add `FieldSpecRepository` Protocol)
- Create: `backend/app/repositories/field_spec_repo.py`
- Create: `backend/tests/unit/repositories/test_field_spec_repo.py`
- Modify: `backend/app/persistence/engines/model_imports.py` (add `RegionFieldSpecModel` import for Alembic discovery) — [#17]
- Modify: `backend/app/data/models.py` (add import + `__all__` entry for `RegionFieldSpecModel`) — [#17]
- Create: Alembic migration

**Reference:** `plans/configurable-field-specs.md` → "Repository Implementation" and "DB Model" sections

### Tasks

#### G4.1: RED — Write failing repository tests

**File:** `backend/tests/unit/repositories/test_field_spec_repo.py`

Use in-memory SQLite. Tests:
1. `test_save_and_find_by_region` — round-trip
2. `test_find_returns_none_for_unknown_region` — not found case
3. `test_save_updates_existing` — upsert behavior
4. `test_delete_removes_spec`
5. `test_delete_returns_false_for_missing`
6. `test_round_trip_preserves_all_fields` — domain fidelity

**Process:** Write test 1 → RED → implement → GREEN → test 2 → repeat.

#### G4.2: GREEN — Implement DB model

**File:** `backend/app/data/database/model/region_field_spec.py`

`RegionFieldSpecModel(SQLModel, table=True)` per spec — JSON columns for `ballot_fields`, `voter_reg_fields`, etc.

#### G4.3: GREEN — Add Protocol contract

**File:** `backend/app/persistence/contracts.py`

Add `FieldSpecRepository` Protocol:

```python
@runtime_checkable
class FieldSpecRepository(Protocol):
    def find_by_region(self, region_id: UUID) -> RegionFieldSpecConfig | None: ...
    def find_by_region_key(self, region_key: str) -> RegionFieldSpecConfig | None: ...
    def save(self, spec: RegionFieldSpecConfig, region_id: UUID) -> RegionFieldSpecConfig: ...
    def upsert(self, region_key: str, spec: RegionFieldSpecConfig) -> None: ...
    def delete(self, region_id: UUID) -> bool: ...
    def list_regions(self) -> list[tuple[str, str, UUID]]: ...  # (key, name, id) — needed by G9 GET /regions
```

> **Note:** `RegionFieldSpecModel.name` is a DB column not present on the domain model. During `upsert`, derive the name from the spec file (e.g., `"DC Default"` from region_key). Add a `name` parameter to `upsert` or derive it conventionally.

#### G4.4: GREEN — Implement repository

**File:** `backend/app/repositories/field_spec_repo.py`

Implement `FieldSpecRepositoryImpl` with `_to_domain()` and `_to_model()` mapping functions.

#### G4.5: GREEN — Register model with Alembic and create migration

**File:** `backend/app/persistence/engines/model_imports.py`, `backend/app/data/models.py`

Alembic autogenerate only discovers models that are imported in `model_imports.py` and registered in `data/models.py`. Add `RegionFieldSpecModel` to both:

```python
# model_imports.py — add import
from app.data.database.model.region_field_spec import RegionFieldSpecModel

# data/models.py — add import and __all__ entry
from app.data.database.model.region_field_spec import RegionFieldSpecModel
# Add "RegionFieldSpecModel" to __all__ list
```

Then generate migration:

```bash
cd backend && uv run alembic revision --autogenerate -m "add region_field_specs table"
```

Verify migration creates `region_field_specs` table with correct columns.

#### G4.6: REFACTOR — Clean up mappers

If `_to_domain` / `_to_model` are complex, extract to separate mapper module.

### G4 Exit Checks

- [ ] `uv run pytest tests/unit/repositories/test_field_spec_repo.py -v` — all pass
- [ ] `FieldSpecRepository` Protocol defined in `contracts.py`
- [ ] Repository imports only from `app/domain` and `app/data` (no service imports)
- [ ] `RegionFieldSpecModel` registered in `model_imports.py` and `data/models.py` — [#17]
- [ ] Migration creates table successfully: `uv run alembic upgrade head`
- [ ] All existing tests still pass
- [ ] Flip flag: `FEATURE_FIELDSPEC_PERSISTENCE=true` in env config
- [ ] Hygiene test passes: flag is referenced in `startup.py` with else branch
- [ ] Commit: `feat(field-spec): G4 persistence layer`

---

## G5: Application Service

**Purpose:** Implement the `FieldSpecService` use-case orchestrator.

**Load skills:** `bunx openskills read tdd python-pytest architecture-patterns`

**Files:**
- Create: `backend/app/services/field_spec_service.py`
- Create: `backend/tests/unit/services/test_field_spec_service.py`
- Modify: `backend/app/domain/field_spec.py` (add `FieldSpecNotFoundError`)

### Tasks

#### G5.1: RED — Write failing service tests

**File:** `backend/tests/unit/services/test_field_spec_service.py`

Use mock repository (Protocol-based). Tests:
1. `test_get_spec_returns_spec` — happy path
2. `test_get_spec_raises_when_not_found` — `FieldSpecNotFoundError`
3. `test_map_voter_to_ballot` — uses `render_template` via spec
4. `test_map_voter_to_ballot_partial_data` — missing fields treated as empty
5. `test_validate_good_spec` — returns empty errors
6. `test_validate_spec_with_bad_references` — returns errors
7. `test_validate_spec_empty_ballot_fields` — returns error

**Process:** Vertical slice — one test → RED → GREEN → next.

#### G5.2: GREEN — Implement FieldSpecService

**File:** `backend/app/services/field_spec_service.py`

Per spec: depends on `FieldSpecRepository` Protocol only. Methods: `get_spec`, `map_voter_to_ballot`, `validate_spec`.

#### G5.3: GREEN — Add FieldSpecNotFoundError

**File:** `backend/app/domain/field_spec.py`

```python
class FieldSpecNotFoundError(Exception):
    def __init__(self, region_id: UUID):
        self.region_id = region_id
        super().__init__(f"Field spec not found for region: {region_id}")
```

#### G5.4: REFACTOR — Review service boundaries

- If `map_voter_to_ballot` grows, consider extracting
- Ensure no infrastructure leaking into service

### G5 Exit Checks

- [ ] `uv run pytest tests/unit/services/test_field_spec_service.py -v` — all pass
- [ ] Service imports only from `app/domain` and `app/persistence/contracts`
- [ ] No mock of domain objects — only repository is mocked
- [ ] All existing tests still pass
- [ ] Commit: `feat(field-spec): G5 application service`

---

## G6: Spec Loading & Startup Integration

**Purpose:** Load JSON5 spec files into DB at app startup.

**Load skills:** `bunx openskills read tdd python-pytest architecture-patterns uv-package-manager`

**Files:**
- Modify: `backend/app/services/field_spec_service.py` (add `load_all_specs`)
- Create: `backend/tests/unit/services/test_field_spec_loading.py`
- Modify: `backend/app/startup.py` (add spec loader call)

### Tasks

#### G6.1: RED — Write failing loading tests

**File:** `backend/tests/unit/services/test_field_spec_loading.py`

Tests:
1. `test_load_valid_spec` — parse dc.json5 → upsert to mock repo
2. `test_load_invalid_schema_reports_error` — malformed JSON5
3. `test_load_invalid_integrity_reports_error` — valid JSON but bad references
4. `test_upsert_updates_existing_spec` — reload updates
5. `test_load_all_specs` — multiple files
6. `test_missing_regions_dir` — graceful, not error
7. `test_all_source_specs_valid` — smoke test all .json5 files

#### G6.2: GREEN — Implement load_all_specs

Add `load_all_specs()` method to `FieldSpecService`. Uses `json5.loads()` → `model_validate` → `validate_integrity()` → `repo.upsert()`.

#### G6.3: GREEN — Wire into startup

Modify `app/startup.py` to call `FieldSpecService.load_all_specs()` after DB init.

**Error handling decision (fail-fast):** If `load_all_specs` returns any errors, log them and raise an exception to prevent app from starting with invalid specs. This avoids silent failures where matching breaks because no spec loaded.

```python
async def startup(self) -> None:
    self._db_initializer()
    self._spec_loader()          # <-- new: load regional specs (fail-fast on error)
    self._config_validator()
    self._worker_task = asyncio.create_task(self._worker_starter())
```

The `ApplicationStartup.__init__` gains a new optional parameter:
```python
spec_loader: Callable[[], tuple[int, list[str]]] = default_spec_loader,
```

#### G6.4: Verify — All source specs load

```bash
cd backend && uv run python -c "
from app.services.field_spec_service import FieldSpecService
# ... exercise load_all_specs and verify zero errors
"
```

#### G6.5: GREEN — Wire FieldSpecService into FastAPI DI

**File:** `backend/app/dependencies.py`

Add dependency providers so downstream services can receive `FieldSpecService` via injection:

```python
def get_field_spec_service() -> Generator[FieldSpecService]:
    session = next(get_session())
    repo = FieldSpecRepositoryImpl(session)
    yield FieldSpecService(repo)
```

Also add a `conftest.py` for approval tests if not already present:

**File:** `backend/tests/conftest.py` (or `backend/tests/unit/conftest.py`)

```python
from approvaltests import set_default_reporter
from approvaltests.reporters.python_native_reporter import PythonNativeReporter

def pytest_configure(config):
    set_default_reporter(PythonNativeReporter())
```

#### G6.7: GREEN — region_key normalization convention

**Convention:** All region keys are stored as **uppercase** in both the filesystem and the database:

- Filenames: `dc.json5`, `md.json5` (lowercase on disk, standard convention)
- `region_key` in DB: `"DC"`, `"MD"` (uppercase — `spec_file.stem.upper()`)
- `Region.region_key` in existing DB: must already be uppercase. If not, add a startup assertion.

`load_all_specs` derives `region_key` via `spec_file.stem.upper()`. The `find_by_region_key` query must normalize input the same way. Add a test:

```python
def test_region_key_case_insensitive_lookup(self):
    """find_by_region_key normalizes to uppercase."""
    # load spec via load_all_specs (stems uppercased)
    # find_by_region_key("dc") should match "DC"
```

#### G6.8: GREEN — Auto-create Region rows during spec loading — [#16]

**Problem:** `load_all_specs` calls `repo.upsert(region_key, spec)`, which inserts `RegionFieldSpecModel` with FK to `regions.id`. If no `Region` row exists for that `region_key`, the FK constraint fails. Currently `_ensure_default_region()` creates DC on demand during campaign creation, but spec loading runs at startup before any campaign exists.

**Fix:** Add `region_name` and `country_code` fields to the JSON5 spec file (or derive from convention). In `upsert()`, check if a `Region` row exists for the `region_key`. If not, create one:

```python
# In repository upsert or a helper in FieldSpecService:
def _ensure_region_exists(self, region_key: str, region_name: str, country_code: str = "US") -> UUID:
    """Create Region row if it doesn't exist, return its ID."""
    existing = self._session.exec(select(Region).where(Region.region_key == region_key)).first()
    if existing:
        return existing.id
    region = Region(region_key=region_key, region_name=region_name, country_code=country_code)
    self._session.add(region)
    self._session.commit()
    return region.id
```

Add to JSON5 spec (top-level):
```json5
{
  region_name: "District of Columbia",  // NEW — used to create Region row
  country_code: "US",                   // NEW — used to create Region row
  ballot_fields: [...],
  ...
}
```

Tests:
1. `test_load_spec_creates_region_if_missing` — spec loading creates `Region` row
2. `test_load_spec_uses_existing_region` — no duplicate if `Region` already exists
3. `test_region_name_from_spec` — `Region.region_name` matches spec

> **Note (#9):** Existing test fixtures with lowercase `region_key="dc"` (e.g., `tests/unit/repositories/test_repositories.py:30`) should be updated to uppercase `"DC"` as part of G6.7 normalization. Add a startup assertion validating all `Region.region_key` values are uppercase.

### G6 Exit Checks

- [ ] `uv run pytest tests/unit/services/test_field_spec_loading.py -v` — all pass
- [ ] App startup loads DC spec without errors
- [ ] Startup fails fast (raises) if any spec has validation errors
- [ ] `get_field_spec_service` dependency provider registered in `dependencies.py`
- [ ] Approval test reporter configured in `conftest.py`
- [ ] region_key normalization convention documented and tested
- [ ] `Region` rows auto-created during spec loading (no FK failures) — [#16]
- [ ] JSON5 spec files include `region_name` and `country_code` — [#16]
- [ ] Existing test fixtures updated to use uppercase `region_key` — [#9]
- [ ] `uv run pytest tests/ -v` — all pass (no regressions)
- [ ] Flip flag: `FEATURE_FIELDSPEC_SERVICE=true` in env config
- [ ] Hygiene test passes: flag referenced in startup.py spec loading gate
- [ ] Commit: `feat(field-spec): G6 spec loading and startup integration`

---

## G7: Matching Service Refactor

**Purpose:** Replace hardcoded field keys in `MatchingService` with spec-driven matching.

**⚠️ CRITICAL:** Write approval baseline BEFORE refactoring. This is a characterization test.

**Files:**
- Create: `backend/tests/unit/services/test_matching_regression_approval.py` (baseline FIRST)
- Create: `backend/app/matching/voter_data_adapter.py` (new — flattens voter blobs for templates)
- Modify: `backend/app/matching/matching_service.py`
- Modify: `backend/app/jobs/worker.py` (consolidate duplicate matching logic) — [#24]
- Extend: `backend/tests/unit/services/test_matching_service.py`

### Pre-requisite Understanding

`RegisteredVoter` stores data as nested JSON blobs: `name_data`, `address_data`, `other_field_data`. But `render_template` expects a flat `dict[str, str]` keyed by `voter_reg_field.id` (e.g., `first_name`, `street_number`). This adapter is needed before MatchingService can use `render_template`.

### Tasks

#### G7.0: RED/GREEN — Voter data adapter

**File:** `backend/app/matching/voter_data_adapter.py`

Create a pure function that flattens `RegisteredVoter` JSON blobs into a single dict keyed by `voter_reg_field.id`:

```python
def flatten_voter_data(
    voter: RegisteredVoter,
    voter_reg_fields: list[VoterRegField],
) -> dict[str, str]:
    """Flatten nested voter JSON blobs into a flat dict for render_template.

    Maps voter_reg_field.csv_column_name → voter_reg_field.id using
    the category to determine which blob to read from.
    """
```

Tests:
1. `test_flatten_name_fields` — name_data keys mapped to voter_reg_field IDs
2. `test_flatten_address_fields` — address_data keys mapped
3. `test_flatten_missing_blob_returns_empty_strings` — graceful on None blobs
4. `test_flatten_preserves_all_categories` — registration + geography too

#### G7.1: RED — Capture baseline with approval test

**File:** `backend/tests/unit/services/test_matching_regression_approval.py`

Write `test_dc_matching_score_matrix` using CURRENT hardcoded `MatchingService`. Run → approve `.received.txt` as baseline.

**This is a characterization test** — captures current behavior before change.

#### G7.2: RED — Write failing tests for new spec-driven behavior

**File:** Extend `backend/tests/unit/services/test_matching_service.py`

Tests:
1. `test_similarity_uses_spec_weights` — dynamic weights replace hardcoded
2. `test_builds_voter_name_from_spec` — uses `render_template`
3. `test_builds_voter_address_from_spec` — uses `render_template`
4. `test_ward_has_reduced_weight` — weight 0.3 per spec

#### G7.3: GREEN — Refactor MatchingService to accept spec

Modify `MatchingService.calculate_similarity` to accept `RegionFieldSpecConfig` and use spec-driven field weights and `render_template` output.

**`field_scores` evolution:** Currently `field_scores` is hardcoded as `{"name": score, "address": score}`. After refactor, `field_scores` should be a dict keyed by `ballot_field.id` for all `matchable_fields()`, enabling dynamic field counts. Update `match_ocr_result` and `MatchResult.field_scores` accordingly. This is a schema change for match results — ensure the approval test captures it.

#### G7.3a: RED/GREEN — Make zipcode pre-filter configurable — [#20]

**Problem:** `matching_service.py:83` hardcodes `col(RegisteredVoter.address_data)["zip"].as_string()` for zipcode pre-filtering. After spec refactor, the key is `zip_code` not `zip`, and the field may differ per region.

**Fix options:**
- **(a) Recommended:** Add a `pre_filter_field` (or `zip_filter_field_id`) to `RegionFieldSpecConfig` specifying which field to use for pre-filtering. Default: first address-category field marked for pre-filtering.
- **(b) Simpler:** Remove zipcode pre-filter entirely, rely on region-only filtering.

Tests:
1. `test_pre_filter_uses_spec_field_id` — filter uses spec-configured field
2. `test_pre_filter_with_no_configured_field` — graceful fallback (no pre-filter)

#### G7.4: Verify — Approval test comparison

Run `test_dc_matching_score_matrix` again. If scores changed:
- Review diff carefully
- If intentional (better scoring) → approve new baseline
- If unintentional → fix regression

#### G7.5: REFACTOR — Clean up

- Remove hardcoded field key references
- Remove old name/address extraction methods if superseded

#### G7.6: NOTE — `RegisteredVoter.full_name`/`is_matchable()` hardcode field keys — [#18]

**Location:** `app/domain/voter.py:21-32`

`full_name` hardcodes `name_data.get("first_name")`, `middle_name`, `last_name`. `is_matchable()` hardcodes `name_data.get("last_name")`. These are domain-layer methods used in tests and `__repr__`.

**Decision:** These remain simplified defaults for display/logging. They do NOT need to be spec-driven for this phase. Document this decision with a comment in code. If a future phase needs spec-aware display names, that's a separate refactor.

Update existing tests in `tests/unit/domain/test_domain.py:205-243` to document that these use default keys, not spec keys.

#### G7.7: RED/GREEN — Consolidate `worker.py` duplicate matching into `MatchingService` — [#24]

**Problem:** `app/jobs/worker.py:950-963` contains inline matching logic using old key schema (`street`, `city`, `state`, `zip`). This is a third variant that will silently break after spec refactor changes voter blob keys.

**Evidence of 3 conflicting key schemas:**

| Code path | Address keys | File |
|-----------|-------------|------|
| `VoterListService.merge_voter_list()` | `street`, `city`, `state`, `zip` | `voter_list_service.py:104-109` |
| `MatchingService._build_voter_address()` | `street_number`, `street_name`, `street_type`, `street_dir_suffix` | `matching_service.py:274-280` |
| `worker.py` inline matching | `street`, `city`, `state`, `zip` | `worker.py:958-961` |

**Fix:** Refactor `worker.py:950-963` to call `MatchingService.match_ocr_result()` instead of reimplementing matching inline. The worker should construct the needed inputs and delegate to the service.

Tests:
1. `test_worker_uses_matching_service` — verify worker delegates to `MatchingService` (integration test or mock verification)
2. `test_worker_matching_results_match_service` — results are identical whether called from worker or directly

#### G7.8: Create matching process explanation doc

**File:** `docs/architecture/matching-process.md` (new)

Diátaxis *Explanation* document describing how spec-driven matching works end-to-end. Covers:
- The matching pipeline: OCR result → voter data adapter → `render_template` → weighted field scoring → confidence assignment
- How `RegionFieldSpecConfig` drives dynamic field weights and field count
- The `field_scores` dict shape (keyed by `ballot_field.id`, not hardcoded `name`/`address`)
- Pre-filtering (zipcode or spec-configured field)
- The voter data adapter: flattening nested JSON blobs (`name_data`, `address_data`, `other_field_data`) into a flat dict keyed by `voter_reg_field.id`
- Why approval tests guard the score matrix (characterization testing pattern)

#### G7.9: Update C4 components diagram

**File:** `docs/architecture/c4-components.md`

Update the C4 Level 3 diagram to reflect new components added by this feature:

**Add to Service Layer:**
- `FieldSpecService` in `services/field_spec_service.py` — field spec use cases + spec loading

**Add to Matching Module:**
- `VoterDataAdapter` in `matching/voter_data_adapter.py` — flattens voter JSON blobs for templates

**Add to Data Layer:**
- `FieldSpecRepo` in `repositories/field_spec_repo.py` — field spec persistence

**Add a new subgraph for Domain Layer:**
```
subgraph Domain Layer
    FieldSpec[field_spec.py]
    TemplateRenderer[render_template]
end
```

**Add a new subgraph for Regional Config:**
```
subgraph Regional Config
    DCSpec[dc.json5]
    RegionsDir[app/regions/]
end
```

**Add edges:**
- `FieldSpecService --> FieldSpecRepo`
- `MatchingService --> FieldSpecService`
- `MatchingService --> VoterDataAdapter`
- `VoterDataAdapter --> FieldSpec` (domain)
- `FieldSpecService --> RegionsDir`

Update component description tables accordingly.

### G7 Exit Checks

- [ ] `uv run pytest tests/unit/services/test_matching_regression_approval.py -v` — passes (baseline matches)
- [ ] `uv run pytest tests/unit/services/test_matching_service.py -v` — all pass
- [ ] `uv run pytest tests/ -v` — NO regressions
- [ ] Approval test baseline committed
- [ ] Zipcode pre-filter uses spec-configured field (or removed) — [#20]
- [ ] `worker.py` delegates to `MatchingService` (no duplicate matching) — [#24]
- [ ] `RegisteredVoter.full_name`/`is_matchable()` documented as simplified defaults — [#18]
- [ ] `docs/architecture/matching-process.md` committed — matching process explanation
- [ ] `docs/architecture/c4-components.md` updated with new components and edges
- [ ] Flip flag: `FEATURE_FIELDSPEC_MATCHING=true` in env config
- [ ] Hygiene test passes: flag referenced in matching_service.py with else branch
- [ ] Commit: `refactor(field-spec): G7 spec-driven matching service`

---

## G8: Voter List Service Refactor

**Purpose:** Update `VoterListService` to use field spec for CSV parsing and hash computation.

**⚠️ Deep coupling warning:** `VoterListService.merge_voter_list()` hardcodes field extraction into `name_data`/`address_data` dicts (lines 100-109) and uses `RegionSchema.column_mappings` for CSV parsing. The spec's `voter_reg_fields[].category` must map to the existing `RegisteredVoter` blob structure. This gate requires careful mapping.

**Files:**
- Modify: `backend/app/services/voter_list_service.py`
- Extend: `backend/tests/unit/services/test_voter_list_service.py`
- Reference: `backend/app/matching/voter_data_adapter.py` (created in G7.0)

### Tasks

#### G8.1: RED — Write failing tests for spec-driven parsing

Tests:
1. `test_parse_csv_with_dc_spec` — columns mapped from `voter_reg_fields[].csv_column_name` → `voter_reg_fields[].id`
2. `test_merge_uses_spec_hash_fields` — hash uses spec-defined `hash_fields`
3. `test_hash_uses_spec_fields` — hash computation correct with new field IDs
4. `test_category_to_blob_mapping` — `voter_reg_fields` with `category="name"` → `name_data`, `category="address"` → `address_data`, everything else → `other_field_data`
5. `test_compute_hash_finds_geography_fields` — [#19] hash field in `other_field_data` (e.g., `ward`) is included, not silently skipped

#### G8.2: GREEN — Refactor VoterListService

Accept `FieldSpecService` dependency. Use spec for:
- Column name mapping (from `voter_reg_fields[].csv_column_name`)
- Hash field selection (from `hash_fields`)
- Category → blob mapping: group parsed fields by `voter_reg_fields[].category` into the existing `name_data`/`address_data`/`other_field_data` structure on `RegisteredVoter`

**⚠️ `compute_data_hash` must search ALL categories — [#19]:** Current implementation only checks `name_data` and `address_data`. After spec refactor, `hash_fields` can reference any `voter_reg_field.id` across all categories (name, address, registration, geography). Fields like `ward` or `party` (stored in `other_field_data`) would be silently skipped, producing wrong hashes and duplicate voter insertions. Refactor `compute_data_hash` to accept the flattened field map or search all three blobs:

```python
def compute_data_hash(self, name_data, address_data, other_field_data, hash_fields):
    all_fields = {**name_data, **address_data, **other_field_data}
    values = [str(all_fields.get(field, "")) for field in hash_fields]
    return hashlib.md5("|".join(values).encode()).hexdigest()
```

**⚠️ 3 conflicting key schemas exist (#15):**

| Code path | Address keys | File |
|-----------|-------------|------|
| `VoterListService.merge_voter_list()` | `street`, `city`, `state`, `zip` | `voter_list_service.py:104-109` |
| `MatchingService._build_voter_address()` | `street_number`, `street_name`, `street_type`, `street_dir_suffix` | `matching_service.py:274-280` |
| `worker.py` inline matching | `street`, `city`, `state`, `zip` | `worker.py:958-961` |

G8 must normalize all voter blob keys to use the spec's `voter_reg_field.id` values. G7.7 consolidates worker.py separately.

```python
def _group_by_category(
    mapped_fields: dict[str, str],
    voter_reg_fields: list[VoterRegField],
) -> tuple[dict, dict, dict]:
    """Group mapped fields into name_data, address_data, other_field_data blobs."""
    name_data = {}
    address_data = {}
    other_data = {}
    for field in voter_reg_fields:
        value = mapped_fields.get(field.id, "")
        if field.category == "name":
            name_data[field.id] = value
        elif field.category == "address":
            address_data[field.id] = value
        else:
            other_data[field.id] = value
    return name_data, address_data, other_data
```

#### G8.3: RED — Write test for replacing `get_or_create_schema`

`get_or_create_schema` creates a hardcoded default schema completely different from DC's actual columns. Test that `FieldSpecService` replaces this lookup:

1. `test_get_spec_replaces_get_or_create_schema` — field spec replaces `RegionSchema` for CSV parsing
2. `test_existing_voters_not_broken` — existing `RegisteredVoter` rows with old field keys still work

#### G8.4: GREEN — Replace schema lookup with spec lookup

Replace `get_or_create_schema` calls with `FieldSpecService.get_spec`. Update `parse_csv_with_schema` to use `voter_reg_fields` instead of `RegionSchema.column_mappings`.

#### G8.5: REFACTOR — Clean up

- Remove hardcoded column references
- Remove `get_or_create_schema` method (dead code after migration)
- Update providers/wiring in `dependencies.py`

### G8 Exit Checks

- [ ] `uv run pytest tests/unit/services/test_voter_list_service.py -v` — all pass
- [ ] Category → blob mapping tested and correct
- [ ] `compute_data_hash` covers all categories (name, address, other) — [#19]
- [ ] Test confirms geography-category hash fields (e.g., `ward`) are included — [#19]
- [ ] `get_or_create_schema` removed or replaced
- [ ] `uv run pytest tests/ -v` — no regressions
- [ ] Flip flag: `FEATURE_FIELDSPEC_VOTER_LIST=true` in env config
- [ ] Hygiene test passes: flag referenced in voter_list_service.py with else branch
- [ ] Commit: `refactor(field-spec): G8 spec-driven voter list service`

---

## G9: API & Frontend

**Purpose:** Expose region list via API and add region selector to campaign creation.

**Files:**
- Modify: `backend/app/routers/region_router.py` (add `GET /regions`)
- Modify: `backend/app/services/campaign_management_service.py` (refactor `create_campaign`) — [#14]
- Create: `backend/tests/integration/api/test_regions.py`
- Modify: Frontend files (Svelte components, stores)

### Tasks

#### G9.1: RED — Write failing API test

**File:** `backend/tests/integration/api/test_regions.py`

```python
class TestRegionsAPI:
    def test_list_regions_returns_dc(self): ...
    def test_create_campaign_with_region_id(self): ...
```

#### G9.2: GREEN — Implement region list endpoint

Modify `region_router.py` to return available regions from `FieldSpecService`.

#### G9.3: RED — Write failing frontend test

Campaign create modal has region dropdown.

#### G9.4: GREEN — Implement region dropdown

Add `<select>` to campaign create page, wire up to API.

#### G9.5: RED/GREEN — Refactor `create_campaign` to use actual region — [#14]

**Problem:** `CampaignManagementService._ensure_default_region()` hardcodes `region_key="DC"` and `create_campaign` accepts a `region` parameter but ignores it — always creates campaigns against DC. This blocks multi-region campaign creation.

**Evidence:**
- `campaign_management_service.py:32` — `Region.region_key == "DC"` hardcoded in query
- `campaign_management_service.py:65` — `create_campaign(self, name, year, region="DC")` accepts `region` param
- `campaign_management_service.py:77` — `region_id = self._ensure_default_region()` ignores `region` param entirely

**Fix:** Replace `_ensure_default_region()` with a method that looks up the region by the provided `region_key`. Accept `region_id: UUID` or `region_key: str` from the frontend. If region not found, raise error.

Tests:
1. `test_create_campaign_with_region_key` — creates campaign with specified region
2. `test_create_campaign_nonexistent_region_raises` — error for unknown region
3. `test_ensure_default_region_removed` — verify old method gone

#### G9.6: Create "Adding a New Region" tutorial

**File:** `docs/development/adding-a-region.md` (new)

Diátaxis *Tutorial* — step-by-step guide for contributors to add a new region (e.g., Maryland). Covers:
1. Create `backend/app/regions/md.json5` — copy from DC spec as template
2. Update `voter_reg_fields` to match the new region's CSV column names
3. Update `field_mappings` templates for the new region's ballot/petition format
4. Validate locally: `uv run python -c "from app.domain.field_spec import RegionFieldSpecConfig; import json5; spec = RegionFieldSpecConfig.model_validate(json5.loads(open('app/regions/md.json5').read())); print(spec.validate_integrity())"`
5. Run approval tests — new spec gets its own snapshot
6. Open PR — reviewers can see the exact spec diff
7. On deploy, startup loads the new spec into DB
8. Region appears in campaign create dropdown automatically

Reference the JSON5 schema reference doc (`docs/development/field-spec-schema.md`) for field definitions.

#### G9.7: Update C4 components diagram for region router

**File:** `docs/architecture/c4-components.md`

Update the API Layer section:
- Update `RegionRouter` description to include "region list endpoint, field spec lookup"
- Add edge: `RegionRouter --> FieldSpecService` (already added in G7.9 but verify)

Update Service Layer description table:
- Add `field_spec_service` row if not already present from G7.9

### G9 Exit Checks

- [ ] `uv run pytest tests/integration/api/test_regions.py -v` — all pass
- [ ] `GET /regions` returns DC in the list
- [ ] Campaign create includes region selector
- [ ] `create_campaign` uses provided region, not hardcoded DC — [#14]
- [ ] All existing tests still pass
- [ ] `docs/development/adding-a-region.md` committed — new region tutorial
- [ ] `docs/architecture/c4-components.md` updated for region router + service
- [ ] Flip flag: `FEATURE_FIELDSPEC_API=true` in env config
- [ ] All fieldspec flags now True — `settings.features.fieldspec.fully_complete` returns True
- [ ] Hygiene test passes: all 5 flags referenced with else branches
- [ ] Commit: `feat(field-spec): G9 region selector API and frontend`

---

## G10: Cleanup & Migration

**Purpose:** Remove deprecated models and complete the migration.

**Files:**
- Remove: `backend/app/data/database/model/region_schema.py` (entire file)
- Remove: `WashingtonDCRegisteredVoter` and `DcRegisteredVoterSummarise` classes from `backend/app/data/database/model/schema.py` (file stays — `Region` and `Campaign` remain) — [#8]
- Remove: `backend/tests/unit/models/test_region_schema.py` — [#21]
- Remove imports from: `backend/app/persistence/engines/model_imports.py`, `backend/app/data/models.py` — [#17]
- Note: `backend/app/voter/voter_processor.py` and `backend/app/voter/voter_schema.py` — demo code, addressed in G10.8 — [#22]
- Update: `backend/app/ocr/ocr_config.py` — load crop config from spec
- Update: `backend/app/matching/match_columns.py` — display constants only, deferred to future phase — [#23]

### Tasks

#### G10.1: Remove RegionSchema model and related files

Delete the following:
- `backend/app/data/database/model/region_schema.py` — **entire file deleted**
- `backend/tests/unit/models/test_region_schema.py` — **entire file deleted** — [#21]
- Remove `RegionSchema` import from `backend/app/persistence/engines/model_imports.py` — [#17]
- Remove `RegionSchema` import and `__all__` entry from `backend/app/data/models.py` — [#17]
- Remove any other imports of `RegionSchema` across the codebase

Add Alembic migration to drop `region_schemas` table (AFTER `region_field_specs` is populated and data migration in G10.5/G10.7 is complete).

#### G10.2: Remove WashingtonDCRegisteredVoter and DcRegisteredVoterSummarise — [#8]

**⚠️ These are inside `schema.py`, NOT a separate file.** The file `backend/app/data/database/model/schema.py` also contains `Region` and `Campaign` classes which must remain.

- Delete `WashingtonDCRegisteredVoter` class (lines ~35-64, `table=False`) from `schema.py`
- Delete `DcRegisteredVoterSummarise` class (lines ~67-89, `table=False`) from `schema.py`
- Update imports across codebase
- Ensure tests still pass

#### G10.3: Update crop config loading

Modify `ocr_config.py` to load from `RegionFieldSpecConfig.crop_config` instead of hardcoded values.

#### G10.4: Final verification

```bash
cd backend
uv run pytest tests/ -v
uv run ruff check app/ tests/
uv run basedpyright app/
```

#### G10.5: Data migration for existing `region_schemas` rows

If any production/dev database has existing `region_schemas` rows, create an Alembic migration that:

1. For each existing `region_schemas` row, create a corresponding `region_field_specs` row
2. Map `column_mappings` → build `voter_reg_fields` list (best-effort, may need manual review)
3. Map `hash_fields` directly
4. Use sensible defaults for `ballot_fields`, `field_mappings`, `crop_config` (from dc.json5 as template)
5. Add a **data validation step** — after migration, run `validate_integrity()` on each migrated spec and log warnings
6. Only drop `region_schemas` table AFTER validation passes

```python
# In Alembic migration:
def upgrade() -> None:
    # 1. Create region_field_specs table (already done in G4)
    # 2. Migrate data from region_schemas → region_field_specs
    # 3. Only then: op.drop_table('region_schemas')
    pass
```

> **If there are no production `region_schemas` rows** (dev-only), this migration can be simplified to just dropping the old table.

#### G10.6: Pin rapidfuzz version

Add version pin in `pyproject.toml` to prevent non-deterministic approval test failures:

```toml
rapidfuzz = ">=3.9.0,<4.0.0"  # Pin major version — approval tests depend on scoring stability
```

#### G10.7: Data migration for existing `RegisteredVoter` JSON blob keys — [#15]

**⚠️ HIGH SEVERITY — 3 conflicting key schemas exist:**

| Code path | Address keys | Status after G7/G8 |
|-----------|-------------|-------------------|
| `VoterListService.merge_voter_list()` | `street`, `city`, `state`, `zip` | Fixed in G8 — writes spec keys |
| `MatchingService._build_voter_address()` | `street_number`, `street_name`, etc. | Fixed in G7 — reads spec keys |
| `worker.py` inline matching | `street`, `city`, `state`, `zip` | Fixed in G7.7 — delegates to MatchingService |

**Problem:** Any production/dev database with existing `RegisteredVoter` rows has the OLD key names (`street`, `city`, `state`, `zip`) in `address_data` JSON blobs. After G8 refactor, new voters get spec keys (`street_number`, `street_name`, `zip_code`). Old voters will have wrong keys, causing matching failures.

**Migration:** Create an Alembic data migration that:

1. For each `RegisteredVoter` row with existing `address_data`:
   - Remap old keys to DC spec keys: `street` → derive `street_number`/`street_name`/`street_type`/`street_dir_suffix` (best-effort split), `city` → keep, `state` → keep, `zip` → `zip_code`
   - Remap `name_data` if keys differ (likely same: `first_name`, `last_name`)
2. For each `RegisteredVoter` row, check `other_field_data` for any fields that should be in a different category
3. Add validation: after migration, count voters with empty `address_data` and log warning if significant
4. Consider a `key_schema_version` column on `RegisteredVoter` to track which schema the row uses (optional but defensive)

**Key mapping for DC:**

```python
OLD_TO_NEW_KEY_MAP = {
    "street": None,  # Cannot auto-split — log warning, set to street_name as fallback
    "city": "city",
    "state": "state",
    "zip": "zip_code",
}
```

> **If there are no production `RegisteredVoter` rows** (dev-only), this migration can be simplified or skipped entirely. Confirm before implementing.

#### G10.8: Address `voter_processor.py` and `voter_schema.py` demo code — [#22]

**Files:** `backend/app/voter/voter_processor.py`, `backend/app/voter/voter_schema.py`

These files use `get_demo_voter_schema()` with hardcoded DC column names (`Street_Number`, `Street_Name`, etc.). They are not used in the main application flow.

**Decision options:**
- **(a) Recommended:** Mark both files as deprecated with a comment. Add `# DEPRECATED: This module uses hardcoded DC schema. Use FieldSpecService instead.` at the top of each file.
- **(b)** Delete both files if confirmed unused.
- **(c)** Refactor to use spec system in a future phase.

Confirm which approach during G10 implementation.

#### G10.9: `match_columns.py` — explicitly deferred — [#23]

**File:** `backend/app/matching/match_columns.py`

`MatchColumns` is a static display column constant class (`OCR_NAME`, `MATCHED_ADDRESS`, etc.). These are UI/display headers, not matching logic. Impact is minimal.

**Decision:** Deferred to a future phase. Add a `# TODO(field-spec): Make display columns configurable per region` comment. No task needed in this gate.

#### G10.10: Update development README — project structure

**File:** `docs/development/README.md`

Update the project structure tree to reflect new directories and modules:
- Add `app/domain/` — domain value objects and pure functions
- Add `app/regions/` — JSON5 regional spec source files
- Add `app/matching/voter_data_adapter.py`
- Add `app/repositories/field_spec_repo.py`
- Add `app/services/field_spec_service.py`
- Remove references to deleted files (`region_schema.py`, `WashingtonDCRegisteredVoter`)

Add links to new documentation:
- Field spec schema reference (`docs/development/field-spec-schema.md`)
- Adding a region tutorial (`docs/development/adding-a-region.md`)
- Matching process explanation (`docs/architecture/matching-process.md`)
- Testing guide with approval tests (`docs/development/testing.md`)

#### G10.11: Update DOCUMENTATION_STRATEGY.md

**File:** `docs/DOCUMENTATION_STRATEGY.md`

Mark documentation tasks complete:
- Phase 2: ✅ C4 Components diagram updated with spec-driven matching
- Phase 2: ✅ ADRs created for matching strategy (ADR-0006, 0007, 0008)
- Phase 5: ✅ Development guide updated with new project structure

Add to Automation Opportunities table:
- ADR index validation: `scripts/validate-docs.sh` checks ADR index matches files in `decisions/`
- C4 component freshness: gate exit checks verify diagram reflects code changes

#### G10.12: Update architecture README — key decisions table

**File:** `docs/architecture/README.md`

Add rows for new ADRs to the Key Architectural Decisions table:
- ADR-0006: Spec-driven field configuration
- ADR-0007: Feature flag lifecycle framework
- ADR-0008: Template-based field rendering

Add to the Technology Stack table:
- Field Specs: JSON5 + Pydantic (spec-driven configuration)
- Testing: ApprovalTests (regression-guarded golden masters)

### G10 Exit Checks

- [ ] No references to `RegionSchema` in codebase (including `model_imports.py`, `data/models.py`) — [#17, #21]
- [ ] `test_region_schema.py` deleted — [#21]
- [ ] `WashingtonDCRegisteredVoter` and `DcRegisteredVoterSummarise` removed from `schema.py` (file kept for `Region`/`Campaign`) — [#8]
- [ ] No references to `WashingtonDCRegisteredVoter` in codebase
- [ ] Crop config loaded from spec, not hardcoded
- [ ] Data migration from `region_schemas` → `region_field_specs` tested (G10.5)
- [ ] JSON blob key migration for existing `RegisteredVoter` rows tested or confirmed unnecessary (G10.7) — [#15]
- [ ] `voter_processor.py`/`voter_schema.py` deprecated or removed (G10.8) — [#22]
- [ ] `match_columns.py` marked with TODO for future phase (G10.9) — [#23]
- [ ] `rapidfuzz` major version pinned
- [ ] `docs/development/README.md` updated with new project structure and doc links
- [ ] `docs/DOCUMENTATION_STRATEGY.md` updated with completed doc tasks
- [ ] `docs/architecture/README.md` updated with new ADRs and tech stack entries
- [ ] `uv run pytest tests/ -v` — ALL tests pass, zero failures
- [ ] `uv run ruff check app/ tests/` — clean
- [ ] `uv run basedpyright app/` — clean
- [ ] Alembic migration `up + down` both work
- [ ] Commit: `chore(field-spec): G10 cleanup and final migration`

---

## Verification Commands (Quick Reference)

```bash
# All tests
cd backend && uv run pytest tests/ -v --tb=short

# Unit tests only
uv run pytest tests/unit/ -v

# Specific gate tests
uv run pytest tests/unit/domain/test_field_spec.py -v
uv run pytest tests/unit/domain/test_template_renderer.py -v
uv run pytest tests/unit/repositories/test_field_spec_repo.py -v
uv run pytest tests/unit/services/test_field_spec_service.py -v
uv run pytest tests/unit/services/test_field_spec_loading.py -v

# Approval tests (first run creates .received. files)
uv run pytest tests/unit/domain/test_template_renderer_approval.py -v
uv run pytest tests/unit/domain/test_dc_spec_approval.py -v
uv run pytest tests/unit/services/test_matching_regression_approval.py -v

# Lint + type check
uv run ruff check app/ tests/
uv run basedpyright app/

# Run specific gate's exit checks
uv run pytest tests/unit/domain/ -v && uv run ruff check app/domain/ && uv run basedpyright app/domain/
```

---

## Risk Register

| Risk | Impact | Mitigation | Gate |
|------|--------|------------|------|
| Template rendering edge cases | Wrong ballot fields | BDD + approval tests cover all DC patterns | G2 |
| "N/A" values treated as non-empty | Wrong address rendering | Add explicit test case + decide treatment in `render_template` | G2 |
| Migration data loss | Existing region_schemas lost | Alembic migration tested, JSON5 source is new source of truth | G4, G10 |
| Matching quality regression | Wrong voter matches | Approval baseline BEFORE refactor | G7 |
| Performance: spec loaded per match call | Slow matching | Cache spec per region in service instance | G5 |
| Domain model ↔ DB model drift | Silent data corruption | Round-trip tests in repository tests | G4 |
| `field_scores` shape change breaks consumers | API consumers break | Approval test captures new shape; update API types | G7 |
| `rapidfuzz` version bump changes scores | Flaky approval tests | Pin major version in pyproject.toml | G10 |
| `RegisteredVoter` blob structure mismatch | Data not found by `render_template` | Voter data adapter with category mapping tests | G7 |
| `region_key` casing mismatch | Spec not found at runtime | Normalize to uppercase consistently; add test | G6 |
| No DI wiring for new services | Services unavailable at runtime | G6.5 wires FieldSpecService into FastAPI DI | G6 |
| FK constraint failure on spec loading | App fails to start | G6.8 auto-creates Region rows from spec metadata | G6 |
| 3 conflicting key schemas in voter blobs | Matching broken for existing voters | G7.7 consolidates worker.py; G10.7 migrates existing blob keys | G7, G10 |
| `create_campaign` ignores region param | All campaigns created against DC | G9.5 refactors to use actual region lookup | G9 |
| `pre_filter_voters` hardcodes `zip` key | Empty filter results post-refactor | G7.3a makes filter field configurable via spec | G7 |
| `compute_data_hash` misses other categories | Duplicate voter insertions | G8.2 expands hash to search all three blobs | G8 |
| `worker.py` duplicate matching breaks silently | Wrong match results | G7.7 consolidates into MatchingService | G7 |
| Documentation drift — diagrams/code go stale | Confusing onboarding | Gate exit checks require doc updates; ADRs for all major decisions | G0–G10 |

---

## Documentation Plan

**Frameworks:** [C4 Model](https://c4model.com/) for architecture diagrams (Mermaid in Markdown), [Diátaxis](https://diataxis.fr/) for documentation types.

### Diátaxis Mapping

| Quadrant | Existing | New in this plan |
|----------|----------|-----------------|
| **Tutorial** (learning-oriented) | `running-locally.md`, `demo-walkthrough.md` | `docs/development/adding-a-region.md` (G9.6) |
| **How-To** (task-oriented) | `development/README.md` (partial) | Approval testing section in `docs/development/testing.md` (G2.6) |
| **Explanation** (understanding-oriented) | `architecture/c4-*.md`, ADRs | `docs/architecture/matching-process.md` (G7.8), ADR-0006/0007/0008 (G0–G2) |
| **Reference** (information-oriented) | `openapi.yaml`, `project-structure.md` | `docs/development/field-spec-schema.md` (G3.5) |

### Documentation Tasks by Gate

| Gate | Task | File | Diátaxis type |
|------|------|------|--------------|
| G0 | ADR-0007: Feature flag lifecycle framework | `docs/architecture/decisions/0007-*.md` | Explanation |
| G1 | ADR-0006: Spec-driven field configuration | `docs/architecture/decisions/0006-*.md` | Explanation |
| G2 | ADR-0008: Template-based field rendering | `docs/architecture/decisions/0008-*.md` | Explanation |
| G2 | Approval testing how-to | `docs/development/testing.md` (new/section) | How-To |
| G3 | JSON5 spec schema reference | `docs/development/field-spec-schema.md` (new) | Reference |
| G7 | Matching process explanation | `docs/architecture/matching-process.md` (new) | Explanation |
| G7 | Update C4 components diagram | `docs/architecture/c4-components.md` | Explanation |
| G9 | Adding a new region tutorial | `docs/development/adding-a-region.md` (new) | Tutorial |
| G9 | Update C4 for region router | `docs/architecture/c4-components.md` | Explanation |
| G10 | Update development README | `docs/development/README.md` | Reference |
| G10 | Update DOCUMENTATION_STRATEGY | `docs/DOCUMENTATION_STRATEGY.md` | Meta |
| G10 | Update architecture README | `docs/architecture/README.md` | Reference |

### Automation: Keeping Documentation Fresh

#### ADR Index Validation

Extend `scripts/validate-docs.sh` to verify ADR index is current:

```bash
# Check: every .md file in decisions/ (except template.md, README.md) has a row in the ADR index
# Check: every ADR number in the index has a corresponding file
```

#### C4 Component Freshness

Add to gate exit checks for gates that add/remove components (G7, G9):

```bash
# Verify c4-components.md mentions any new component files
grep -q "FieldSpecService" docs/architecture/c4-components.md || echo "FAIL: c4-components.md missing FieldSpecService"
```

#### Mermaid Syntax Validation

```bash
# Validate all Mermaid diagrams render correctly
npx @mermaid-js/mermaid-cli -i docs/architecture/c4-components.md -o /dev/null
```

#### Documentation Completeness Check

Add to gate exit protocol (optional, manual):

1. ADR index in `docs/architecture/decisions/README.md` includes all new ADRs from this gate
2. C4 diagram in `docs/architecture/c4-components.md` reflects any new/removed components
3. `docs/development/README.md` project structure tree is current
4. Any new config file formats documented in `docs/development/field-spec-schema.md`
