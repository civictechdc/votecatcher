# Sample A: Raw git-cliff output (alpha.5)

> `git-cliff --config cliff.toml v1.0.0-alpha.3..v1.0.0-alpha.5`
> Mechanical, deterministic, one-line-per-commit. This is the base for both audience levels.

---

## [1.0.0-alpha.5] - 2026-04-16

### Added

- **monitor**: Cleanup dicts on terminal status, pool recycling, SSE max lifetime
- **results**: Add client-side sort for results table
- **crops**: EPIC-2 — crop image endpoint + thumbnail_url in results
- **frontend**: Add thumbnailUrl to CampaignResultResponse interface
- **frontend**: Add thumbnail column to results table
- **results**: Add renderPredictionsTable + renderExpandedCropImage pure functions
- **results**: Add expandable rows to Table + wire accordion in results page
- **results**: Add crop lightbox, backend semaphore, keyed table rows
- **results**: Add progressive reveal — source page with crop highlight
- **results**: Per-entry highlight on source page
- **results**: Clip thumbnail/crop to entry row + source page lightbox
- **results**: Adaptive score-based prediction truncation (#63)

### Fixed

- **crops**: Validate resolved path against storage base
- **security**: Sanitize HTML output, add focus trap, fix VDD findings
- **results**: Address LOW VDD findings #6 #7 #8
- **frontend**: Centralize API URL, fix relative URL 404s
- **backend**: Fix crop_router test import shadowing from __init__.py
- **frontend**: Update featureFlags test env to match base-url convention
- **results**: Add crop metadata to campaign results endpoint

### Performance

- **pagination**: SQL-level pagination and GROUP BY for results

### Changed

- **services**: Extract PredictionBuilder from duplicated logic
- **services**: Wire export_results_csv to OcrTextParser.format_text()
- **tests**: Consolidate engine/session fixtures into conftest
- **services**: Stream CSV export with yield_per, extract HTTP concern
- **services**: Readability pass — deduplicate, flatten, simplify
- **monitor**: Close EPIC-6 — remove dead _providers, add edge cases, fix structlog
