```
## [1.0.0-alpha.5] — Pre-release

### Image Cropping & Results Enhancement

Added comprehensive image handling for campaign results. Users can now view cropped thumbnails, expand images with source context, and navigate highlights.

- Added crop image endpoint with thumbnail URLs in results
- Implemented client-side sorting for results table
- Added expandable rows with crop lightbox and source page highlights
- Secured crop paths against storage base validation
- Added progressive reveal of source pages with crop context
- Implemented adaptive score-based prediction truncation

### Security & API Improvements

Strengthened frontend security and centralized API configuration.

- Sanitized HTML output and added focus traps
- Fixed relative URL 404s by centralizing API URL
- Added crop metadata to campaign results endpoint
- Secured against VDD findings #6-8

### Performance

- Implemented SQL-level pagination and GROUP BY for results

### Fixed

- Resolved crop_router test import shadowing
- Updated featureFlags test environment to match base-url convention
- Removed dead provider code and fixed edge cases in monitoring
```