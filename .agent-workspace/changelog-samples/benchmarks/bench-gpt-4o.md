## [1.0.0-alpha.5] - 2026-04-16 — Pre-release

### Crop Images in Results

Introduced new capabilities for managing and displaying cropped images in results. Includes client-side enhancements and backend support for image cropping and thumbnails.

- Added crop image endpoint and thumbnail URL in results.
- Added thumbnail column to results table and updated CampaignResultResponse interface.
- Enabled expandable rows and accordion functionality in results table.
- Added crop lightbox with backend semaphore and keyed table rows.
- Implemented progressive reveal with source page crop highlight.
- Enabled per-entry highlight on the source page.
- Clipped thumbnail/crop to entry row and added source page lightbox.
- Adaptive score-based prediction truncation added.

### Results Table Enhancements

Improved results table functionality with sorting, rendering, and metadata updates.

- Added client-side sorting for the results table.
- Added renderPredictionsTable and renderExpandedCropImage pure functions.
- Added crop metadata to campaign results endpoint.

### Fixed

- Validated resolved path against storage base for crop images.
- Sanitized HTML output, added focus trap, and resolved security findings.
- Addressed VDD findings related to results table (#6, #7, #8).
- Centralized API URL to fix relative URL 404 errors.
- Fixed crop_router test import shadowing from `__init__.py`.
- Updated featureFlags test environment to match base URL convention.

### Performance

Optimized database queries for results pagination.

- Implemented SQL-level pagination and GROUP BY for results.

### Changed

- Extracted PredictionBuilder from duplicated logic in services.
- Connected export_results_csv to OcrTextParser.format_text().
- Streamlined CSV export with yield_per and extracted HTTP concerns.
- Improved readability by deduplicating and simplifying service logic.