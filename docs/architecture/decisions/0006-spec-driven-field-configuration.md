# ADR-0006: Spec-Driven Field Configuration

## Status

Accepted

## Context

Votecatcher handles voter registration data from different US regions (currently DC). Each region has different CSV column names, ballot field structures, matching weights, and hash fields. The current implementation hardcodes DC-specific field names, column mappings, and matching logic across multiple files (`MatchingService`, `VoterListService`, `worker.py`, `RegionSchema`).

Adding a new region (e.g., Maryland) would require duplicating and modifying hardcoded logic in at least 5 files with 3 conflicting key schemas for address fields alone.

## Decision

Replace hardcoded region-specific field handling with a **spec-driven system** loaded from JSON5 source files.

### Architecture

- **JSON5 source files** in `app/regions/` define per-region field specs (e.g., `dc.json5`)
- **Pure Pydantic domain layer** (`app/domain/field_spec.py`) — no DB or framework imports
- **Hexagonal outside-in**: domain → services → adapters dependency direction
- **DDD aggregate root** (`RegionFieldSpecConfig`) with value objects (`BallotField`, `VoterRegField`, `FieldMapping`, `CropConfig`)

### Why JSON5 over Alembic migrations

Specs are configuration, not user data. JSON5 files are PR-reviewable, diffable, and version-controlled. Per-region Alembic migrations would conflate schema changes with configuration data.

### Why pure Pydantic domain layer

The domain types have zero infrastructure dependencies. They validate at construction time, support `model_validate()` for deserialization, and can be tested in complete isolation.

## Consequences

- Each new region requires only a new `.json5` file — no code changes
- Spec files must pass `validate_integrity()` with 9+ validation rules
- Feature flags guard incremental rollout across 10 gates (G0–G10)
- After G10, old `RegionSchema`, `WashingtonDCRegisteredVoter`, and hardcoded paths are removed

## References

- Spec document: `plans/configurable-field-specs.md`
- Implementation plan: `plans/configurable-field-specs-plan.md`
