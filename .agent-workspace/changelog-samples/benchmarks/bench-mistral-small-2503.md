## [1.0.0-alpha.5] — Pre-release

### Crop Images in Results

Added crop images to results and enhanced the user interface for better visualization. This includes thumbnail previews, expandable rows, and a lightbox for detailed views.

- Added crop image endpoint and thumbnail URL to results.
- Added thumbnail column to results table.
- Added expandable rows to results table with accordion functionality.
- Added crop lightbox and backend semaphore for managing image display.
- Added progressive reveal of source page with crop highlight.
- Added per-entry highlight on source page.
- Clipped thumbnail/crop to entry row and source page lightbox.
- Added adaptive score-based prediction truncation.
- Added crop metadata to campaign results endpoint.

### Fixed

- Validated resolved path against storage base.
- Sanitized HTML output and added focus trap.
- Centralized API URL to fix relative URL 404s.

### Performance

- Implemented SQL-level pagination and GROUP BY for results.