## [1.0.0-alpha.5] — Pre-release

### View Results with Image Crops

This release introduces image crops in the results table, with expandable rows and a lightbox for source page highlights.

- Added client-side sort for results table
- Added thumbnail column and expandable rows to results table
- Added crop lightbox and progressive reveal of source page with crop highlight
- Added per-entry highlight on source page and clipped thumbnail/crop to entry row
- Added adaptive score-based prediction truncation

### Improve Results Handling

- Implemented SQL-level pagination and GROUP BY for results
- Streamlined CSV export with yield_per and extracted HTTP concern

### Fixed

- Validated resolved path against storage base for crops
- Sanitized HTML output and addressed security findings
- Fixed relative URL 404s and centralized API URL
- Added crop metadata to campaign results endpoint

### Security

- Added focus trap and fixed security findings