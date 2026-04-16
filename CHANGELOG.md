# Changelog
## [1.0.0-alpha.5](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.3..v1.0.0-alpha.5) — Pre-release

### Crop Images in Results

Crop images are now integrated throughout the results workflow. Users can view thumbnails, expand crop images, and highlight entries on the source page.

- Added crop image endpoint and thumbnail URLs to results.
- Added thumbnail column to results table and CampaignResultResponse interface.
- Added crop lightbox with backend semaphore and keyed table rows.
- Added progressive reveal with crop highlight on source page.
- Added per-entry highlight and clipped thumbnails to entry row and lightbox.

### Results Table Enhancements

Results table now supports client-side sorting and adaptive prediction truncation. Pure functions for rendering predictions and expanded crop images improve frontend modularity.

- Added client-side sort for results table.
- Added renderPredictionsTable and renderExpandedCropImage pure functions.
- Added adaptive score-based prediction truncation.

### Fixed

- Secured resolved crop image paths against storage base.
- Sanitized HTML output, added focus trap, and addressed security findings.
- Addressed low-severity security findings in results.
- Centralized API URL and fixed relative URL 404s in frontend.
- Fixed crop metadata inclusion in campaign results endpoint.

### Performance

- Added SQL-level pagination and GROUP BY for results.

## [1.0.0-alpha.3](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.2..v1.0.0-alpha.3) — Pre-release

### Spec-Driven Voter Matching

Spec-driven voter matching and region selection capabilities were added, including domain value objects, template rendering, and region list endpoints.

- Added editor config and feature flag framework.
- Added domain value objects and template renderer.
- Added DC region spec source file and persistence layer.
- Implemented voter data adapter and matching baseline approval test.
- Added spec-driven matching to MatchingService.
- Integrated application service and spec loading.
- Added configurable pre-filter for voter selection.
- Consolidated worker matching and updated matching process documentation.
- Added demo.json5 spec and approval tests.
- Added region list endpoint and campaign region resolution.

### Matching Improvements

- Added legacy address fallback in voter_data_adapter.
- Extracted ScoreAggregator protocol with HarmonicMeanAggregator.

### Fixed

- Fixed SSE setup:updated event and field_spec None crash.
- Fixed double chevron dropdown.
- Added .strip() to render_template to eliminate trailing space penalty.
- Enabled spec-driven voter CSV import with structured address_data.
- Replaced import.meta.env with SSR-safe alternatives and ESLint guard.
- Ensured campaign results and metrics use only latest job.
- Addressed CI failures and code quality feedback.
- Updated featureFlags/settings/demo/database tests to use vi.stubEnv.

### Changed

- Switched to spec-driven voter list service.
- Changed production code to spec-only paths.

## [1.0.0-alpha.2](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1..v1.0.0-alpha.2) — Pre-release

### Fixed

- Prefixed unused catch variable with underscore in edge function.
- Split dependency install into backend/frontend steps.
- Bumped pytest to >=9.0.3 to resolve security advisory.
- Skipped gold master tests when voter CSV unavailable.

## [0.1.0-alpha.1](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1) — Pre-release

### Svelte Frontend and Backend Integration

Initial release: SvelteKit frontend with workspace, campaigns, jobs, uploads, results, and demo mode. Supabase persistence, OCR pipeline, background workers, Docker deployment, and CI/CD hardening.

- Added workspace layout with sidebar navigation, campaigns, jobs, uploads, and results pages.
- Added Svelte stores for campaigns, jobs, uploads, results, and demo with full CRUD and SSE integration.
- Added demo mode with pre-baked sessions and walkthrough guide.
- Added Supabase persistence layer with Alembic migrations and domain objects.
- Added Docker Compose, DevContainer, production Dockerfiles, and deploy configs.
- Added supply chain protection and security scanning in CI.
- Added background job worker with FastAPI lifecycle and orphan job termination.
- Added OpenAPI spec with generated TypeScript client and camelCase API serialization.

### Fixed

- Resolved frontend SSR errors and import.meta.env compatibility across SvelteKit and jsdom.
- Fixed API URL routing — missing /api prefix, double-slash URLs, relative path 404s.
- Fixed OCR pipeline — multi-entry ocr_index, UNIQUE constraint handling, result deduplication.
- Fixed Docker production builds — build-time env vars, adapter-node, sqlite scheme validation.
- Resolved CI failures across security scans, typecheck, SCA, container scanning, and frontend tests.
- Removed hardcoded database credentials from Alembic config.

### Changed

- Extracted service layer — ResultsQueryService, CampaignQueryService, JobQueryService, SessionService, ConfigService, DemoOrchestrationService.
- Consolidated OCR providers — removed batching module, LangChain, dotenv, and settings_repo.
- Renamed frontend-svelt/ to frontend/.

### Security

- Added API key redaction to structlog processor.

<!-- generated by git-cliff, summarized by GitHub Models -->
<!-- Format: https://keepachangelog.com/en/1.0.0/ -->
