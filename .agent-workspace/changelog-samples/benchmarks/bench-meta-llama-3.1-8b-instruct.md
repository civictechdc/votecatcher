## [1.0.0-alpha.5] — Pre-release

### Crop Images in Results

Added the ability to crop images in the results table, including thumbnail URLs, expandable rows, and a lightbox for viewing cropped images.

- **crops**: Crop image endpoint + thumbnail_url in results
- **results**: Add client-side sort for results table
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

### Security

- **security**: Sanitize HTML output, add focus trap, fix VDD findings

### Removed

### Deprecated

### Changed

- **services**: Extract PredictionBuilder from duplicated logic
- **services**: Wire export_results_csv to OcrTextParser.format_text()
- **tests**: Consolidate engine/session fixtures into conftest
- **services**: Stream CSV export with yield_per, extract HTTP concern
- **services**: Readability pass — deduplicate, flatten, simplify
- **monitor**: Close EPIC-6 — remove dead _providers, add edge cases, fix structlog