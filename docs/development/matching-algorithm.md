# Matching Algorithm

This document describes the matching algorithm for comparing OCR-extracted
petition signer data against voter registration lists. The spec-driven system
supports configurable regions via JSON5 field definitions.

## Algorithm Overview

The algorithm compares OCR results against every registered voter in a region,
computing a combined similarity score by aggregating per-field fuzzy match
scores using a pluggable engine.

### Source

`app/matching/matching_service.py`, `app/matching/engines.py`, `app/domain/field_spec.py`

### Scoring Formula

Each matchable field is scored independently, then aggregated:

```
field_scores[field_id] = fuzz.ratio(ocr_value, voter_value) / 100
weights[field_id] = field.match_weight

combined = engine.aggregate(field_scores, weights)
```

Where `fuzz.ratio` is RapidFuzz's normalized Levenshtein distance returning a
float in [0, 100].<sup>[1](#f1)</sup> This was chosen over more sophisticated
string metrics (Jaro-Winkler, Smith-Winkler) because Levenshtein distance
directly measures character-level edit operations — the kind of errors OCR
commonly introduces (character substitutions, transpositions, insertions from
handwriting artifacts).<sup>[2](#f2)</sup>

### Field Composition

Fields are defined per-region in JSON5 spec files. Voter data is composed via
templates with `{field_id}` placeholders:

| Field | Template (DC) | Example |
|-------|---------------|---------|
| Name | `{first_name} {last_name}` | `"Alexis Walter"` |
| Address | `{street_number} {street_name} {street_type} {street_dir_suffix}` | `"23407 Hawkins Lock"` |

Empty parts are omitted by `render_template()`. Fields are mapped from voter CSV
columns via the spec's `voter_reg_fields` definitions.

### Score Aggregation Engines

Two engines are available, selectable via `MATCHING_ENGINE` env var:

#### Harmonic Mean (default)

```
H = Σ(wᵢ) / Σ(wᵢ / sᵢ)
```

Zero-propagating: if any field scores 0.0, the overall score is 0.0.

#### Weighted Average

```
W = Σ(sᵢ × wᵢ) / Σ(wᵢ)
```

Arithmetic mean weighted by `BallotField.match_weight`.

#### Comparison

| name_score | addr_score | Harmonic | Weighted |
|-----------|-----------|----------|----------|
| 1.0 | 1.0 | 1.000 | 1.000 |
| 1.0 | 0.5 | 0.667 | 0.750 |
| 0.9 | 0.9 | 0.900 | 0.900 |
| 0.5 | 0.1 | 0.167 | 0.300 |

Harmonic mean penalizes imbalanced scores — both name AND address must be
reasonable matches. Weighted average is more permissive when one field is
strong but another is weak.

#### Parity Against Gold Master Baseline

50 OCR results × 100,000 registered voters:

| Metric | Harmonic | Weighted |
|--------|----------|----------|
| Same confidence as baseline | **50/50** | 50/50 |
| Same top voter as baseline | **50/50** | 44/50 |
| Within ±0.0005 of baseline | **50/50** | 35/50 |
| Mean delta | **0.000000** | +0.005415 |
| Max \|delta\| | **0.000000** | 0.052300 |

### Confidence Levels

| Level | Threshold | Description |
|-------|-----------|-------------|
| HIGH | `>= 0.85` | Strong match — high confidence in voter identity |
| MEDIUM | `>= 0.60` | Possible match — needs manual review |
| LOW | `< 0.60` | Unlikely match |

The 0.85 HIGH threshold was calibrated empirically against DC petition data: at
this threshold, 74% of OCR results matched the correct voter with high
confidence. The 0.60 MEDIUM threshold captures near-matches where OCR quality
degraded a field (e.g., "Christina" vs "Christian" → name_score=0.750) but the
address partially confirms the match.<sup>[3](#f3)</sup>

### Precision Characteristics

- `fuzz.ratio` returns a float (not integer), divided by 100 → recurring decimals possible
- Individual scores reported at **3 decimal places** (0.001 precision)
- Combined (harmonic mean) reported at **4 decimal places** (0.0001 precision)
- Confidence thresholds at 2 decimal places — individual scores are 10x more precise

### Why Harmonic Mean Is Default

Petition matching requires **both** name and address to
agree.<sup>[4](#f4)</sup> Weighted average would allow a perfect name match
(1.0) paired with a garbage address (0.1) to score 0.55 — nearly MEDIUM —
which is misleading for a petition validation use case where address is an
independent confirming signal.

### Matching Process

1. Load region spec from JSON5 → get matchable fields, templates, weights
2. Flatten voter data via spec's `voter_reg_fields` → compose field values using templates
3. Load OCR results from database (field-level extracted text)
4. For each OCR result:
   - Compute `fuzz.ratio` for each matchable field against every voter
   - Aggregate per-field scores using configured engine
   - Sort by combined score, return top N matches
5. Assign confidence level based on combined score

### Limitations

- **Full scan**: Compares every OCR result against every voter (O(n×m)) — no pre-filtering index
- **Single similarity function**: Uses `fuzz.ratio` (full string) rather than `partial_ratio` or token-based variants
- **No batch optimization**: Each OCR result scanned independently

### Gold Master Approval Tests

The baseline is locked in approval tests at:
- Test: `tests/unit/matching/test_matching_gold_master.py`
- Approved snapshot: `tests/unit/matching/test_old_algorithm_approval.approved.txt`

Any change to the matching engine must prove parity against this locked baseline.

---

## Footnotes

<a id="f1"></a>**[1]** [RapidFuzz `fuzz.ratio`](https://rapidfuzz.github.io/rapidfuzz/Usage/fuzz.html#ratio) —
Computes the normalized Indel distance (a variant of Levenshtein distance that
only considers insertions and deletions). Chosen for this project because it is
a C++-optimized implementation that handles 100K comparisons per OCR result in
~400ms on commodity hardware, making it practical for the full-scan approach.
The underlying algorithm is described in the
[Levenshtein distance Wikipedia article](https://en.wikipedia.org/wiki/Levenshtein_distance).

<a id="f2"></a>**[2]** Levenshtein-based metrics are well-suited to OCR error patterns.
Handwriting recognition errors tend to be character-level: "Mcdonald" vs
"McDonald", "Catty" vs "Cathy", missing spaces, extra punctuation. Edit
distance captures these directly, whereas phonetic algorithms (Soundex,
Metaphone) are designed for spelling variation in typed text, not visual
recognition errors. For a comprehensive survey of approximate string matching
techniques and their applications to OCR correction, see: Navarro, G. (2001).
["A guided tour to approximate string matching"](https://dl.acm.org/doi/10.1145/375360.375657).
*ACM Computing Surveys*, 33(1), 31–88.

<a id="f3"></a>**[3]** The two-threshold (HIGH/MEDIUM/LOW) scheme follows the pattern used in
voter registration match systems where false positives are costly (wrongly
attributing a petition signature to the wrong voter). The 0.85 HIGH threshold
was not derived from statistical theory but from iterative calibration against
the DC dataset. A more principled approach would use precision-recall curves on
labeled data, but no labeled ground truth was available at the time this
algorithm was written. For a taxonomy of classification approaches in record
linkage (threshold-based, probabilistic, machine learning), see Christen (2012),
Chapter 6: [Classification](https://link.springer.com/chapter/10.1007/978-3-642-31164-2_6).

<a id="f4"></a>**[4]** The harmonic mean for combining multi-field similarity scores is a
common pattern in entity resolution literature. It enforces that all fields
contribute meaningfully — a single high score cannot compensate for a low score
in another dimension. For the mathematical properties of the harmonic mean and
its tendency to mitigate the impact of large outliers while aggravating small
ones, see the [Harmonic mean Wikipedia article](https://en.wikipedia.org/wiki/Harmonic_mean).
Alternative approaches include weighted geometric mean (allows tuning per-field
importance) and learned scoring models (requires labeled training data). For a
comprehensive treatment of multi-field comparison and decision models in data
matching, see: Christen, P. (2012).
[*Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*](https://link.springer.com/book/10.1007/978-3-642-31164-2).
Springer.
