# Prediction Truncation

This document describes the adaptive score-based truncation algorithm that
filters match predictions shown to users. It replaced a hard `[:5]` slice with
a multi-stage filter that drops low-quality predictions while preserving
genuinely ambiguous candidates.

## Problem Statement

The matching engine returns up to 5 predictions per petition entry, sorted by
`similarity_score`. Without filtering, a perfect match (score 1.0) followed by
four noise matches (score 0.55) is displayed identically to five plausible
candidates clustered at 0.65. This is misleading — the noise predictions
carry no informational value and clutter the UI.

### Source

`app/services/prediction_truncation.py` — pure function, no I/O, no DB, no
side effects.

### Call Sites

Two parallel results endpoints invoke the function (both must be updated
together for any signature changes):

```
/api/jobs/{job_id}/results           → ResultsQueryService:153
/api/campaigns/{campaign_id}/results → CampaignQueryService:171
```

### Test Suite

`tests/unit/services/test_prediction_truncation.py` — 25 BDD-style tests.

> **Sync check:** Run `uv run pytest tests/unit/services/test_prediction_truncation.py -v`
> from `backend/` to verify all tests pass after any parameter changes.

## Algorithm

```
truncate_predictions(predictions, *, max_predictions=5,
                     relative_threshold=0.5, absolute_floor=0.1,
                     gap_ratio=1.4) → list[Scored]
```

Four filters applied in sequence. The algorithm always returns ≥1 prediction
(unless input is empty). Each filter can be independently disabled by setting
its parameter to an extreme value (see [Disabling Filters](#disabling-filters)).

### Step 1: Sort and Cap

```
sorted_preds = sort(predictions, by=score, descending)
capped = sorted_preds[:max_predictions]
```

Defensive sort (input may not be pre-sorted) followed by a hard ceiling. The
default `max_predictions=5` matches the previous `[:5]` behavior as a safe
upper bound.

### Step 2: Absolute Floor

```
above_floor = [p for p in capped if p.score >= absolute_floor]
```

Removes predictions below a fixed minimum score. Default `absolute_floor=0.1`
eliminates near-zero matches while preserving everything above 10% similarity.
If all predictions fall below the floor, the top prediction is retained
(invariant: always ≥1).

### Step 3: Relative Threshold

```
min_score = top_score × relative_threshold
above_relative = [p for p in above_floor if p.score >= min_score]
```

Drops predictions that fall below a proportion of the best score. Default
`relative_threshold=0.5` means: keep only predictions scoring at least 50% of
the top match. For a top score of 1.0, this cuts at 0.5; for a top score of
0.6, this cuts at 0.3. This adapts to the score distribution rather than using
a fixed cutoff.

If all predictions fall below the relative threshold, the top prediction is
retained (invariant).

### Step 4: Gap Detection

```
for each adjacent pair (prev, curr):
    if prev / curr > gap_ratio:
        truncate at curr
```

Identifies a score "cliff" — a sudden drop between adjacent predictions that
indicates a qualitative boundary between viable and non-viable candidates.
Default `gap_ratio=1.4` means: truncate if a prediction is more than 40% worse
than its predecessor.

**Why ratio rather than difference?** A drop from 0.80→0.50 (Δ0.30, ratio 1.6)
is more significant than 0.40→0.30 (Δ0.10, ratio 1.33), even though the second
drop represents a larger relative change. The ratio captures the multiplicative
structure of similarity scores — scores are proportional measures, so
multiplicative comparisons are more appropriate than additive ones.<sup>[1](#f1)</sup>

### Invariants

| Invariant | Guarantee |
|-----------|-----------|
| Empty input → empty output | No predictions generated from nothing |
| Non-empty input → ≥1 output | User always sees at least one candidate |
| Output sorted descending | No re-sorting needed by caller |
| Pure function | No side effects, deterministic for same input |

### Filter Pipeline Visualization

```
Input: [0.97, 0.57, 0.56, 0.45, 0.32]
  │
  ├─ Step 1 (cap @5): [0.97, 0.57, 0.56, 0.45, 0.32]
  │
  ├─ Step 2 (floor ≥0.1): [0.97, 0.57, 0.56, 0.45, 0.32]
  │
  ├─ Step 3 (relative ≥0.485): [0.97, 0.57, 0.56]
  │
  └─ Step 4 (gap ≤1.4): [0.97]   ← 0.97/0.57 = 1.70 > 1.4

Output: [0.97]
```

## Default Parameter Calibration

### gap_ratio = 1.4

Calibrated against DC petition demo data (50 entries, ~100K registered voters).
The data exhibits a bimodal score distribution:

| Pattern | Example | Gap | Truncated? |
|---------|---------|-----|------------|
| Dominant match + noise | 1.0 → 0.57 | 1.75 | Yes |
| Dominant match + borderline | 1.0 → 0.71 | 1.41 | No |
| Ambiguous cluster | 0.67 → 0.66 → 0.65 | ≤1.05 | No |

At `gap_ratio=1.4`:
- **34/50** entries truncated to 1 prediction (clear dominant match)
- **16/50** entries kept all 5 predictions (genuinely ambiguous — same-surname
  groups, shared first names with different addresses)
- **0** entries had an intermediate truncation (2-4 predictions)

The 1.4 threshold sits in the natural gap between these two modes. At 1.5,
entries like Tina Briggs (1.0→0.67, ratio 1.49) survived truncation despite
being clear dominant matches. At 1.3, entries like Erik Acosta
(1.0→0.73 "Eric Acosta", ratio 1.37) would be truncated despite the second
candidate sharing both first and last name under minor OCR variation.

### relative_threshold = 0.5

Follows the "50% of best" heuristic common in information retrieval systems.
Below this threshold, a prediction contributes less than half the confidence of
the top match, making it unlikely to be the correct candidate.<sup>[2](#f2)</sup>

### absolute_floor = 0.1

Conservative — only removes predictions below 10% similarity, which in practice
are degenerate matches (empty strings, completely different names). The
relative threshold and gap detection handle the meaningful filtering.

### max_predictions = 5

Matches the previous hard limit. Serves as a safety ceiling, not an active
filter in most cases.

## Disabling Filters

Each filter can be effectively disabled for testing or tuning:

| Filter | Disable by |
|--------|------------|
| Max cap | `max_predictions=sys.maxsize` |
| Absolute floor | `absolute_floor=0.0` |
| Relative threshold | `relative_threshold=0.0` |
| Gap detection | `gap_ratio=float("inf")` |

The test suite uses this pattern to verify each filter in isolation.

## Performance

Pure Python function operating on in-memory lists. For the project's typical
input (≤5 predictions per entry), performance is negligible (<0.1ms). The
`sorted()` call is the dominant cost at O(n log n), but n ≤ 5 makes this
constant-time in practice.

## Limitations

- **No inter-entry correlation**: Each entry's predictions are truncated
  independently. An entry with scores [0.65, 0.64, 0.63] keeps all 5 even if
  other entries truncate at lower absolute scores.
- **Fixed parameters**: All entries use the same thresholds. Regions with
  systematically different score distributions (e.g., shorter names producing
  higher baseline similarity) may need different defaults.
- **No statistical calibration**: Thresholds are hand-tuned against one dataset
  (DC petition demo). A more principled approach would use precision-recall
  curves on labeled ground truth, but no labeled data is available.

## Keeping This Document in Sync

| What changed | Where to verify | Command |
|-------------|----------------|---------|
| Parameter defaults | `prediction_truncation.py` function signature | `grep "def truncate_predictions" backend/app/services/prediction_truncation.py -A 6` |
| Filter logic | `prediction_truncation.py` function body | `cat backend/app/services/prediction_truncation.py` |
| Test coverage | `test_prediction_truncation.py` | `cd backend && uv run pytest tests/unit/services/test_prediction_truncation.py -v` |
| Call sites | `campaign_query_service.py`, `results_query_service.py` | `grep -rn "truncate_predictions" backend/app/` |
| Real-world behavior | API response | `curl localhost:8080/api/campaigns/{id}/results \| python3 -c "import json,sys; ..."` |

When changing parameters:
1. Update the default in `prediction_truncation.py`
2. Run `uv run pytest tests/unit/services/test_prediction_truncation.py -v`
3. Update the "Default Parameter Calibration" section with new distribution
   analysis (query the API and tally prediction counts)
4. Update the filter pipeline visualization example if step behavior changes

---

## Footnotes

<a id="f1"></a>**[1]** Using ratios rather than differences for change-point detection
is well-established in statistical process control and signal processing. The
likelihood ratio test (Neyman-Pearson lemma) compares multiplicative changes in
probability density, not additive differences. For score-based ranking
truncation, the ratio captures the relative drop in confidence between adjacent
candidates. See: Basseville, M. & Nikiforov, I.V. (1993).
[*Detection of Abrupt Changes: Theory and Application*](https://www.sciencedirect.com/book/9780120744701/detection-of-abrupt-changes).
Prentice-Hall. Chapter 2 discusses the CUSUM algorithm, which uses log-likelihood
ratios (equivalent to score ratios under a log-normal model) for change-point
detection in sequential data.

<a id="f2"></a>**[2]** The 50% relative threshold is analogous to the "elbow method"
used in determining the number of clusters in k-means clustering — keeping only
items within a significant proportion of the best. In information retrieval,
the related "percentage threshold" approach (keep documents scoring above X% of
the top-retrieved document) is discussed in: Manning, C.D., Raghavan, P. &
Schütze, H. (2008).
[*Introduction to Information Retrieval*](https://nlp.stanford.edu/IR-book/).
Cambridge University Press. Chapter 6 discusses score-based pruning in ranking.

<a id="f3"></a>**[3]** The minimum-one-prediction invariant follows the principle that
a system should never present "no results" when data exists. In the context of
petition verification, showing at least one candidate ensures the reviewer has
something to evaluate — even if it's a low-confidence match that will be
rejected. This aligns with the design philosophy described in: Norman, D.A.
(2013). [*The Design of Everyday Things*](https://basicbooks.com/titles/don-norman/the-design-of-everyday-things/9780465050659/).
Basic Books. The "visibility" principle: the system state should always be
comprehensible to the user.
