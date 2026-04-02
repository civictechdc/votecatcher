# Database Schema

Auto-generated from SQLModel definitions.

**Last updated:** 2026-04-01 01:22 UTC

## Diagram

- [Mermaid ERD](./schema.md) - Renders in GitHub

## Tables

| Table | Purpose |
|-------|---------|
| `campaigns` | Election campaigns |
| `llm_provider_config` | LLM provider configurations |
| `match_results` | Signature match results |
| `matcher_jobs` | Matching job queue |
| `ocr_jobs` | OCR job queue |
| `ocr_models` | OCR model definitions |
| `ocr_providers` | OCR provider definitions |
| `ocr_results` | OCR processing results |
| `petition_crops` | Extracted signature images |
| `petition_scans` | Uploaded petition PDFs |
| `regions` | Geographic regions for campaigns |
| `registered_voters` | Voter registration data |
| `sessions` | User sessions |
| `users` | User accounts |
| `voter_list_uploads` | Voter list upload records |

## Regeneration

Run to regenerate after model changes:

```bash
cd backend && python scripts/generate_schema_docs.py
```
