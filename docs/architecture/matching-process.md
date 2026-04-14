# Matching Process

This document explains how spec-driven matching works end-to-end in VoteCatcher.

## Overview

The matching pipeline takes OCR-extracted text from petition scans and finds the best-matching registered voters using fuzzy string comparison. The pipeline is driven by a `RegionFieldSpecConfig` — a declarative spec loaded from a JSON5 file that defines which fields to compare, how to compose voter data into ballot field values, and how much weight each field carries.

## Pipeline

```
OCR Result ──► Voter Data Adapter ──► Template Rendering ──► Weighted Field Scoring ──► Confidence Assignment
                                              │
                                     RegionFieldSpecConfig
                                     (field mappings + weights)
```

### Step 1: OCR Result

An `OcrResult` contains `extracted_text` — a dict like `{"name": "John Smith", "address": "123 Main St"}`. The keys correspond to `ballot_field.id` values from the spec.

### Step 2: Voter Data Adapter

`RegisteredVoter` stores voter data in nested JSON blobs:
- `name_data` — first name, middle name, last name
- `address_data` — street number, street name, zip code, etc.
- `other_field_data` — ward, party, etc.

The `flatten_voter_data` function (in `app/matching/voter_data_adapter.py`) collapses these three blobs into a single flat `dict[str, str]` keyed by `voter_reg_field.id`. It uses the spec's `voter_reg_fields` to map each field's `category` to the correct blob.

```python
flat = flatten_voter_data(voter, spec.voter_reg_fields)
# {"first_name": "John", "last_name": "Smith", "street_number": "123", ...}
```

### Step 3: Template Rendering

Each `FieldMapping` in the spec defines a `template` string with placeholders:

```json5
{
  ballot_field_id: "address",
  template: "{street_number} {street_name} {street_type} {street_dir_suffix}"
}
```

`render_template` substitutes placeholders from the flattened voter dict, dropping empty values and cleaning up extra whitespace. Sentinel values like `"N/A"` are treated as empty.

### Step 4: Weighted Field Scoring

For each `matchable_fields()` ballot field (those with `match_weight > 0`):

1. Get the OCR value: `ocr_text.get(ballot_field.id)`
2. Get the voter value: `render_template(mapping.template, flat_voter_data)`
3. Score: `fuzz.ratio(ocr_value, voter_value) / 100.0` using RapidFuzz
4. Weight: `score * ballot_field.match_weight`

The overall similarity is the weighted sum divided by `total_match_weight()`.

The `field_scores` dict in the result is keyed by `ballot_field.id` (e.g., `"name"`, `"address"`, `"ward"`), not hardcoded strings.

### Step 5: Confidence Assignment

| Level | Threshold | Meaning |
|-------|-----------|---------|
| HIGH  | ≥ 0.85    | Strong match — likely the same person |
| MEDIUM | 0.60–0.84 | Possible match — review recommended |
| LOW   | < 0.60    | Weak match — unlikely correct |

## Pre-Filtering

Before scoring each voter, the pipeline narrows the candidate set:

1. **Region filter**: Only voters with `region_id` matching the campaign's region
2. **Spec-driven field filter** (optional): If the spec defines `pre_filter_field_id`, voters are filtered by a specific field value (e.g., zip code). The spec's `pre_filter_field()` method returns the `VoterRegField` with the matching ID, and the filter uses the correct JSON blob based on the field's `category`.

## The Two Code Paths

The `MatchingService` currently supports two code paths, gated by `settings.features.fieldspec.matching`:

| Flag | Path | Method |
|------|------|--------|
| `False` (default) | Hardcoded | `match_ocr_result` → `calculate_similarity` with fixed name/address fields |
| `True` | Spec-driven | `calculate_spec_driven_similarity` with dynamic fields and weights |

The hardcoded path uses `_build_voter_name` / `_build_voter_address` with fixed key names. The spec-driven path uses `flatten_voter_data` + `render_template`.

The `JobWorker` (background job processor) delegates all matching to `MatchingService.match_ocr_result()` — no duplicate inline matching logic exists.

## Approval Tests

The matching pipeline is guarded by characterization tests (approval tests) that capture a baseline score matrix. Any change to scoring that alters the matrix is flagged for review. The baseline is stored in `tests/unit/services/test_matching_regression_approval.py`.

## Key Files

| File | Purpose |
|------|---------|
| `app/matching/matching_service.py` | Core matching logic, both hardcoded and spec-driven |
| `app/matching/voter_data_adapter.py` | Flattens voter JSON blobs for template rendering |
| `app/domain/field_spec.py` | `RegionFieldSpecConfig`, `render_template`, domain types |
| `app/services/field_spec_service.py` | Loads specs, provides them to matching |
| `app/regions/dc.json5` | DC region spec (field definitions, mappings, weights) |
| `app/jobs/worker.py` | Background worker — delegates to MatchingService |
