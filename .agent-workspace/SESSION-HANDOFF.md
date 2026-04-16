# Session Handoff — Smart Prediction Truncation

> **You are a fresh agent picking up this work. Read this file first.**

## Branch

**`feat/smart-prediction-truncation`** — from `main` (`57d1a11`). Uncommitted, unpushed.

## What Was Done

Replaced hard `[:5]` prediction slice with adaptive score-based truncation.

### New Files
```
backend/app/services/prediction_truncation.py              (pure function)
backend/tests/unit/services/test_prediction_truncation.py  (25 tests)
```

### Changed Files
```
backend/app/services/campaign_query_service.py:170    ([:5] → truncate_predictions)
backend/app/services/results_query_service.py:152     ([:5] → truncate_predictions)
frontend/src/lib/stores/campaign-results.ts:179       (removed .slice(0, 5))
```

### Algorithm
```python
truncate_predictions(predictions, *, max_predictions=5, relative_threshold=0.5,
                     absolute_floor=0.1, gap_ratio=2.0)
```

1. **Sort** descending by similarity_score (defensive)
2. **Max cap** at `max_predictions`
3. **Absolute floor** — drop below `absolute_floor`
4. **Relative threshold** — drop below `top_score * relative_threshold`
5. **Gap detection** — truncate at first `prev/curr > gap_ratio`

Invariant: always returns ≥1 prediction. Pure function — no side effects.

78 tests pass, 0 regressions. VDD adversarial review done.

## Remaining Steps

1. Commit changes
2. Push branch, open PR
3. Bump version to `1.0.0-alpha.5` (`just version-set 1.0.0-alpha.5`), verify both files, commit
4. Merge PR → CI auto-tags release

## Entry Coordinates Note

Demo and DC use the same ballot sheet — hardcoded constants in `entry_coordinates.py` are valid for both.

**Future regions:** `_HEADER_FRAC`, `_STRIDE_FRAC`, `_BOX_FRAC` are ballot-layout-dependent. Extend `CropConfig` in `app/domain/field_spec.py` to carry `header_frac`, `stride_frac`, `box_frac` per region. Then `compute_entry_coordinates` reads from spec.

## Open Issues

| Issue | Description |
|-------|-------------|
| #61 | Edge/line detection for entry boundary calibration |
| #62 | Analyze historic CI/CD failures for common patterns |

## Architecture Reminders

Two parallel results endpoints — both must be updated together:
```
/api/jobs/{job_id}/results           → ResultsQueryService
/api/campaigns/{campaign_id}/results → CampaignQueryService
```

## Version

Current: `1.0.0-alpha.4`. Bump to `1.0.0-alpha.5` before merge. CI auto-tags on main push.
