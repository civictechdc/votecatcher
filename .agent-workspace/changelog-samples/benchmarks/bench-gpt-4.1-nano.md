## [1.0.0-alpha.5] — 2026-04-16

### Added

- **monitor**: Cleanup dicts on terminal status, pool recycling, SSE max lifetime.
- **results**: Add client-side sort for results table.
- **crops**: Crop image endpoint and thumbnail URL in results.
- **frontend**: Add thumbnailUrl to CampaignResultResponse interface.
- **frontend**: Add thumbnail column to results table.
- **results**: Add renderPredictionsTable and renderExpandedCropImage functions.
- **results**: Add expandable rows and accordion in results page.
- **results**: Add crop lightbox, backend semaphore, and keyed table rows.
- **results**: Add progressive reveal on source page with crop highlight.
- **results**: Add per-entry highlight on source page.
- **results**: Clip thumbnail and crop to entry row, add source page lightbox.
- **results**: Implement adaptive score-based prediction truncation.

### Fixed

- **crops**: Validate resolved path against storage base.
- **security**: Sanitize HTML output, add focus trap, fix findings.
- **results**: Address low-severity findings.
- **frontend**: Centralize API URL, fix relative URL 404s.
- **backend**: Fix crop router test import shadowing.
- **frontend**: Update feature flags test environment to match base URL convention.
- **results**: Add crop metadata to campaign results endpoint.

### Performance

- **pagination**: Implement SQL-level pagination and GROUP BY for results.

### Changed

- **services**: Extract PredictionBuilder from duplicated logic.
- **services**: Wire export_results_csv to OCR text parser.
- **tests**: Consolidate engine and session fixtures into conftest.
- **services**: Stream CSV export with yield_per, extract HTTP concerns.
- **services**: Simplify code with deduplication and flattening.
- **monitor**: Remove dead providers, add edge case handling, fix structlog.