## [1.0.0-alpha.5] — Pre-release

### Crop Images in Results

This release enabled image cropping and thumbnail display throughout the results workflow. Users can view cropped images and thumbnails directly in results tables and lightboxes.

- Added crop image endpoint and thumbnail_url in results.
- Added thumbnail column to results table and CampaignResultResponse interface.
- Added crop lightbox, backend semaphore, and keyed table rows.
- Added progressive reveal with crop highlight on source page.
- Clipped thumbnail/crop to entry row and source page lightbox.
- Added expandable rows and accordion wiring in results page.
- Added renderPredictionsTable and renderExpandedCropImage pure functions.

### Results Table Enhancements

Results tables now support client-side sorting and adaptive prediction truncation. Expanded rows and per-entry highlights improve navigation and clarity.

- Added client-side sort for results table.
- Added adaptive score-based prediction truncation.
- Added per-entry highlight on source page.

### Security and Validation

Sanitization and validation measures were strengthened to protect user data and application integrity.

- Validated resolved path against storage base.
- Sanitized HTML output and added focus trap.
- Fixed vulnerabilities identified in security review.

### API and Frontend Integration

API URLs and feature flags were centralized for consistency. Crop metadata is now included in campaign results.

- Centralized API URL and fixed relative URL 404s.
- Updated featureFlags test environment to match base-url convention.
- Added crop metadata to campaign results endpoint.

### Performance

Results pagination now leverages SQL-level optimizations for faster queries.

- Added SQL-level pagination and GROUP BY for results.

### Changed

- Extracted PredictionBuilder from duplicated logic.
- Wired export_results_csv to OcrTextParser.format_text().
- Streamed CSV export with yield_per and extracted HTTP concern.
- Closed monitor edge cases and fixed structlog.
- Deduplicated and simplified service logic.