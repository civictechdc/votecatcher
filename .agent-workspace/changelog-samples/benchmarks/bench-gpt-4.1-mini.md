## [1.0.0-alpha.5] - 2026-04-16

### View and Interact with Crop Images in Results

This release introduced comprehensive support for crop images in the results interface. Users can now view thumbnails, expand rows for detailed views, and interact with lightboxes highlighting crop images on source pages.

- Added crop image endpoint and thumbnail URLs in results
- Added thumbnail column to results table and client-side sorting
- Added expandable rows with accordion functionality on results page
- Added crop lightbox with backend semaphore and keyed table rows
- Added progressive reveal with source page crop highlight and per-entry highlights
- Clipped thumbnails and crops to entry rows and source page lightbox

### Manage and Display Prediction Results

Improvements were made to how prediction results are rendered and truncated based on scores. The results endpoint now includes crop metadata for richer data display.

- Added adaptive score-based prediction truncation
- Added renderPredictionsTable and renderExpandedCropImage pure functions
- Added crop metadata to campaign results endpoint

### Improve Pagination Performance

The results pagination was optimized by implementing SQL-level pagination and GROUP BY queries, enhancing performance for large datasets.

- Added SQL-level pagination and GROUP BY for results

### Fix Security and Stability Issues

Several security vulnerabilities were addressed by sanitizing HTML output and adding focus traps. Various low-severity findings were fixed, and API URL handling was centralized to prevent 404 errors.

- Fixed HTML output sanitization and added focus trap for security
- Fixed multiple low-severity security findings in results
- Centralized API URL and fixed relative URL 404 errors
- Validated resolved crop paths against storage base

### Backend and Service Enhancements

Backend services were refactored for better code reuse and streaming capabilities. Test imports and environment configurations were corrected to improve reliability.

- Extracted PredictionBuilder to remove duplicated logic
- Wired CSV export to OCR text parser with streaming via yield_per
- Fixed crop_router test import shadowing
- Updated feature flags test environment to match base URL conventions
- Closed monitor issues by removing dead providers and fixing logging

### Other Changes

- Cleaned up dictionaries on terminal status, pool recycling, and SSE max lifetime