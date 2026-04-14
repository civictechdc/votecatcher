# Plan: Configurable Ballot & Voter Registration Field Specifications

## Summary

Introduce a region-specific field specification system that defines:
1. **Ballot template fields** — what fields appear on a petition/ballot form for a region
2. **Voter registration field specs** — what columns exist in a region's voter roll CSV
3. **Field mappings** — template strings that combine voter reg fields into ballot template fields
4. **Crop config** — default petition crop dimensions per region

Replace the existing `RegionSchema` model with a richer `RegionFieldSpec` aggregate.

---

## Related Issues & PRs

| # | Type | Title | Alignment | Notes |
|---|------|-------|-----------|-------|
| [#12](https://github.com/civictechdc/votecatcher/pull/12) | PR | Add configurable voter region specifications | **Direct predecessor** — same intent. Branch `voter_specs` is stale (pre-SvelteKit). Superseded by this plan. | Close when plan execution begins |
| [#11](https://github.com/civictechdc/votecatcher/pull/11) | PR | Migration fixes and refactoring | Subset of #12. FastAPI migration fixes already addressed by #18. | Superseded |
| [#21](https://github.com/civictechdc/votecatcher/issues/21) | Issue | DDD restructuring of app/matching/ | **Overlaps G7** — proposes DDD value objects for matching. | **Deferred until post-G10.** Will need rewriting against spec-driven architecture anyway |
| [#18](https://github.com/civictechdc/votecatcher/pull/18) | PR | Backend hardening, brand updates, deploy fix | G6 startup integration builds on its `ApplicationStartup` DI pattern. | Already merged |

---

## Branch & Worktree Strategy

**Methodology:** [Trunk-Based Development](https://trunkbaseddevelopment.com/) with gate-scoped feature flags for safe incremental integration.

### Feature Flags (Gate Integration Guards)

Each gate has a feature flag guarding its integration point. **`False` = old code path. `True` = new spec-driven path.** This enables merging incrementally without breaking the running app.

**Implementation:** `FieldSpecFlags` as a nested Pydantic model on `FeatureConfig`, sourced from `FEATURE_FIELD_SPEC_*` env vars. Full details in `plans/configurable-field-specs-plan.md` → "Feature Flags" section.

| Flag | Default | Guards | Removed in |
|------|---------|--------|------------|
| `field_spec_domain` | `False` | Domain types available (G1–G2) | G10 |
| `field_spec_persistence` | `False` | DB model + repo (G3–G4) | G10 |
| `field_spec_loading` | `False` | Startup spec loading (G5–G6) | G10 |
| `field_spec_matching` | `False` | MatchingService spec-driven (G7) | G10 |
| `field_spec_voter_list` | `False` | VoterListService spec-driven (G8) | G10 |
| `field_spec_api` | `False` | /regions endpoint + frontend (G9) | G10 |
| `field_spec_cleanup` | `False` | Old code removed (G10) | G10 (immediate) |

After G10, all flags are deleted. The feature is no longer a feature — it's how the app works.

### Single Feature Branch

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

---

## Feature Flag Framework

**Purpose:** Structured, enforceable feature flags that support incremental gate delivery with automated lifecycle hygiene.

### Architecture

```
app/settings/providers/features/
├── _base.py          # FeatureFlag, FlagMeta, FlagLifecycle
├── runtime.py        # permanent toggles (simulation, demo, debug)
├── fieldspec.py      # transitional: one flag per gate (G4–G9)
└── __init__.py       # AllFeatures registry + all_transitional()
```

**Two flag lifecycles:**
- **Permanent** (`FlagLifecycle.permanent`): Always exists. Simulation mode, demo mode, debug mode. Exempt from hygiene checks.
- **Transitional** (`FlagLifecycle.transitional`): Added for a feature, removed after rollout. Enforced by CI hygiene tests.

### Usage Pattern

Each gate adds an `if/else` at the call site:

```python
if settings.features.fieldspec.matching.enabled:
    # spec-driven path (new code)
    score = spec_driven_matching(spec, ocr, voter_data)
else:
    # legacy path (old code — removed in G10)
    score = hardcoded_matching(ocr_name, ocr_address, voter_name, voter_address)
```

### Transitional Flags for This Plan

| Flag | Env var | Gate |
|------|---------|------|
| `fieldspec.persistence` | `FEATURE_FIELDSPEC_PERSISTENCE` | G4 |
| `fieldspec.service` | `FEATURE_FIELDSPEC_SERVICE` | G5-G6 |
| `fieldspec.matching` | `FEATURE_FIELDSPEC_MATCHING` | G7 |
| `fieldspec.voter_list` | `FEATURE_FIELDSPEC_VOTER_LIST` | G8 |
| `fieldspec.api` | `FEATURE_FIELDSPEC_API` | G9 |

### Automated Hygiene (CI)

| Check | Detects | Action |
|-------|---------|--------|
| `test_no_dead_transitional_flags` | Flag defined but no code references `.enabled` | Remove the flag |
| `test_no_ossified_transitional_flags` | Flag checked but no `else` branch | Add fallback or remove |
| `test_domain_files_match_registry` | File/registry mismatch | Sync |

### Testing Strategy

| Test file | Scope | Extends when |
|-----------|-------|-------------|
| `test_feature_flag_framework.py` | Unit: base types, domain models, registry | New domain or flag added |
| `test_feature_flag_hygiene.py` | CI: dead/ossified/orphan detection | Automatic — no changes needed |
| `test_feature_flag_lifecycle.py` | Integration: add→use→cleanup simulation | Reference for new domains |

### Adding a New Domain (Future)

1. Create `app/settings/providers/features/newdomain.py` with `NewDomainFlags(BaseModel)`
2. Add field to `AllFeatures` in `__init__.py`
3. Update `test_domain_files_match_registry` expected set
4. Hygiene tests auto-discover new transitional flags

### G10 Cleanup

1. Delete `fieldspec.py`
2. Remove `fieldspec` from `AllFeatures`
3. Remove all `if/else` branches, keep only spec-driven paths
4. Delete `feature_config.py` (old flat config)
5. Hygiene test confirms zero stale flags

---

## Architecture Principles

### Outside-In Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Adapters (outside)                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │ Routers   │  │ Repos    │  │ External (OCR, etc)   │  │
│  │ (FastAPI) │  │ (SQLMod) │  │                       │  │
│  └────┬─────┘  └────┬─────┘  └───────────┬───────────┘  │
│       │              │                    │               │
│  ┌────▼──────────────▼────────────────────▼───────────┐  │
│  │  Application Services (use cases)                   │  │
│  │  FieldSpecService, VoterListService, MatchingService │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────▼───────────────────────────────┐  │
│  │  Domain (inside - pure, no infrastructure deps)     │  │
│  │  BallotField, VoterRegField, FieldMapping,           │  │
│  │  CropConfig, RegionFieldSpecConfig                   │  │
│  │  TemplateRenderer (pure function)                    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Dependency direction**: adapters → services → domain. Domain never imports infrastructure.

### Layer Conventions

| Layer | Location | Depends on | Testing |
|-------|----------|------------|---------|
| **Domain** | `app/domain/field_spec.py` | Nothing (pure Pydantic) | Unit tests, no mocks |
| **Domain services** | `app/domain/field_spec.py` (methods on domain objects) | Domain only | Unit tests, no mocks |
| **Application services** | `app/services/` | Domain + Protocol interfaces | Unit tests with mock repos |
| **Repositories** | `app/repositories/` | Domain + DB models | Integration tests with SQLite |
| **Persistence contracts** | `app/persistence/contracts.py` | Domain only (Protocol definitions) | N/A (structural typing) |
| **Routers** | `app/routers/` | Services + API models | Integration tests via TestClient |

### DDD Aggregates & Value Objects

| Type | Class | Rationale |
|------|-------|-----------|
| **Aggregate Root** | `RegionFieldSpecConfig` | Single consistency boundary for all region spec data |
| **Value Object** | `BallotField` | Immutable, compared by value, no identity |
| **Value Object** | `VoterRegField` | Immutable, compared by value |
| **Value Object** | `FieldMapping` | Immutable, compared by value |
| **Value Object** | `CropConfig` | Immutable, compared by value |
| **Domain Service** | `TemplateRenderer` | Stateless pure function, operates on domain types |

### BDD Test Scenarios

Tests are written as behavioral scenarios **before** implementation (outside-in):

```gherkin
Feature: Region Field Specification

  Scenario: Map voter registration fields to ballot fields
    Given a DC region field spec with voter reg fields [First_Name, Middle_Name, Last_Name]
    And a field mapping from ballot field "name" with template "{first_name} {middle_name} {last_name}"
    When I render the template with voter data {first_name: "John", middle_name: "", last_name: "Smith"}
    Then the ballot field "name" should be "John Smith"

  Scenario: Drop empty placeholders in address template
    Given a DC field mapping for "address" with template "{street_number} {street_name} {street_type}, Apt {apartment_number}"
    When I render with voter data {street_number: "730", street_name: "Lawrence", street_type: "St", apartment_number: ""}
    Then the result should be "730 Lawrence St"

  Scenario: Weighted similarity from spec-driven matching
    Given a spec with ballot fields [name(weight=1.0), address(weight=1.0), ward(weight=0.3)]
    When I match OCR "John Smith at 123 Main St" against voter "John Smith at 123 Main St, Ward 5"
    Then name and address scores should dominate the similarity
    And ward should contribute at most 0.3 / 2.3 of the total weight
```

### TDD Red-Green-Refactor Cycle

Each phase follows this loop:

1. **RED**: Write failing BDD test for one behavior
2. **GREEN**: Write minimum code to pass (domain first, then adapter)
3. **REFACTOR**: Clean up while tests stay green

**Outside-in order**: Write acceptance test → write unit test → implement domain → implement service → implement adapter.

### Approval Testing (Regression Guard)

**Library**: [ApprovalTests.Python](https://github.com/approvals/approvaltests.Python)

```
pip install approvaltests pytest-approvaltests
```

Run with: `pytest --approvaltests-use-reporter='PythonNativeReporter'`

#### Core Concept

Approval tests replace `assert x == y` with `verify(x)`. Instead of predicting expected output, you **capture actual output and approve it**. Future changes that alter output are flagged as failures — the developer reviews the diff and either fixes the regression or explicitly approves the new output.

Source: [ApprovalTests Documentation — What Are Approvals](https://github.com/approvals/ApprovalTests.Documentation/blob/main/explanations/what_are_approvals.md)

#### Approval TDD Loop (differs from assertion TDD)

Per the [official documentation](https://github.com/approvals/ApprovalTests.Documentation/blob/main/explanations/approval_testing.md):

```
Traditional TDD:         write test (with expected) → RED → write code → GREEN → refactor
Approval TDD:            write test (no expected) → write code → assess result → approve → refactor
```

The key difference: you don't need to know the expected output upfront. Write the test calling `verify()`, implement the code, inspect the `.received.` file, then approve it.

#### Why Approval Testing Here

This feature has three areas where exact output matters and regressions are hard to catch with simple assertions:

1. **Template rendering** — address formatting is finicky (whitespace, commas, "Apt" prefixes). A suite of real DC voter rows rendered to ballot fields creates a golden master. Any change in `render_template` logic breaks the approval.

2. **Spec-driven matching scores** — switching from hardcoded fields to dynamic spec-driven matching changes similarity scores. Approval tests capture the *full score matrix* for a known set of OCR vs voter pairs. If refactoring MatchingService changes scores, the approval test catches it.

3. **DC spec JSON seed** — the default DC field spec is a large JSON blob. Approval test verifies the seeded spec matches exactly, preventing accidental drift.

#### Creating Output (rendering strategy)

Per [Creating Desired Output](https://github.com/approvals/ApprovalTests.Documentation/blob/main/explanations/creating_output.md), we have 3 places to control output:

```
#1: Custom formatter (like __str__ or a to_approval_string() method on domain objects)
#2: Per-element transformation in verify_all (lambda scrubbing)
#3: Whole-file scrubber (e.g., scrub timestamps, non-deterministic values)
```

For this project:
- **#1**: Add `to_approval_string()` on `RegionFieldSpecConfig` for readable spec diffs
- **#2**: Use lambdas in `verify_all` to format voter→ballot mapping results
- **#3**: Use `Scrubber` for matching scores (round floats to 4 decimal places for deterministic output)

#### Approval Test Locations

Approved files live alongside test files (standard ApprovalTests convention). Committed to git.

```
tests/unit/domain/
├── test_field_spec.py
├── test_template_renderer.py
├── test_template_renderer_approval.py              # Approval tests
│   ├── *.test_dc_address_variants.approved.txt
│   ├── *.test_dc_name_variants.approved.txt
│   └── *.test_dc_full_ballot_mapping.approved.txt
│
tests/unit/services/
├── test_matching_service.py
├── test_matching_regression_approval.py             # Approval tests
│   └── *.test_dc_matching_score_matrix.approved.txt
│
tests/unit/domain/
├── test_dc_spec_approval.py                         # Approval tests
│   └── *.test_dc_seed_spec.approved.json
```

#### Approval Test Pattern

**Template rendering (verify_all for collections):**

```python
from approvaltests import verify, verify_all

class TestTemplateRendererApproval:
    """Approval test: golden master for all DC address/name rendering variants.

    Uses real DC voter CSV data to generate comprehensive render output.
    Any change to render_template logic will fail until re-approved.
    """

    def test_dc_address_variants(self):
        """Render all DC address patterns from sample voter data."""
        template = "{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"
        dc_addresses = {
            "standard NE": {"street_number": "730", "street_number_suffix": "", "street_name": "Lawrence", "street_type": "St", "street_dir_suffix": "NE", "apartment_number": ""},
            "with unit SE": {"street_number": "1300", "street_number_suffix": "", "street_name": "4th", "street_type": "St", "street_dir_suffix": "SE", "apartment_number": "UNIT 715"},
            "with apt hash": {"street_number": "235", "street_number_suffix": "", "street_name": "Carroll", "street_type": "St", "street_dir_suffix": "NW", "apartment_number": "#316"},
            "N/A street num": {"street_number": "N/A", "street_number_suffix": "", "street_name": "4th", "street_type": "St", "street_dir_suffix": "NW", "apartment_number": "#011"},
            "empty street num": {"street_number": "", "street_number_suffix": "", "street_name": "Emailes", "street_type": "St", "street_dir_suffix": "SW", "apartment_number": ""},
        }
        verify_all(
            "DC address template renders",
            dc_addresses.items(),
            lambda pair: f"{pair[0]}: {pair[1]} => {render_template(template, pair[1])!r}"
        )

    def test_dc_name_variants(self):
        """Render all DC name patterns (with/without middle, etc.)."""
        template = "{first_name} {middle_name} {last_name}"
        names = {
            "full name": {"first_name": "John", "middle_name": "M", "last_name": "Smith"},
            "no middle": {"first_name": "Jane", "middle_name": "", "last_name": "Doe"},
            "empty middle": {"first_name": "Bob", "middle_name": " ", "last_name": "Jones"},
        }
        verify_all(
            "DC name template renders",
            names.items(),
            lambda pair: f"{pair[0]}: {pair[1]} => {render_template(template, pair[1])!r}"
        )

    def test_dc_full_ballot_mapping(self):
        """End-to-end: voter row → all ballot fields for DC spec."""
        spec = dc_default_spec()
        voters = _load_dc_sample_voters_from_split_csvs()
        lines = []
        for voter in voters:
            ballot = FieldSpecService.map_voter_to_ballot(spec, voter)
            lines.append(f"Voter: {voter.get('Last_Name', '')}, {voter.get('First_Name', '')}")
            for k, v in ballot.items():
                lines.append(f"  {k}: {v!r}")
            lines.append("")
        verify("\n".join(lines))
```

**Matching score regression (scrubbed for determinism):**

```python
from approvaltests import verify
from approvaltests.scrubbers import Scrubbers

def _round_scores(text: str) -> str:
    """Scrubber: round all float scores to 4 decimal places."""
    import re
    return re.sub(r"score=\d+\.\d+", lambda m: f"score={float(m.group()[6:]):.4f}", text)

class TestMatchingRegressionApproval:
    """Approval test: capture matching score matrix before and after refactor.

    Write this BEFORE refactoring MatchingService.
    Run with current (hardcoded) implementation to create approved baseline.
    Then refactor to spec-driven matching — if scores change, test fails.
    """

    def test_dc_matching_score_matrix(self):
        """Golden master: similarity scores for known OCR vs voter pairs."""
        spec = dc_default_spec()
        voters = _load_dc_sample_voters()
        ocr_results = _load_dc_sample_ocr()

        lines = []
        for ocr in ocr_results:
            for voter in voters:
                ballot_fields = map_voter_to_ballot(spec, voter)
                score = calculate_similarity(spec, ocr, ballot_fields)
                confidence = assign_confidence(score)
                lines.append(
                    f"OCR={ocr['name']!r} vs Voter={ballot_fields['name']!r} "
                    f"=> score={score:.4f} conf={confidence.value}"
                )
        verify("\n".join(lines), scrubber=_round_scores)
```

**DC spec snapshot:**

```python
class TestDcDefaultSpecApproval:
    """Approval test: verify DC seed spec hasn't drifted."""

    def test_dc_seed_spec(self):
        """Snapshot the full DC spec as pretty-printed JSON."""
        from approvaltests import verify
        spec = dc_default_spec()
        verify(spec.model_dump_json(indent=2))
```

#### Pre-Refactor Baseline Pattern

The matching score approval test follows a critical workflow for **characterization testing** (per [understandlegacycode.com](https://understandlegacycode.com/approval-tests/)):

```
1. BEFORE refactoring MatchingService:
   - Write test_dc_matching_score_matrix using CURRENT hardcoded implementation
   - Run test → inspect .received. file → approve it (this is the baseline)

2. DURING refactoring:
   - Change MatchingService to use spec-driven matching
   - Run test → if .received. differs from .approved. → diff tool shows exactly what changed
   - If changes are intentional (e.g., better weighted scoring) → approve new output
   - If changes are unintentional → fix the regression

3. AFTER refactoring:
   - Approved file represents the new (correct) scoring behavior
   - Future changes to matching logic are regression-guarded
```

#### Approval Testing Workflow

1. **First run**: test fails because no `.approved.` file exists. A `.received.` file is created with actual output.
2. **Inspect**: review `.received.` file content.
3. **Approve**: `mv *.received.txt *.approved.txt` (or use reporter/diff tool).
4. **Subsequent runs**: output matches → pass. Differs → fail with diff shown.
5. **CI**: `.approved.` files committed to git. Any unapproved change fails CI.

#### Dependencies

Add to `pyproject.toml`:

```toml
# In [project.optional-dependencies] or dev dependency group (uv format):
approvaltests = "*"
pytest-approvaltests = "*"
```

#### When to Write Approval Tests vs Assertion Tests

| Use assertion tests when | Use approval tests when |
|--------------------------|-------------------------|
| Single value check (`assert score >= 0.95`) | Multi-line / multi-case output |
| Testing one behavior | Golden master / regression guard |
| Fast feedback on exact value | Catching unexpected changes in complex output |
| Domain invariant enforcement | Template rendering across many variants |
| | Matching score matrices |
| | JSON spec snapshots |
| | Characterization testing before refactoring |

---

## Current State

- `RegionSchema` has flat `column_mappings` (CSV col → canonical name) and `hash_fields`
- `RegisteredVoter` stores generic JSON blobs (`name_data`, `address_data`, `other_field_data`)
- `MatchingService` hardcodes field keys: `first_name`, `last_name`, `street_number`, etc.
- `WashingtonDCRegisteredVoter` model exists with DC-specific columns but is not table-backed
- `CropConfig` hardcoded in `ocr_config.py` with TODO to load from configuration
- DC voter roll CSV has 21 core columns (name, address, registration, ward/precinct)
- Petition signature fields for DC: **Name, Address, Ward, Date Signed** (no Party)
- Project already uses hexagonal patterns: domain models (Pydantic), Protocol-based contracts, repos that map DB → domain

## Problems

1. Adding a new region requires code changes (hardcoded field keys in MatchingService)
2. No explicit definition of what the ballot/petition template looks like per region
3. Mapping voter reg fields → ballot fields is implicit and scattered
4. Address formatting (combining 6 address components) needs special handling
5. Crop config is hardcoded, not region-aware

---

## Regional Spec Source Files

### Rationale

Regional field specs are **configuration, not user data**. They define the shape of external systems (voter rolls, petition forms) per jurisdiction. Adding a new region should be:

1. Add a JSON5 file to the repo
2. Get it reviewed in a PR (visible, auditable, diffable)
3. Loaded into DB automatically on next startup

This avoids per-region Alembic migrations and makes specs reviewable like code.

### JSON5 Format

Spec files use **JSON5** (superset of JSON) for readability — `//` line comments, `/* */` block comments, and trailing commas are all supported.

**Parser**: [json5](https://pypi.org/project/json5/) v0.14.0 — actively maintained (29 releases), Apache 2.0, zero dependencies, drop-in `json5.loads()`.

**Add to `pyproject.toml`:**

```toml
# In [project.dependencies] (uv format — this project does NOT use Poetry):
json5 = ">=0.14.0"
```

Example spec file with JSON5 features:

```json5
{
    // DC voter registration field specification
    // Source: DC Board of Elections voter roll export

    "region_name": "District of Columbia",
    "country_code": "US",

    "ballot_fields": [
        {
            "id": "name",
            "label": "Full Name",
            "field_type": "text",
            "required_for_matching": true,
            "match_weight": 1.0,  // highest weight for name matching
        },
        {
            "id": "address",
            "label": "Address",
            "field_type": "address",
            "required_for_matching": true,
            "match_weight": 1.0,
        },
        // Ward contributes to matching but at reduced weight
        {
            "id": "ward",
            "label": "Ward",
            "field_type": "integer",
            "required_for_matching": false,
            "match_weight": 0.3,
        },
    ],

    /* Voter registration fields from DC Board of Elections.
       21 core fields, election history columns excluded. */
    "voter_reg_fields": [
        {"id": "last_name", "csv_column_name": "Last_Name", "data_type": "text", "category": "name"},
        {"id": "first_name", "csv_column_name": "First_Name", "data_type": "text", "category": "name"},
        // ...
    ],

    "field_mappings": [
        {"ballot_field_id": "name", "template": "{first_name} {middle_name} {last_name}"},
        {"ballot_field_id": "address", "template": "{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"},
        {"ballot_field_id": "ward", "template": "{ward}"},
    ],
    "hash_fields": ["last_name", "first_name", "street_number", "street_name", "zip_code"],
    "crop_config": {
        "top_crop": 0.385,    // 38.5% from top of page
        "bottom_crop": 0.725, // 72.5% from top of page
        "base_threshold": 85,
    },
}
```

### Directory Structure

```
backend/app/regions/                     # Source of truth for regional specs
├── dc.json5                             # Washington, D.C.
├── md.json5                             # Maryland (future)
├── va.json5                             # Virginia (future)
└── README.md                            # How to add a new region spec
```

The filename (sans `.json5`) becomes the `region_key` (e.g., `dc` → region_key `"DC"`).

### Loading Strategy

**File**: `app/services/field_spec_service.py`

```python
import json5

class FieldSpecService:
    """Application service: load, validate, and manage field specs."""

    REGIONS_DIR = Path(__file__).parent.parent / "regions"

    def __init__(self, repo: FieldSpecRepository):
        self._repo = repo

    def load_all_specs(self) -> tuple[int, list[str]]:
        """Load all regional spec files into DB.

        Called at app startup. For each region:
        1. Parse JSON5 → dict (json5.loads supports comments + trailing commas)
        2. Validate dict → RegionFieldSpecConfig (Pydantic validates schema)
        3. Run validate_integrity() → collect structural errors
        4. Upsert into DB (create region if missing, update spec if changed)

        Returns (loaded_count, all_errors).
        """
        errors: list[str] = []
        loaded = 0

        for spec_file in sorted(self.REGIONS_DIR.glob("*.json5")):
            region_key = spec_file.stem.upper()
            try:
                raw = spec_file.read_text()
                data = json5.loads(raw)
                spec = RegionFieldSpecConfig.model_validate(data)
            except (ValueError, ValidationError) as e:
                errors.append(f"[{region_key}] Parse/validation error: {e}")
                continue

            validation_errors = spec.validate_integrity()
            if validation_errors:
                for err in validation_errors:
                    errors.append(f"[{region_key}] {err}")
                continue

            self._repo.upsert(region_key=region_key, spec=spec)
            loaded += 1

        return loaded, errors

    # ... existing methods (get_spec, map_voter_to_ballot, validate_spec)
```

### Startup Integration

**File**: `app/startup.py` — add spec loading after DB init:

```python
async def startup(self) -> None:
    self._db_initializer()
    self._spec_loader()          # <-- new: load regional specs
    self._config_validator()
    self._worker_task = asyncio.create_task(self._worker_starter())
```

### Repository Contract Addition

**File**: `app/persistence/contracts.py`

```python
@runtime_checkable
class FieldSpecRepository(Protocol):
    """Port: manages field spec persistence."""
    def find_by_region(self, region_id: UUID) -> RegionFieldSpecConfig | None: ...
    def find_by_region_key(self, region_key: str) -> RegionFieldSpecConfig | None: ...
    def save(self, spec: RegionFieldSpecConfig, region_id: UUID) -> RegionFieldSpecConfig: ...
    def upsert(self, region_key: str, spec: RegionFieldSpecConfig) -> None: ...
    def delete(self, region_id: UUID) -> bool: ...
    def list_regions(self) -> list[tuple[str, str, UUID]]: ...  # (key, name, id)
```

> **Note:** `RegionFieldSpecModel.name` is a DB column not present on the domain model. During `upsert`, derive the name from the spec file's `region_name` field. The `find_by_region_key` method normalizes input to uppercase.

### Region Key Normalization Convention

All region keys are stored as **uppercase** in both filesystem and database:

- Filenames: `dc.json5`, `md.json5` (lowercase on disk, standard convention)
- `region_key` in DB: `"DC"`, `"MD"` (uppercase — `spec_file.stem.upper()`)
- `Region.region_key` in existing DB: must be uppercase

`load_all_specs` derives `region_key` via `spec_file.stem.upper()`. The `find_by_region_key` query normalizes input the same way.

### How to Add a New Region

1. Create `backend/app/regions/{key}.json5` with the spec
2. Validate locally: `python -m app.domain.field_spec validate app/regions/md.json5`
3. Open PR — reviewers can see the exact spec diff
4. On deploy, startup loads the new spec into DB
5. The region appears in the campaign create dropdown automatically

### Tests for Spec Loading

**File**: `tests/unit/services/test_field_spec_service.py`

```python
class TestFieldSpecLoading:
    """BDD: loading regional specs from source files."""

    # Scenario: valid spec file loads successfully
    def test_load_valid_spec(self): ...

    # Scenario: invalid JSON schema produces error
    def test_load_invalid_schema_reports_error(self): ...

    # Scenario: integrity validation failure produces error
    def test_load_invalid_integrity_reports_error(self): ...

    # Scenario: existing spec updated on reload
    def test_upsert_updates_existing_spec(self): ...

    # Scenario: multiple specs load independently
    def test_load_all_specs(self): ...

    # Scenario: missing regions dir is not an error (graceful)
    def test_missing_regions_dir(self): ...

    # Scenario: all source specs pass validation at startup
    def test_all_source_specs_valid(self): ...
```

---

## Design

### Domain Layer (pure, no infrastructure imports)

**File**: `app/domain/field_spec.py`

```python
class BallotField(BaseModel, frozen=True):
    """Value Object: one field on a petition/ballot template."""
    id: str
    label: str
    field_type: Literal["text", "address", "integer", "date"]
    required_for_matching: bool
    match_weight: float = Field(default=1.0, ge=0.0)

class VoterRegField(BaseModel, frozen=True):
    """Value Object: one column in a voter registration CSV."""
    id: str
    csv_column_name: str
    data_type: Literal["text", "integer", "date"]
    category: Literal["name", "address", "registration", "geography"]

class FieldMapping(BaseModel, frozen=True):
    """Value Object: maps one ballot field to voter reg fields via template."""
    ballot_field_id: str
    template: str

class CropConfig(BaseModel, frozen=True):
    """Value Object: petition crop dimensions for a region."""
    top_crop: float = Field(ge=0.0, le=1.0)
    bottom_crop: float = Field(ge=0.0, le=1.0)
    base_threshold: int = Field(ge=0, le=255)

class RegionFieldSpecConfig(BaseModel, frozen=True):
    """Aggregate Root: complete field specification for a region."""
    region_name: str
    country_code: str = "US"
    ballot_fields: list[BallotField]
    voter_reg_fields: list[VoterRegField]
    field_mappings: list[FieldMapping]
    hash_fields: list[str]
    crop_config: CropConfig

    def get_mapping_for(self, ballot_field_id: str) -> FieldMapping | None:
        """Domain query: find mapping for a specific ballot field."""
        return next(
            (m for m in self.field_mappings if m.ballot_field_id == ballot_field_id),
            None,
        )

    def matchable_fields(self) -> list[BallotField]:
        """Domain query: ballot fields that participate in matching."""
        return [f for f in self.ballot_fields if f.required_for_matching and f.match_weight > 0]

    def total_match_weight(self) -> float:
        """Domain query: sum of match weights."""
        return sum(f.match_weight for f in self.matchable_fields())

    def validate_integrity(self) -> list[str]:
        """Domain invariant: structural validation of the spec.

        Returns a list of error messages. Empty list = valid spec.
        Called on save (via FieldSpecService) and at app startup for seeded specs.

        Validation rules:
        1. No duplicate ballot field IDs
        2. No duplicate voter reg field IDs
        3. No duplicate voter reg CSV column names
        4. Every mapping references an existing ballot field
        5. Template placeholders reference existing voter reg fields
        6. Every matchable ballot field (required_for_matching=True) has a mapping
        7. Hash fields reference existing voter reg field IDs
        8. At least one matchable ballot field exists
        9. Crop config: top_crop < bottom_crop
        """
        errors: list[str] = []

        ballot_ids = {f.id for f in self.ballot_fields}
        voter_ids = {f.id for f in self.voter_reg_fields}
        csv_columns = {f.csv_column_name for f in self.voter_reg_fields}

        # 1. Duplicate ballot field IDs
        seen_ballot: set[str] = set()
        for f in self.ballot_fields:
            if f.id in seen_ballot:
                errors.append(f"Duplicate ballot field ID: {f.id}")
            seen_ballot.add(f.id)

        # 2. Duplicate voter reg field IDs
        seen_voter: set[str] = set()
        for f in self.voter_reg_fields:
            if f.id in seen_voter:
                errors.append(f"Duplicate voter reg field ID: {f.id}")
            seen_voter.add(f.id)

        # 3. Duplicate CSV column names
        seen_csv: set[str] = set()
        for f in self.voter_reg_fields:
            if f.csv_column_name in seen_csv:
                errors.append(f"Duplicate CSV column name: {f.csv_column_name}")
            seen_csv.add(f.csv_column_name)

        # 4. Mapping ballot_field_id references
        mapped_ballot_ids: set[str] = set()
        for m in self.field_mappings:
            if m.ballot_field_id not in ballot_ids:
                errors.append(f"Mapping references unknown ballot field: {m.ballot_field_id}")
            mapped_ballot_ids.add(m.ballot_field_id)

            # 5. Template placeholder references
            for ref in _extract_placeholders(m.template):
                if ref not in voter_ids:
                    errors.append(
                        f"Template for ballot field '{m.ballot_field_id}' "
                        f"references unknown voter field: {ref}"
                    )

        # 6. Matchable fields must have a mapping
        for f in self.ballot_fields:
            if f.required_for_matching and f.match_weight > 0:
                if f.id not in mapped_ballot_ids:
                    errors.append(
                        f"Matchable ballot field '{f.id}' has no field mapping"
                    )

        # 7. Hash fields must reference existing voter reg fields
        for hf in self.hash_fields:
            if hf not in voter_ids:
                errors.append(f"Hash field references unknown voter reg field: {hf}")

        # 8. At least one matchable field
        if not self.matchable_fields():
            errors.append("Must have at least one matchable ballot field (required_for_matching=True, match_weight > 0)")

        # 9. Crop config ordering
        if self.crop_config.top_crop >= self.crop_config.bottom_crop:
            errors.append(
                f"Crop config: top_crop ({self.crop_config.top_crop}) must be < bottom_crop ({self.crop_config.bottom_crop})"
            )

        return errors
```

### Domain Service (pure function)

**File**: `app/domain/field_spec.py` (same file, co-located)

```python
NA_SENTINELS = {"N/A", "NA", "n/a", "na"}

def render_template(template: str, voter_row: dict[str, str]) -> str:
    """Pure domain service: render a mapping template, dropping empty placeholders.

    No I/O, no infrastructure. Testable without mocks.

    Sentinel values (N/A, NA, n/a, na) are treated as empty strings
    and dropped, avoiding "N/A" appearing in rendered ballot fields.
    """
    if not template:
        return ""

    placeholders = _extract_placeholders(template)
    result = template
    for field in placeholders:
        value = voter_row.get(field, "").strip()
        if value.upper() in NA_SENTINELS:
            value = ""
        result = result.replace(f"{{{field}}}", value)

    result = re.sub(r"\s+", " ", result).strip()
    result = re.sub(r",\s*$", "", result)
    result = re.sub(r"^\s*,\s*", "", result)
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r"\bApt\s*$", "", result).strip()
    return result

def _extract_placeholders(template: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", template)
```

### Persistence Contract (Protocol)

**File**: `app/persistence/contracts.py` (add to existing)

```python
@runtime_checkable
class FieldSpecRepository(Protocol):
    """Port: manages field spec persistence."""
    def find_by_region(self, region_id: UUID) -> RegionFieldSpecConfig | None: ...
    def find_by_region_key(self, region_key: str) -> RegionFieldSpecConfig | None: ...
    def save(self, spec: RegionFieldSpecConfig, region_id: UUID) -> RegionFieldSpecConfig: ...
    def upsert(self, region_key: str, spec: RegionFieldSpecConfig) -> None: ...
    def delete(self, region_id: UUID) -> bool: ...
    def list_regions(self) -> list[tuple[str, str, UUID]]: ...  # (key, name, id)
```

### Repository Implementation (adapter)

**File**: `app/repositories/field_spec_repo.py` (new)

Translates between domain `RegionFieldSpecConfig` and DB `RegionFieldSpecModel`. No domain logic here — only mapping.

```python
class FieldSpecRepositoryImpl:
    """Adapter: SQLModel-backed implementation of FieldSpecRepository."""

    def __init__(self, engine: ProvidesEngine):
        self._engine = engine

    def find_by_region(self, region_id: UUID) -> RegionFieldSpecConfig | None:
        with self._engine.create_session() as session:
            model = session.exec(
                select(RegionFieldSpecModel).where(
                    RegionFieldSpecModel.region_id == region_id
                )
            ).first()
            if model is None:
                return None
            return _to_domain(model)

    # ... save, delete similarly
```

### DB Model (persistence detail)

**File**: `app/data/database/model/region_field_spec.py` (new)

```python
class RegionFieldSpecModel(SQLModel, table=True):
    __tablename__ = "region_field_specs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    region_id: UUID = Field(foreign_key="regions.id", unique=True, index=True)
    name: str
    ballot_fields: list = Field(sa_column=Column(JSON))
    voter_reg_fields: list = Field(sa_column=Column(JSON))
    field_mappings: list = Field(sa_column=Column(JSON))
    hash_fields: list = Field(sa_column=Column(JSON))
    crop_config: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime
    updated_at: datetime
```

### Application Service (use case orchestrator)

**File**: `app/services/field_spec_service.py` (new)

Depends on domain types and Protocol interfaces only. No SQLModel imports.

```python
class FieldSpecService:
    """Application service: field spec use cases."""

    def __init__(self, repo: FieldSpecRepository):
        self._repo = repo

    def get_spec(self, region_id: UUID) -> RegionFieldSpecConfig:
        spec = self._repo.find_by_region(region_id)
        if spec is None:
            raise FieldSpecNotFoundError(region_id)
        return spec

    def map_voter_to_ballot(
        self, spec: RegionFieldSpecConfig, voter_data: dict[str, str]
    ) -> dict[str, str]:
        """Use case: transform voter reg row into ballot field values."""
        result = {}
        for mapping in spec.field_mappings:
            result[mapping.ballot_field_id] = render_template(
                mapping.template, voter_data
            )
        return result

    def validate_spec(self, spec: RegionFieldSpecConfig) -> list[str]:
        """Use case: verify spec integrity before saving."""
        errors = spec.validate_integrity()
        if not spec.ballot_fields:
            errors.append("Must have at least one ballot field")
        if not spec.voter_reg_fields:
            errors.append("Must have at least one voter reg field")
        return errors
```

### DC Default Spec

### Voter Data Adapter

`RegisteredVoter` stores data as nested JSON blobs: `name_data`, `address_data`, `other_field_data`. But `render_template` expects a flat `dict[str, str]` keyed by `voter_reg_field.id`.

**File**: `app/matching/voter_data_adapter.py` (new)

```python
def flatten_voter_data(
    voter: RegisteredVoter,
    voter_reg_fields: list[VoterRegField],
) -> dict[str, str]:
    """Flatten nested voter JSON blobs into a flat dict for render_template.

    Maps voter_reg_field.csv_column_name → voter_reg_field.id using
    the category to determine which blob to read from.
    """
    all_data: dict[str, str] = {}
    for field in voter_reg_fields:
        if field.category == "name" and voter.name_data:
            all_data[field.id] = str(voter.name_data.get(field.csv_column_name, ""))
        elif field.category == "address" and voter.address_data:
            all_data[field.id] = str(voter.address_data.get(field.csv_column_name, ""))
        elif voter.other_field_data:
            all_data[field.id] = str(voter.other_field_data.get(field.csv_column_name, ""))
    return all_data
```

### Category → Blob Mapping

When `VoterListService` parses CSV and creates/updates `RegisteredVoter`, fields must be grouped by `voter_reg_field.category` into the correct JSON blob:

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

### Region Auto-Creation during Spec Loading

**Problem:** `load_all_specs` calls `repo.upsert(region_key, spec)`, which inserts `RegionFieldSpecModel` with FK to `regions.id`. If no `Region` row exists for that `region_key`, the FK constraint fails.

**Fix:** The JSON5 spec includes `region_name` and `country_code` fields. During `upsert`, check if a `Region` row exists for the `region_key`. If not, create one:

```python
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

### Conflicting Key Schemas (Pre-Refactor)

Three code paths currently use different address key names:

| Code path | Address keys | File |
|-----------|-------------|------|
| `VoterListService.merge_voter_list()` | `street`, `city`, `state`, `zip` | `voter_list_service.py:104-109` |
| `MatchingService._build_voter_address()` | `street_number`, `street_name`, `street_type`, `street_dir_suffix` | `matching_service.py:274-280` |
| `worker.py` inline matching | `street`, `city`, `state`, `zip` | `worker.py:958-961` |

After spec refactor, all voter blob keys are normalized to use `voter_reg_field.id` values from the spec. `worker.py` duplicate matching is consolidated into `MatchingService`.

### compute_data_hash Expansion

**Problem:** Current `compute_data_hash` only searches `name_data` and `address_data`. After spec refactor, `hash_fields` can reference any `voter_reg_field.id` across all categories.

**Fix:** Merge all three blobs before computing hash:

```python
def compute_data_hash(self, name_data, address_data, other_field_data, hash_fields):
    all_fields = {**name_data, **address_data, **other_field_data}
    values = [str(all_fields.get(field, "")) for field in hash_fields]
    return hashlib.md5("|".join(values).encode()).hexdigest()
```

### Configurable Zipcode Pre-Filter

`MatchingService.pre_filter_voters` hardcodes `address_data["zip"]` for zipcode pre-filtering. After spec refactor, the field may differ per region.

**Options:**
- **(Recommended)** Add a `pre_filter_field` to `RegionFieldSpecConfig` specifying which field to use for pre-filtering
- Remove zipcode pre-filter entirely, rely on region-only filtering

### RegisteredVoter.full_name / is_matchable() Decision

`RegisteredVoter.full_name` and `is_matchable()` hardcode field keys (`first_name`, `last_name`). These remain **simplified defaults** for display/logging — they do NOT need to be spec-driven for this phase. Document with code comments. Future phase may add spec-aware display names.

### create_campaign Refactor

`CampaignManagementService._ensure_default_region()` hardcodes `region_key="DC"`. The `create_campaign` method accepts a `region` parameter but ignores it entirely. After refactor, `_ensure_default_region()` is replaced with a method that looks up the region by the provided `region_key`. If region not found, raise error.

### DI Wiring

**File**: `app/dependencies.py`

```python
def get_field_spec_service() -> Generator[FieldSpecService]:
    session = next(get_session())
    repo = FieldSpecRepositoryImpl(session)
    yield FieldSpecService(repo)
```

**File**: `tests/conftest.py` (approval test reporter)

```python
from approvaltests import set_default_reporter
from approvaltests.reporters.python_native_reporter import PythonNativeReporter

def pytest_configure(config):
    set_default_reporter(PythonNativeReporter())
```

### Model Registration for Alembic

Alembic autogenerate only discovers models imported in `model_imports.py` and registered in `data/models.py`. Add `RegionFieldSpecModel` to both:

```python
# model_imports.py
from app.data.database.model.region_field_spec import RegionFieldSpecModel

# data/models.py
from app.data.database.model.region_field_spec import RegionFieldSpecModel
# Add "RegionFieldSpecModel" to __all__ list
```

### Data Migration Strategy

#### Migration 1: region_schemas → region_field_specs

If production/dev databases have existing `region_schemas` rows, an Alembic migration:
1. Creates `region_field_specs` table (from G4)
2. Maps each `region_schemas` row → `region_field_specs` row (best-effort)
3. Validates migrated specs via `validate_integrity()`
4. Only drops `region_schemas` table after validation passes

#### Migration 2: RegisteredVoter JSON blob key remapping

Existing `RegisteredVoter` rows have old key names (`street`, `city`, `state`, `zip`) in `address_data`. After spec refactor, new voters get spec keys (`street_number`, `street_name`, `zip_code`).

Remapping: `street` → derive `street_number`/`street_name`/`street_type`/`street_dir_suffix` (best-effort split), `zip` → `zip_code`, etc.

#### Migration 3: rapidfuzz version pin

Pin major version in `pyproject.toml` to prevent non-deterministic approval test failures:

```toml
rapidfuzz = ">=3.9.0,<4.0.0"
```

### Demo Code

`backend/app/voter/voter_processor.py` and `backend/app/voter/voter_schema.py` are demo code that hardcodes DC columns. These are low priority and addressed in cleanup. `match_columns.py` has display constants only — deferred to future phase.

### DC Default Spec (Full)

```json
{
  "region_name": "District of Columbia",
  "country_code": "US",
  "ballot_fields": [
    {"id": "name",        "label": "Full Name",       "field_type": "text",    "required_for_matching": true,  "match_weight": 1.0},
    {"id": "address",     "label": "Address",          "field_type": "address", "required_for_matching": true,  "match_weight": 1.0},
    {"id": "ward",        "label": "Ward",             "field_type": "integer", "required_for_matching": false, "match_weight": 0.3},
    {"id": "date_signed", "label": "Date Signed",      "field_type": "date",    "required_for_matching": false, "match_weight": 0.0}
  ],
  "voter_reg_fields": [
    {"id": "last_name",              "csv_column_name": "Last_Name",              "data_type": "text",  "category": "name"},
    {"id": "first_name",             "csv_column_name": "First_Name",             "data_type": "text",  "category": "name"},
    {"id": "middle_name",            "csv_column_name": "Middle_Name",            "data_type": "text",  "category": "name"},
    {"id": "name_style",             "csv_column_name": "Name_Style",             "data_type": "text",  "category": "name"},
    {"id": "street_number",          "csv_column_name": "Street_Number",          "data_type": "text",  "category": "address"},
    {"id": "street_number_suffix",   "csv_column_name": "Street_Number_Suffix",   "data_type": "text",  "category": "address"},
    {"id": "street_name",            "csv_column_name": "Street_Name",            "data_type": "text",  "category": "address"},
    {"id": "street_type",            "csv_column_name": "Street_Type",            "data_type": "text",  "category": "address"},
    {"id": "street_dir_suffix",      "csv_column_name": "Street_Dir_Suffix",      "data_type": "text",  "category": "address"},
    {"id": "unit_type",              "csv_column_name": "Unit_Type",              "data_type": "text",  "category": "address"},
    {"id": "apartment_number",       "csv_column_name": "Apartment_Number",       "data_type": "text",  "category": "address"},
    {"id": "zip_code",               "csv_column_name": "Zip_Code",               "data_type": "text",  "category": "address"},
    {"id": "city_name",              "csv_column_name": "City_Name",              "data_type": "text",  "category": "address"},
    {"id": "registration_date",      "csv_column_name": "Registration_Date",      "data_type": "date",  "category": "registration"},
    {"id": "party",                  "csv_column_name": "Party",                  "data_type": "text",  "category": "registration"},
    {"id": "precinct",               "csv_column_name": "Precinct",              "data_type": "text",  "category": "geography"},
    {"id": "smd",                    "csv_column_name": "SMD",                    "data_type": "text",  "category": "geography"},
    {"id": "anc",                    "csv_column_name": "ANC",                    "data_type": "text",  "category": "geography"},
    {"id": "ward",                   "csv_column_name": "WARD",                   "data_type": "integer","category": "geography"},
    {"id": "voter_status",           "csv_column_name": "Voter Status",           "data_type": "text",  "category": "registration"},
    {"id": "is_us_citizen",          "csv_column_name": "IsUSCitizen",            "data_type": "text",  "category": "registration"}
  ],
  "field_mappings": [
    {"ballot_field_id": "name",    "template": "{first_name} {middle_name} {last_name}"},
    {"ballot_field_id": "address", "template": "{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"},
    {"ballot_field_id": "ward",    "template": "{ward}"},
    {"ballot_field_id": "date_signed", "template": ""}
  ],
  "hash_fields": ["last_name", "first_name", "street_number", "street_name", "zip_code"],
  "crop_config": {
    "top_crop": 0.385,
    "bottom_crop": 0.725,
    "base_threshold": 85
  }
}
```

---

## Implementation Phases (TDD, Outside-In)

Each phase lists: tests to write FIRST (RED), then implementation (GREEN), then cleanup (REFACTOR).

### Phase 1: Domain Layer — Pure Value Objects + Template Renderer

**This phase has ZERO infrastructure dependencies. No DB, no SQLModel, no FastAPI.**

#### RED (write these tests first)

**File**: `tests/unit/domain/test_field_spec.py`

```python
class TestBallotField:
    def test_create_ballot_field(self): ...
    def test_ballot_field_is_frozen(self): ...
    def test_match_weight_must_be_non_negative(self): ...

class TestVoterRegField:
    def test_create_voter_reg_field(self): ...
    def test_invalid_category_rejected(self): ...

class TestFieldMapping:
    def test_create_field_mapping(self): ...

class TestCropConfig:
    def test_create_crop_config(self): ...
    def test_crop_values_must_be_0_to_1(self): ...
    def test_threshold_must_be_0_to_255(self): ...

class TestRegionFieldSpecConfig:
    def test_create_full_spec(self): ...
    def test_get_mapping_for_existing_field(self): ...
    def test_get_mapping_for_missing_field_returns_none(self): ...
    def test_matchable_fields_excludes_zero_weight(self): ...
    def test_total_match_weight(self): ...
    def test_validate_integrity_catches_bad_ballot_ref(self): ...
    def test_validate_integrity_catches_bad_voter_ref(self): ...
    def test_validate_integrity_passes_for_valid_spec(self): ...
```

**File**: `tests/unit/domain/test_template_renderer.py`

```python
class TestRenderTemplate:
    """BDD: Template rendering scenarios."""

    # Scenario: simple name concatenation
    def test_concatenates_fields(self): ...

    # Scenario: empty middle name dropped
    def test_drops_empty_placeholder(self): ...

    # Scenario: address with no apartment
    def test_address_without_apartment(self): ...

    # Scenario: address with apartment
    def test_address_with_apartment(self): ...

    # Scenario: completely empty template
    def test_empty_template_returns_empty(self): ...

    # Scenario: all fields empty
    def test_all_fields_empty_returns_empty(self): ...

    # Scenario: single field mapping (ward)
    def test_single_field(self): ...

    # Scenario: missing field in voter data
    def test_missing_field_treated_as_empty(self): ...

    # Scenario: extra whitespace collapsed
    def test_collapses_multiple_spaces(self): ...

    # Scenario: special characters in values
    def test_handles_special_characters(self): ...
```

**File**: `tests/unit/domain/test_template_renderer_approval.py` (approval test)

```python
from approvaltests import verify, verify_all

class TestTemplateRendererApproval:
    """Approval test: golden master for all DC address/name rendering variants.

    Uses verify_all for collection-based rendering and verify for full mapping output.
    Per ApprovalTests convention: .approved. files committed to git.
    """

    def test_dc_address_variants(self):
        """Render all DC address patterns from sample voter data."""
        template = "{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"
        dc_addresses = {
            "standard NE": {"street_number": "730", ...},
            "with unit SE": {"street_number": "1300", ..., "apartment_number": "UNIT 715"},
            ...
        }
        verify_all("DC address template renders", dc_addresses.items(),
                   lambda pair: f"{pair[0]}: {pair[1]} => {render_template(template, pair[1])!r}")

    def test_dc_name_variants(self):
        """Render all DC name patterns (with/without middle, suffix, etc.)."""
        ...

    def test_dc_full_ballot_mapping(self):
        """End-to-end: voter row → all ballot fields for DC spec."""
        # Uses verify() with multi-line output
        ...
```

**File**: `tests/unit/domain/test_dc_spec_approval.py` (approval test)

```python
from approvaltests import verify

class TestDcDefaultSpecApproval:
    """Approval test: verify DC seed spec JSON hasn't drifted."""

    def test_dc_seed_spec(self):
        """Snapshot the full DC spec as pretty-printed JSON."""
        spec = dc_default_spec()
        verify(spec.model_dump_json(indent=2))
```

#### GREEN (implement)

- `app/domain/field_spec.py` — all value objects, `render_template`, `_extract_placeholders`
- `app/domain/__init__.py` — export new types

#### REFACTOR

- Extract validation helpers if `validate_integrity` grows
- Consider `@cached_property` for `matchable_fields` if called frequently

---

### Phase 2: Persistence Layer — Repository + DB Model

#### RED

**File**: `tests/unit/repositories/test_field_spec_repo.py`

```python
class TestFieldSpecRepository:
    """Tests using in-memory SQLite (integration-level but fast)."""

    # Scenario: save and retrieve spec for a region
    def test_save_and_find_by_region(self): ...

    # Scenario: find returns None for unknown region
    def test_find_returns_none_for_unknown_region(self): ...

    # Scenario: save overwrites existing spec
    def test_save_updates_existing(self): ...

    # Scenario: delete removes spec
    def test_delete_removes_spec(self): ...

    # Scenario: delete returns False for missing spec
    def test_delete_returns_false_for_missing(self): ...

    # Scenario: domain round-trip preserves all fields
    def test_round_trip_preserves_all_fields(self): ...
```

#### GREEN

- `app/data/database/model/region_field_spec.py` — SQLModel table
- `app/repositories/field_spec_repo.py` — repository implementation with `_to_domain` / `_to_model`
- `app/persistence/contracts.py` — add `FieldSpecRepository` Protocol
- Alembic migration: create `region_field_specs`, drop `region_schemas` (no data seed — specs loaded from `app/regions/*.json` at startup)

#### REFACTOR

- Extract `_to_domain` / `_to_model` into a separate mapper if complex

---

### Phase 3: Application Service — Use Cases

#### RED

**File**: `tests/unit/services/test_field_spec_service.py`

```python
class TestFieldSpecService:
    """Tests using mock repository (unit-level, no DB)."""

    # Scenario: get spec for region with existing spec
    def test_get_spec_returns_spec(self): ...

    # Scenario: get spec for region without spec raises error
    def test_get_spec_raises_when_not_found(self): ...

    # Scenario: map voter data to ballot fields
    def test_map_voter_to_ballot(self): ...

    # Scenario: map with partial voter data
    def test_map_voter_to_ballot_partial_data(self): ...

    # Scenario: validate good spec returns empty errors
    def test_validate_good_spec(self): ...

    # Scenario: validate spec with bad references returns errors
    def test_validate_spec_with_bad_references(self): ...

    # Scenario: validate spec with no ballot fields returns error
    def test_validate_spec_empty_ballot_fields(self): ...
```

#### GREEN

- `app/services/field_spec_service.py` — `FieldSpecService` class
- `app/domain/field_spec.py` — add `FieldSpecNotFoundError` domain exception

#### REFACTOR

- Consider extracting `map_voter_to_ballot` to its own service if it grows

---

### Phase 4: Refactor Existing Services

#### CRITICAL: Create approval baseline BEFORE refactoring

Write the matching score approval test **while the current hardcoded implementation is still in place**. This captures the current behavior as the approved baseline. Then refactor, and any score changes are flagged.

#### RED (write tests for new behavior before changing existing code)

**File**: `tests/unit/services/test_matching_regression_approval.py` (approval test — write FIRST)

```python
from approvaltests import verify

class TestMatchingRegressionApproval:
    """Characterization test: capture current matching scores BEFORE refactoring.

    1. Run with current hardcoded MatchingService → approve baseline
    2. Refactor MatchingService to use spec-driven matching
    3. If scores change, diff tool shows exactly what changed
    """

    def test_dc_matching_score_matrix(self):
        """Golden master: current similarity scores for known OCR vs voter pairs."""
        ...
```

**File**: `tests/unit/services/test_voter_list_service.py` (extend existing)

```python
class TestVoterListServiceWithFieldSpec:
    """BDD: voter list parsing using field spec."""

    # Scenario: parse DC CSV using voter reg field spec
    def test_parse_csv_with_dc_spec(self): ...

    # Scenario: merge voters using spec-driven hash fields
    def test_merge_uses_spec_hash_fields(self): ...

    # Scenario: hash computation uses spec-defined fields
    def test_hash_uses_spec_fields(self): ...
```

**File**: `tests/unit/services/test_matching_service.py` (extend existing)

```python
class TestMatchingServiceWithFieldSpec:
    """BDD: spec-driven matching replaces hardcoded fields."""

    # Scenario: matching uses dynamic ballot field weights
    def test_similarity_uses_spec_weights(self): ...

    # Scenario: matching builds voter name from spec template
    def test_builds_voter_name_from_spec(self): ...

    # Scenario: matching builds voter address from spec template
    def test_builds_voter_address_from_spec(self): ...

    # Scenario: ward contributes at reduced weight
    def test_ward_has_reduced_weight(self): ...
```

#### GREEN

- Refactor `VoterListService` to accept `FieldSpecService` and use spec for parsing
- Refactor `MatchingService` to accept `RegionFieldSpecConfig` and use `render_template`
- Update `ocr_config.py` `get_current_crop_config()` to load from spec

#### REFACTOR

- Remove `WashingtonDCRegisteredVoter` and `DcRegisteredVoterSummarise` models
- Remove hardcoded field keys from `MatchingService`
- Remove `RegionSchema` model
- Clean up `MatchColumns` to be spec-driven

---

### Phase 5: Region Selector (Frontend + API)

#### RED

**File**: `tests/integration/api/test_regions.py` (new)

```python
class TestRegionsAPI:
    # Scenario: list available regions
    def test_list_regions_returns_dc(self): ...

    # Scenario: create campaign with region UUID
    def test_create_campaign_with_region_id(self): ...
```

**File**: `frontend/tests/e2e/campaigns.spec.ts` (extend existing)

```typescript
// Scenario: campaign create shows region dropdown
test('create campaign modal has region dropdown', ...)

// Scenario: region dropdown defaults to DC
test('region dropdown defaults to DC', ...)
```

#### GREEN

- `app/routers/region_router.py` — add `GET /regions` list endpoint
- `frontend/src/routes/(app)/workspace/campaigns/+page.svelte` — `<select>` dropdown
- `frontend/src/lib/stores/campaigns.ts` — send region_id

#### REFACTOR

- Update generated API client types

---

### Phase 6: Extensibility (future)

- Region setup wizard / field spec configuration UI
- Import/export specs as JSON
- Per-campaign spec override (inherit from region, customize)

---

## Dependency Flow Summary

```
app/domain/field_spec.py          ← NO imports from app/data, app/services, app/routers
app/persistence/contracts.py      ← imports from app/domain only (Protocol definitions)
app/repositories/field_spec_repo  ← imports from app/domain + app/data (adapter)
app/matching/voter_data_adapter   ← imports from app/domain (pure function)
app/services/field_spec_service   ← imports from app/domain + app/persistence/contracts
app/services/voter_list_service   ← imports from app/domain + app/services/field_spec_service
app/matching/matching_service     ← imports from app/domain
app/services/campaign_management  ← uses field_spec_service for region lookup
app/jobs/worker.py                ← delegates to MatchingService (no inline matching)
app/routers/*                     ← imports from app/services + app/api_models
app/dependencies.py               ← wires FieldSpecService into FastAPI DI
app/startup.py                    ← calls _spec_loader() after DB init
```

---

## Files Changed (estimated)

| Layer | File | Action | Test file |
|-------|------|--------|-----------|
| Domain | `app/domain/field_spec.py` (new) | Value objects + renderer + `FieldSpecNotFoundError` | `tests/unit/domain/test_field_spec.py` (new) |
| Domain | `tests/unit/domain/test_template_renderer.py` (new) | BDD scenarios | — |
| Domain | `tests/unit/domain/test_template_renderer_approval.py` (new) | Approval: template golden masters | `.approved.txt` files |
| Domain | `tests/unit/domain/test_dc_spec_approval.py` (new) | Approval: DC spec snapshot | `.approved.json` files |
| Domain | `app/domain/__init__.py` | Export new types | — |
| Contract | `app/persistence/contracts.py` | Add `FieldSpecRepository` Protocol (with `find_by_region_key`, `upsert`, `list_regions`) | — |
| Adapter | `app/repositories/field_spec_repo.py` (new) | SQLModel implementation | `tests/unit/repositories/test_field_spec_repo.py` (new) |
| Persistence | `app/data/database/model/region_field_spec.py` (new) | DB table model | — |
| Persistence | `app/persistence/engines/model_imports.py` | Register `RegionFieldSpecModel` for Alembic | — |
| Persistence | `app/data/models.py` | Register `RegionFieldSpecModel` import + `__all__` | — |
| Migration | `alembic/versions/...` (new) | Create `region_field_specs` table | — |
| Migration | `alembic/versions/...` (new) | Data migration: `region_schemas` → `region_field_specs` | — |
| Migration | `alembic/versions/...` (new) | Data migration: voter blob key remapping (`zip` → `zip_code`, etc.) | — |
| Config | `app/regions/dc.json5` (new) | DC source spec file (JSON5 with `region_name`, `country_code`) | Loaded by `test_field_spec_service.py` |
| Config | `app/regions/README.md` (new) | How to add new region spec | — |
| Dependency | `pyproject.toml` | Add `json5` runtime dep; `rapidfuzz` version pin | — |
| Remove | `app/data/database/model/region_schema.py` | Delete entire file | Delete `tests/unit/models/test_region_schema.py` |
| Remove | `WashingtonDCRegisteredVoter` + `DcRegisteredVoterSummarise` from `schema.py` | Delete classes (file stays) | — |
| Remove | `app/ocr/ocr_config.py` hardcoded defaults | Load from spec | — |
| Service | `app/services/field_spec_service.py` (new) | Use cases + `load_all_specs` | `tests/unit/services/test_field_spec_service.py` (new) |
| Service | `app/services/field_spec_loading.py` (new) | Spec loading tests | `tests/unit/services/test_field_spec_loading.py` (new) |
| Service | `app/services/voter_list_service.py` | Refactor to use spec (category→blob mapping, `compute_data_hash` expansion) | Extend `test_voter_list_service.py` |
| Service | `app/services/campaign_management_service.py` | Replace `_ensure_default_region()` with region lookup | — |
| Matching | `app/matching/voter_data_adapter.py` (new) | Flatten voter JSON blobs for `render_template` | Tests in `test_voter_data_adapter.py` |
| Matching | `app/matching/matching_service.py` | Refactor to dynamic spec-driven matching | Extend `test_matching_service.py` |
| Matching | `app/jobs/worker.py` | Consolidate duplicate matching into `MatchingService` | — |
| Approval | `tests/unit/services/test_matching_regression_approval.py` (new) | Approval: score matrix baseline | `.approved.txt` |
| DI | `app/dependencies.py` | Add `get_field_spec_service` provider | — |
| DI | `tests/conftest.py` | Configure approval test reporter | — |
| Startup | `app/startup.py` | Add `_spec_loader()` call after DB init | — |
| API | `app/routers/region_router.py` | Add `GET /regions` | `tests/integration/api/test_regions.py` (new) |
| Frontend | `+page.svelte` (campaigns) | Region dropdown | E2E tests |
| Frontend | `campaigns.ts` store | Send region_id | Unit tests |
| Config | `pyproject.toml` | Add `approvaltests` + `pytest-approvaltests` dev deps | — |
| Editor | `.vscode/settings.json` (new) | VS Code settings (parity with Zed) | — |
| Editor | `.vscode/extensions.json` (new) | Recommended extensions | — |
| Editor | `.vscode/launch.json` (new) | Debug configs | — |
| Editor | `.vscode/tasks.json` (new) | Build/test tasks | — |
| Editor | `.zed/settings.json` | Add JSON5 language config | — |
| Editor | `.zed/tasks.json` | Add spec validation task | — |
| Note | `app/voter/voter_processor.py`, `app/voter/voter_schema.py` | Demo code — low priority, addressed in cleanup | — |
| Note | `app/matching/match_columns.py` | Display constants only — deferred to future phase | — |
| Docs | `docs/architecture/decisions/0006-spec-driven-field-configuration.md` (new) | ADR: why JSON5 source files, hexagonal architecture, DDD aggregates | — |
| Docs | `docs/architecture/decisions/0007-feature-flag-lifecycle-framework.md` (new) | ADR: transitional vs permanent flags, CI hygiene | — |
| Docs | `docs/architecture/decisions/0008-template-based-field-rendering.md` (new) | ADR: templates over code, sentinel convention | — |
| Docs | `docs/development/testing.md` (new or section) | How-To: approval testing workflow in this project | — |
| Docs | `docs/development/field-spec-schema.md` (new) | Reference: JSON5 spec file format and validation rules | — |
| Docs | `docs/architecture/matching-process.md` (new) | Explanation: spec-driven matching pipeline end-to-end | — |
| Docs | `docs/architecture/c4-components.md` | Update: add FieldSpecService, VoterDataAdapter, FieldSpecRepo, Domain Layer, Regional Config | — |
| Docs | `docs/development/adding-a-region.md` (new) | Tutorial: step-by-step guide for contributors | — |
| Docs | `docs/development/README.md` | Update: project structure, doc links | — |
| Docs | `docs/DOCUMENTATION_STRATEGY.md` | Update: mark Phase 2 doc tasks complete | — |
| Docs | `docs/architecture/README.md` | Update: add ADR-0006/0007/0008 to key decisions table | — |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Template rendering edge cases (empty fields, special chars, N/A values) | BDD scenarios + N/A sentinel handling cover all DC address patterns |
| Migration from `region_schemas` to `region_field_specs` with existing data | Data migration in Alembic; test against dev.db; validate migrated specs |
| Matching quality regression from dynamic weighting | Approval test baseline before refactoring; A/B comparison |
| Performance: loading spec on every match call | Cache spec per region in service instance |
| Domain model drift from DB model | `_to_domain`/`_to_model` mappers tested via round-trip |
| 3 conflicting address key schemas across codebase | G7.7 consolidates `worker.py`; G8 normalizes to spec keys; data migration remaps old blobs |
| `rapidfuzz` version changes causing non-deterministic approval test failures | Pin major version in `pyproject.toml` |
| FK failure if `Region` row doesn't exist at spec load time | Auto-create `Region` rows during `load_all_specs` using `region_name`/`country_code` from spec |
| `Region.region_key` casing mismatch | Normalization convention: all keys uppercase; `find_by_region_key` normalizes input |
| `compute_data_hash` missing geography-category fields | Refactored to merge all three blobs before computing hash |
| `create_campaign` ignoring region param | Replace `_ensure_default_region()` with spec-aware region lookup |

---

## Editor Configuration Review

### Current State

| Editor | Config exists? | Files |
|--------|---------------|-------|
| **Zed** | Yes | `.zed/settings.json`, `.zed/tasks.json`, `.zed/debug.json` |
| **VS Code** | No | `.gitignore` allows `.vscode/{settings,extensions,launch,tasks}.json` but none exist |
| **Cursor** | Blocked | `.gitignore` excludes `.cursor/` |

### Changes Needed for This Feature

#### Zed (`.zed/settings.json`)

Current config is comprehensive. Add JSON5 file association:

```jsonc
// ADD to existing languages block:
"JSON5": {
    "formatter": "prettier",
    "format_on_save": "on"
},

// ADD to file_patterns (if Zed supports it):
"file_associations": {
    "**/app/regions/*.json5": "JSON5"
}
```

Also add a task for spec validation:

```jsonc
// ADD to .zed/tasks.json:
{
    "label": "Backend: Validate Region Specs",
    "command": "uv run python -c \"from app.services.field_spec_service import FieldSpecService; from app.repositories.field_spec_repo import FieldSpecRepositoryImpl; from app.persistence.engines.sqlite_engine import SqliteEngine; import json5, sys; svc = FieldSpecService(FieldSpecRepositoryImpl(SqliteEngine())); count, errors = svc.load_all_specs(); [print(e) for e in errors]; sys.exit(1 if errors else 0)\"",
    "cwd": "$ZED_WORKTREE_ROOT/backend"
}
```

#### VS Code (`.vscode/` — needs creation)

Create the following files (all allowed by `.gitignore`):

**`.vscode/extensions.json`:**
```json
{
    "recommendations": [
        "dbaeumer.vscode-eslint",
        "svelte.svelte-vscode",
        "ms-python.python",
        "ms-python.vscode-pyright",
        "charliermarsh.ruff",
        "bradlc.vscode-tailwindcss",
        "eriklynd.json-tools"
    ]
}
```

**`.vscode/settings.json`:**
```jsonc
{
    // Python
    "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },
    "ruff.importStrategy": "fromEnvironment",
    "basedpyright.analysis.include": ["backend/app"],
    "basedpyright.analysis.typeCheckingMode": "strict",

    // Svelte/Frontend
    "[svelte]": {
        "editor.defaultFormatter": "svelte.svelte-vscode"
    },
    "[typescript]": {
        "editor.defaultFormatter": "dbaeumer.vscode-eslint"
    },
    "tailwindCSS.includeLanguages": { "svelte": "html" },

    // JSON5 spec files
    "[json5]": {
        "editor.defaultFormatter": "eriklynd.json-tools",
        "editor.formatOnSave": true
    },
    "files.associations": {
        "**/app/regions/*.json5": "json5"
    },

    // Approval tests
    "files.associations": {
        "**/*.approved.*": "plaintext"
    }
}
```

**`.vscode/launch.json`:**
```json
[
    {
        "name": "Backend: FastAPI (Local)",
        "type": "debugpy",
        "request": "launch",
        "module": "uvicorn",
        "args": ["app.api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"],
        "cwd": "${workspaceFolder}/backend",
        "env": { "ENV": "local" }
    },
    {
        "name": "Backend: Run Tests",
        "type": "debugpy",
        "request": "launch",
        "module": "pytest",
        "args": ["tests/", "-v", "--tb=short"],
        "cwd": "${workspaceFolder}/backend"
    },
    {
        "name": "Backend: Validate Region Specs",
        "type": "debugpy",
        "request": "launch",
        "module": "pytest",
        "args": ["tests/unit/services/test_field_spec_service.py::TestFieldSpecLoading", "-v"],
        "cwd": "${workspaceFolder}/backend"
    }
]
```

**`.vscode/tasks.json`:**
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Backend: Run Server (Local)",
            "type": "shell",
            "command": "uv run main.py --env local",
            "options": { "cwd": "${workspaceFolder}/backend" },
            "group": "build",
            "problemMatcher": []
        },
        {
            "label": "Backend: Run Tests",
            "type": "shell",
            "command": "uv run pytest tests/ -v",
            "options": { "cwd": "${workspaceFolder}/backend" },
            "group": "test"
        },
        {
            "label": "Backend: Type Check",
            "type": "shell",
            "command": "uv run basedpyright app/",
            "options": { "cwd": "${workspaceFolder}/backend" }
        },
        {
            "label": "Backend: Lint",
            "type": "shell",
            "command": "uv run ruff check app/",
            "options": { "cwd": "${workspaceFolder}/backend" }
        },
        {
            "label": "Frontend: Dev Server",
            "type": "shell",
            "command": "bun run dev",
            "options": { "cwd": "${workspaceFolder}/frontend" },
            "isBackground": true,
            "group": "build"
        },
        {
            "label": "Frontend: Run Tests",
            "type": "shell",
            "command": "bun run test:unit",
            "options": { "cwd": "${workspaceFolder}/frontend" },
            "group": "test"
        },
        {
            "label": "Frontend: Type Check",
            "type": "shell",
            "command": "bun run check",
            "options": { "cwd": "${workspaceFolder}/frontend" }
        }
    ]
}
```

### Implementation Phase

Editor configs should be created/updated as part of **Phase 1** (foundation) so they're in place when developers start working on the feature. Specifically:

1. **Create** `.vscode/{settings,extensions,launch,tasks}.json` — parity with existing Zed config
2. **Update** `.zed/settings.json` — add JSON5 language association
3. **Update** `.zed/tasks.json` — add spec validation task
4. **No changes** to `.gitignore` — already allows these files
