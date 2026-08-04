# ADR-0011: Extract API Response Contracts

## Status

Accepted

## Date

2026-07-22

## Crosslink

L3

## Context

VoteCatcher's backend had four production import cycles between router and service modules:

1. `campaign_router` ↔ `campaign_management_service`
2. `campaign_router` ↔ `campaign_query_service`
3. `job_router` ↔ `job_query_service`
4. `results_router` ↔ `results_query_service`

These cycles existed because both routers and services imported Pydantic response models that lived in the router modules. ADR-0010's no-cycle architecture rule cannot exempt cycles, so the cycles had to be broken before the rule could be enforced.

## Decision

Create `backend/app/responses/` as the canonical home for Pydantic response models consumed by both routers and services.

- Move campaign, job, and results response contracts out of router modules into `app/responses/{campaign,jobs,results}.py`.
- Routers import and re-export the shared contracts so existing direct router imports (`from app.routers.job_router import JobResponse`) continue to resolve.
- Services import response contracts from `app.responses`, never from `app.routers`.
- Preserve JSON field names, aliases, defaults, and endpoint behavior. Do not consolidate near-duplicate response models in this change.

## Verification

- `backend/tests/architecture/test_response_contracts.py` guards that routers re-export the same class objects and that field names, aliases, and defaults match the canonical models.
- `backend/tests/architecture/test_dependency_boundaries.py::test_services_do_not_depend_on_routers` enforces the one-directional service→responses dependency.
- The cycle rule (`test_production_code_has_no_import_cycles`) passes after extraction.

## Consequences

### Positive

- Eliminates four router↔service import cycles, enabling ADR-0010's no-cycle enforcement.
- Response models have a single canonical location, reducing duplication risk.
- Services no longer depend on HTTP adapter modules.

### Negative

- Two import paths exist for the same model (`app.responses.jobs.JobResponse` and `app.routers.job_router.JobResponse`). The router path is a re-export kept for backward compatibility.

### Neutral

- Response models are not consolidated or deduplicated; near-duplicate models (e.g., `CampaignResultResponse` vs `ResultResponse`) are preserved for separate refactoring.

## Alternatives Considered

1. **Exempt the cycles**
   - Pros: No code changes needed.
   - Cons: ADR-0010 explicitly forbids cycle exemptions; cycles hide dependency direction and prevent isolated testing.
   - Why not chosen: Cycles are non-exemptible per the approved architecture policy.

2. **Move models into services instead of a separate module**
   - Pros: Fewer modules.
   - Cons: Services would own transport-layer concerns; routers would import from services, inverting the dependency direction.
   - Why not chosen: Response models are shared contracts, not service-owned policy. A neutral `app/responses/` module keeps the dependency direction correct.

## References

- [ADR-0010: Adopt Architecture Fitness Tests](./0010-adopt-architecture-fitness-tests.md)
- `docs/agents/architecture-testing.md`
