# Complexity Tech Debt

> Last updated: 2026-03-29
> Source: radon v6.0.1
> Status: Baseline captured (Phase 0)

## Critical

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| E-rated function | `app/routers/campaign_router.py:362` | radon | `get_campaign_results` — complexity E. Needs decomposition. |

## High

| Finding | File:Line | Tool | Details |
|---------|-----------|------|---------|
| D-rated method | `app/files/file_service.py:194` | radon | `FileService.import_voter_list` — complexity D |
| C-rated function | `app/matching/fuzzy_match_helper.py:185` | radon | `create_ocr_matched_df` — complexity C |
| C-rated function | `app/routers/results_router.py:55` | radon | `_build_predictions_from_match_results` — complexity C |
| C-rated function | `app/routers/results_router.py:133` | radon | `get_results` — complexity C |
| C-rated function | `app/routers/results_router.py:230` | radon | `export_results_csv` — complexity C |
| C-rated function | `app/routers/campaign_router.py:562` | radon | `get_setup_status` — complexity C |
| C-rated method | `app/jobs/worker.py:271` | radon | `JobWorker._run_ocr_phase` — complexity C |
| C-rated method | `app/jobs/worker.py:881` | radon | `JobWorker._find_top_matches` — complexity C |
| C-rated method | `app/jobs/worker.py:435` | radon | `JobWorker._run_real_ocr` — complexity C |
| C-rated method | `app/jobs/worker.py:551` | radon | `JobWorker._run_batch_ocr` — complexity C |
| C-rated function | `app/logger_config/app_logger.py:40` | radon | `redact_api_keys` — complexity C |
| C-rated method | `app/events/event_bus.py:66` | radon | `EventBus.publish` — complexity C |

## Medium

20 B-rated functions/methods across matching, OCR, routers, files, jobs modules. Average complexity: B (9.84).

## Low / Informational

- All 106 modules scored A for maintainability
- Full reports: `baselines/radon-complexity.txt`, `baselines/radon-maintainability.txt`
- 44 blocks analyzed total
