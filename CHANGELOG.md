# Changelog

## [1.0.0-alpha.7](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.6..v1.0.0-alpha.7) — Pre-release

### Fixed

- Persisted provider job IDs and terminal statuses to prevent stuck jobs
- Patched OpenSSL and postcss CVEs in frontend Docker images
- Stripped unnecessary package managers from frontend production image
- Fixed changelog generation to preserve prior version entries on release

## [1.0.0-alpha.6](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.5..v1.0.0-alpha.6) — Pre-release

### Security & Observability

Added security headers, CORS configuration, and rate limiting to the API. Structured logging with correlation IDs and Sentry integration now tracks requests end-to-end.

- Secured API with rate limiting and configurable CORS policy
- Added health check endpoint and structured query logging
- Integrated Sentry for error tracking with correlation IDs

### Faster Results Loading

Replaced offset-based pagination with cursor-based keyset pagination for campaign results. Large result sets no longer degrade as pages increase.

## [1.0.0-alpha.5](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.3..v1.0.0-alpha.5) — Pre-release

### Crop Images in Results

Crop images are now integrated throughout the results workflow. Users can view thumbnails in the results table, expand rows to see full crops, and click to highlight entries on the source page.

- Added crop image endpoint with thumbnail URLs in results
- Added thumbnail column to results table with expandable rows
- Added crop lightbox with concurrency control and keyed table rows
- Added progressive reveal with crop highlight on source page

### Results Table Improvements

- Added client-side sorting to the results table
- Filtered low-confidence matches automatically via adaptive score-based truncation
- Moved results pagination to SQL-level grouping for large datasets

### Fixed

- Secured resolved crop image paths against path traversal
- Sanitized HTML output and added focus trap for accessibility
- Centralized API URL resolution — relative URL 404s resolved

## [1.0.0-alpha.3](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.2..v1.0.0-alpha.3) — Pre-release

### Spec-Driven Voter Matching

Added spec-driven voter matching with domain value objects, template rendering, and region-based field configuration. The matching pipeline now uses declarative specs instead of hardcoded logic.

- Added domain value objects and template renderer for field specs
- Added DC region spec source file and persistence layer
- Implemented voter data adapter with matching baseline approval tests
- Added configurable pre-filter for voter selection
- Added region list endpoint and campaign region resolution

### Matching Improvements

- Added legacy address fallback in voter data adapter
- Extracted score aggregator protocol with harmonic mean implementation

### Fixed

- Fixed SSE setup event and field spec null crash
- Fixed double chevron dropdown in UI
- Fixed trailing space penalty in template rendering
- Replaced `import.meta.env` with SSR-safe alternatives for CI compatibility

## [1.0.0-alpha.2](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1..v1.0.0-alpha.2) — Pre-release

### Fixed

- Split dependency install into separate backend/frontend steps for faster builds
- Bumped pytest to resolve security advisory
- Skipped gold master tests when voter CSV is unavailable

## [0.1.0-alpha.1](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1) — Pre-release

### Svelte Frontend and Backend Integration

Initial release with SvelteKit frontend, Supabase persistence, OCR pipeline, background workers, Docker deployment, and CI/CD hardening.

- Added workspace layout with sidebar navigation, campaigns, jobs, uploads, and results pages
- Added Svelte stores for campaigns, jobs, uploads, results, and demo mode with SSE integration
- Added demo mode with pre-baked sessions and walkthrough guide
- Added Supabase persistence layer with Alembic migrations and domain objects
- Added Docker Compose, DevContainer, production Dockerfiles, and deploy configs
- Added supply chain protection and security scanning in CI
- Added background job worker with FastAPI lifecycle and orphan job termination
- Added OpenAPI spec with generated TypeScript client and camelCase API serialization

### Fixed

- Resolved frontend SSR errors and `import.meta.env` compatibility across SvelteKit and jsdom
- Fixed API URL routing — missing `/api` prefix, double-slash URLs, relative path 404s
- Fixed OCR pipeline — multi-entry `ocr_index`, UNIQUE constraint handling, result deduplication
- Fixed Docker production builds — build-time env vars, adapter-node, sqlite scheme validation
- Resolved CI failures across security scans, typecheck, SCA, container scanning, and frontend tests
- Removed hardcoded database credentials from Alembic config

### Changed

- Extracted service layer — ResultsQueryService, CampaignQueryService, JobQueryService, SessionService, ConfigService, DemoOrchestrationService
- Consolidated OCR providers — removed batching module, LangChain, dotenv, and settings repository
- Renamed `frontend-svelt/` to `frontend/`

### Security

- Added API key redaction to structlog processor

<!-- generated by git-cliff, summarized by GitHub Models -->
<!-- Format: https://keepachangelog.com/en/1.0.0/ -->
