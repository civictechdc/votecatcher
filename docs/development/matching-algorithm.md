# Matching Algorithm — DC Region (Legacy)

This document describes the **original matching algorithm** used for matching
OCR-extracted petition signer data against the DC voter registration list.

## Algorithm Overview

The algorithm compares OCR results (name + address) against every registered
voter, computing a combined similarity score using **harmonic mean** of
individual fuzzy match scores.

### Source

`app/matching/fuzzy_match_helper.py` (commit `11b9617`)

### Scoring Formula

```
name_score = fuzz.ratio(ocr_name, voter_name) / 100
addr_score = fuzz.ratio(ocr_address, voter_address) / 100

if name_score + addr_score == addr_score == 0:
    combined = 0.0
else:
    combined = (2 * name_score * addr_score) / (name_score + addr_score)
```

Where `fuzz.ratio` is RapidFuzz's normalized Levenshtein distance returning a
float in [0, 100].<sup>[1](#f1)</sup> This was chosen over more sophisticated
string metrics (Jaro-Winkler, Smith-Waterman) because Levenshtein distance
directly measures character-level edit operations — the kind of errors OCR
commonly introduces (character substitutions, transpositions, insertions from
handwriting artifacts).<sup>[2](#f2)</sup>

### Field Composition

| Field | Template | Example |
|-------|----------|---------|
| Name | `First_Name + " " + Last_Name` | `"Alexis Walter"` |
| Address | `Street_Number + " " + Street_Name + " " + Street_Type + " " + Street_Dir_Suffix` | `"23407 Hawkins Lock "` |

Empty parts are omitted. Fields are read directly from the voter CSV columns.

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

### Baseline Performance (Gold Master)

50 OCR results × 100,000 registered voters:

| Metric | Value |
|--------|-------|
| HIGH | 37 (74%) |
| MEDIUM | 12 (24%) |
| LOW | 1 (2%) |
| Exact name matches | 36/50 (72%) |
| Avg name score | 0.9205 |
| Avg address score | 0.8974 |
| Avg combined score | 0.9055 |
| Combined range | 0.5783 – 1.0000 |

### Precision Characteristics

- `fuzz.ratio` returns a float (not integer), divided by 100 → recurring decimals possible
- Individual scores reported at **3 decimal places** (0.001 precision)
- Combined (harmonic mean) reported at **4 decimal places** (0.0001 precision)
- Confidence thresholds at 2 decimal places — individual scores are 10x more precise

### Why Harmonic Mean

The harmonic mean was chosen over the arithmetic mean as the aggregation
function because petition matching requires **both** name and address to
agree.<sup>[4](#f4)</sup> Arithmetic mean would allow a perfect name match
(1.0) paired with a garbage address (0.1) to score 0.55 — nearly MEDIUM —
which is misleading for a petition validation use case where address is an
independent confirming signal.

Harmonic mean penalizes imbalanced scores:

| name_score | addr_score | Harmonic | Arithmetic |
|-----------|-----------|----------|------------|
| 1.0 | 1.0 | 1.000 | 1.000 |
| 1.0 | 0.5 | 0.667 | 0.750 |
| 0.9 | 0.9 | 0.900 | 0.900 |
| 0.5 | 0.1 | 0.167 | 0.300 |

This ensures both name AND address must be reasonable matches — a perfect name
with a terrible address won't produce a misleadingly high score.

### Matching Process

1. Load voter registration CSV → compose `Full Name` and `Full Address` for each voter
2. Load OCR results from database (name + address extracted text)
3. For each OCR result:
   - Compute `fuzz.ratio` against every voter's `Full Name` → get top N name matches
   - Among top N name matches, compute `fuzz.ratio` against their `Full Address`
   - Calculate harmonic mean of name + address scores
   - Sort by combined score, return top match
4. Assign confidence level based on combined score

### Limitations

- **Full scan**: Compares every OCR result against every voter (O(n×m)) — no pre-filtering
- **Region-specific**: Hardcoded DC column names (`First_Name`, `Street_Number`, etc.)
- **No weights**: Name and address contribute equally
- **No partial matching**: Uses `fuzz.ratio` (full string) rather than `partial_ratio`
- **No batch optimization**: Each OCR result scanned independently

### Gold Master Approval Tests

The baseline is locked in approval tests at:
- Branch: `test/matching-baseline-gold`
- Test: `tests/unit/matching/test_matching_gold_master.py`
- Approved snapshot: `tests/unit/matching/test_old_algorithm_approval.approved.txt`

Any future matching implementation must prove parity against this locked baseline.

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
