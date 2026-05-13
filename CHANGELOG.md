# Changelog

## [1.0.0](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.7..v1.0.0) - 2026-05-13

### Fixed

- **ci**: Generate only new version section, fix summarize guards
- **ci**: Remove unsupported --format json from vulture, fix whitelist filename
- **ci**: Correct nuclei path, update bun audit ignores, update deps
- **ci**: Use -ud flag for nuclei templates, add --output jscpd-report to duplication recipe
- **deps**: Upgrade mako, python-multipart, urllib3, mistralai — resolves 4 vulns + adverse status
- **docker**: Bump uv 0.11.2→0.11.13 to resolve rustls-webpki CVE (GHSA-82j2-j2ch-gfr8)
- **ci**: Ignore libcap2 CVE-2026-4878 in Trivy — no Debian fix available

### Changed

- Externalize blocked-dir patterns into .gitblock
- Make reject-internal-dirs.sh project-agnostic

### Bump

- Version 1.0.0-a7 → 1.0.0

## [1.0.0-alpha.7](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.6..v1.0.0-alpha.7) - 2026-04-25

### Added

- Devcontainer hardening + oxc editor migration (#128)
- **ci**: Retry changelog summarization with fallback model

### Fixed

- **ci**: Add radon dev dependency, replace codecov with shields.io coverage badge
- **worker**: Persist provider_job_id, terminal status, Python <3.14 pin (#131)
- **docker**: Upgrade OS packages in frontend prod image (#132)
- **docker**: Pin trixie source to upgrade OpenSSL in node:20-slim
- **justfile**: Add uv lock to version-set recipe
- **docker**: Add trixie-security source for frontend OpenSSL CVE fix
- **docker**: Remove -t trixie pin to allow trixie-security upgrades
- **docker**: Patch OpenSSL CVEs in frontend dev image and scan prod images
- **deps**: Override postcss to >=8.5.10 for XSS CVE fix
- **lint**: Sort package.json overrides, fill empty placeholder files
- **docker**: Use node:22-trixie-slim for frontend prod image
- **docker**: Strip npm/yarn/corepack from frontend prod runner stage
- **ci**: Pin git-cliff v2.12.0 with versioned asset name, fix edge function TS errors
- **ci**: Prevent changelog wipe on release, restore prior versions
- **ci**: Generate changelog to temp file and prepend, add API fallback
- **ci**: Gracefully handle AI summarization API failures

## [1.0.0-alpha.6](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.5..v1.0.0-alpha.6) - 2026-04-21

### Added

- Git-cliff changelog generation with GitHub Models summarization (#110)
- **middleware**: Implement security headers, CORS config, rate limiting modules
- **api**: Wire security middleware into app startup
- Observability foundation — correlation IDs, health check, query logging, Sentry (#123)
- **pagination**: Cursor-based keyset pagination + CSV N+1 fix + adversarial hardening (#124)

### Fixed

- Add GitHub compare links to changelog version headers
- Add google-genai as explicit dependency after langchain removal
- Upgrade mako 1.3.10→1.3.11 to resolve path traversal vuln
- **backend**: Add stale task cleanup to DemoMatchingTaskMonitor (#120)
- **ci**: Add GHSA-rp42-5vxx-qpwr ignore for basic-ftp transitive vuln

### Changed

- **ocr**: Remove dead _create_ocr_client and langchain imports
- **middleware**: Remove redundant local in security headers dispatch

## [1.0.0-alpha.5](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.3..v1.0.0-alpha.5) - 2026-04-16

### Added

- **monitor**: Cleanup dicts on terminal status, pool recycling, SSE max lifetime
- **results**: Add client-side sort for results table
- **crops**: EPIC-2 — crop image endpoint + thumbnail_url in results
- **frontend**: Add thumbnailUrl to CampaignResultResponse interface
- **frontend**: Add thumbnail column to results table
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

### Changed

- **services**: Extract PredictionBuilder from duplicated logic
- **services**: Wire export_results_csv to OcrTextParser.format_text()
- **tests**: Consolidate engine/session fixtures into conftest
- **services**: Stream CSV export with yield_per, extract HTTP concern
- **services**: Readability pass — deduplicate, flatten, simplify
- **monitor**: Close EPIC-6 — remove dead _providers, add edge cases, fix structlog

## [1.0.0-alpha.3](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.2..v1.0.0-alpha.3) - 2026-04-15

### Added

- **field-spec**: G0 dependencies, editor config, and feature flag framework
- **field-spec**: G1 domain value objects
- **field-spec**: G2 template renderer with approval tests
- **field-spec**: G3 DC region spec source file
- **field-spec**: G4 persistence layer
- **field-spec**: G7 implement voter data adapter
- **field-spec**: G7 capture matching baseline approval test
- **field-spec**: G7 add spec-driven matching to MatchingService
- **field-spec**: G5 application service + G6 spec loading and startup integration
- **field-spec**: G7.3a configurable pre-filter for voter selection
- **field-spec**: G7.6 document full_name/is_matchable as simplified defaults + update progress
- **field-spec**: G7.7-G7.9 consolidate worker matching, matching process doc, C4 update
- **field-spec**: G3 add demo.json5 spec with approval tests and template smoke tests
- **field-spec**: G9 backend — region list endpoint, campaign region resolution, integration tests (5/5 pass)
- **matching**: Legacy address fallback in voter_data_adapter
- **matching**: Extract ScoreAggregator protocol with HarmonicMeanAggregator

### Fixed

- SSE setup:updated event, field_spec None crash, double chevron dropdown
- **matching**: Add .strip() to render_template to eliminate trailing space penalty
- **matching**: Spec-driven voter CSV import with structured address_data
- **frontend**: Replace import.meta.env with SSR-safe alternatives, add ESLint guard
- **matching**: Campaign results and metrics must only use latest job
- **ci**: Address PR #24 CI failures and code quality feedback
- **frontend**: Use bracket access for import.meta.env to satisfy svelte-check
- **frontend**: Replace $env/static/public with import.meta.env for CI build
- **frontend**: Replace all $env/static/public imports with import.meta.env
- **ci**: Replace $env/static/private with $env/dynamic/private to fix frontend build
- **frontend**: Replace remaining $env/static/public imports with import.meta.env
- **tests**: Update featureFlags/settings/demo/database tests to use vi.stubEnv

### Changed

- **field-spec**: G8 spec-driven voter list service
- **field-spec**: G10 switch production code to spec-only paths

## [1.0.0-alpha.2](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1..v1.0.0-alpha.2) - 2026-04-14

### Fixed

- Prefix unused catch variable with underscore in edge function
- Split dependency install into separate backend/frontend steps
- Bump pytest to >=9.0.3 to resolve GHSA-6w46-j5rx-g56g
- **ci**: Skip gold master tests when voter CSV unavailable

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
- Review: git hook infrastructure (.gitblock + reject-internal-dirs + pre-commit) (#80)

- Extracted service layer — ResultsQueryService, CampaignQueryService, JobQueryService, SessionService, ConfigService, DemoOrchestrationService
- Consolidated OCR providers — removed batching module, LangChain, dotenv, and settings repository
- Renamed `frontend-svelt/` to `frontend/`

### Security

- Added API key redaction to structlog processor

<!-- generated by git-cliff, summarized by GitHub Models -->
<!-- Format: https://keepachangelog.com/en/1.0.0/ -->
