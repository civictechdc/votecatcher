# ADR-0008: Template-Based Field Rendering

## Status

Accepted

## Date

2026-04-13

## Context

Ballot petition forms have region-specific field layouts. A DC ballot may show "Full Name" as one field, while another region splits it into "First Name" and "Last Name". Similarly, addresses vary: some regions include apartment numbers, others don't.

We need a way to compose ballot field values from voter registration data that:
- Varies by region without per-region Python code
- Is declarative and PR-reviewable
- Handles edge cases (empty middle names, missing apartments, N/A values)

## Decision

Use string templates with `{field_id}` placeholders in the JSON5 region spec files. A pure function `render_template` replaces placeholders with voter data values, handling edge cases:

- **Empty placeholders are dropped** — `"{first_name} {middle_name} {last_name}"` with empty middle name produces `"John Smith"`, not `"John  Smith"`
- **Sentinel values treated as empty** — `"N/A"`, `"NA"` (case-insensitive) are replaced with empty strings
- **Trailing punctuation cleaned** — commas and "Apt" labels after empty values are removed
- **Multiple spaces collapsed** — no double spaces in output

The `_extract_placeholders` helper uses `re.findall(r"\{(\w+)\}", template)` to discover which voter fields a template needs.

This function lives in the domain layer (`app/domain/field_spec.py`) because it has no infrastructure dependencies and operates purely on domain types.

## Consequences

- **Region configs are self-documenting** — `{first_name} {middle_name} {last_name}` is readable
- **No per-region Python code needed** — adding a new region is a JSON5 file change only
- **Approval tests guard rendering** — golden masters catch unintended changes
- **Edge cases handled uniformly** — N/A values, empty fields, trailing punctuation all handled in one place
