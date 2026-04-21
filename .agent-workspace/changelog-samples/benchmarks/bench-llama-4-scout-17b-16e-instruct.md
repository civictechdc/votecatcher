## [1.0.0-alpha.5] — Pre-release

### Crop Images in Results

The results page now supports displaying cropped images. This feature includes a new endpoint for cropping images and displaying thumbnails in the results table.

- Added crop image endpoint and thumbnail_url in results
- Added thumbnail column to results table
- Added expandable rows to Table and wired accordion in results page
- Added crop lightbox, backend semaphore, keyed table rows
- Added progressive reveal with source page and crop highlight
- Added per-entry highlight on source page
- Clipped thumbnail/crop to entry row and source page lightbox

### Predict Results

Prediction rendering has been improved for better performance and readability.

- Added client-side sort for results table
- Added renderPredictionsTable and renderExpandedCropImage pure functions
- Added adaptive score-based prediction truncation

### Security

Security vulnerabilities have been addressed to ensure the integrity of the application.

- Secured HTML output and added focus trap
- Sanitized HTML output and addressed VDD findings

### Fixed Issues

Several issues have been fixed to improve the stability of the application.

- Fixed validation of resolved path against storage base
- Addressed LOW VDD findings
- Fixed crop_router test import shadowing
- Fixed relative URL 404s
- Updated featureFlags test env to match base-url convention

### Performance

Performance improvements have been made to enhance the user experience.

- Added SQL-level pagination and GROUP BY for results

### Internal Changes

Several internal changes have been made to improve code readability and maintainability.

- Extracted PredictionBuilder from duplicated logic
- Streamlined CSV export with yield_per and extracted HTTP concern
- Consolidated engine/session fixtures into conftest