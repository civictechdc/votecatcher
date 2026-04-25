# Changelog

## [1.0.0-alpha.7](https://github.com/civictechdc/votecatcher/compare/v1.0.0-alpha.6..v1.0.0-alpha.7) - 2026-04-25

### Added

- Devcontainer hardening + oxc editor migration (#128)

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

## [0.1.0-alpha.1](https://github.com/civictechdc/votecatcher/compare/v0.1.0-alpha.1) - 2026-04-12

### Added

- Add /workspace/ocr/simulate/{task_id} endpoint for testing
- Add design tokens CSS and cn utility for frontend
- Add Pagination component with tests
- Add simulation API and feature flag system
- Add verification script for fix-results-table
- Update API client to support both old and new request signatures
- Add Docker Compose and DevContainer configuration
- Add OpenAPI spec and generate TypeScript client
- **backend**: Implement FileService for Phase 2
- **ui**: Add SidebarNavItem component with TDD
- **ui**: Add Sidebar component with mobile support
- **routes**: Add workspace layout with sidebar
- **routes**: Add placeholder workspace pages
- **frontend**: Add API client wrapper singleton
- **frontend**: Add campaigns store with fetchAll
- **frontend**: Add create and delete to campaigns store
- **frontend**: Load campaign count from API in dashboard
- **frontend**: Add campaigns list page with CRUD
- **frontend**: Add jobs store with create/fetch/cancel
- **frontend**: Add uploads store with progress tracking
- **frontend**: Add petition upload page with campaign selector
- **frontend**: Add SSE integration to jobs store
- **frontend**: Add job status page with SSE integration
- **frontend**: Add results store with pagination and CSV export
- **frontend**: Add CSV export button component with download functionality
- **frontend**: Add results page with table and CSV export
- **frontend**: Add demo store with reset/loadPrebaked methods
- **frontend**: Add E2E tests with Playwright
- **api,frontend**: Add session management endpoints and UI
- **phase5**: Complete demo mode and walkthrough guide
- **demo**: Add DemoDataService for pre-baked sessions
- **demo**: Wire DemoDataService into router endpoints
- **frontend**: Show demo session loading details
- **backend**: Add background job worker with FastAPI lifecycle
- Complete Phase 1 (Stability) and Phase 3 (Page Hierarchy)
- Campaign-scoped results with improved UI
- Complete Phase 4 with provider selection and E2E infrastructure
- **phase-9**: Add job creation flow with /jobs/new route
- **phase-10**: Enhance jobs list with sorting, filtering, and status updates
- **phase-11**: Upload enhancements with file size, delete scans, duplicate handling
- **frontend**: Campaigns list enhancements (Phase 8)
- **frontend**: Job details and settings enhancements (Phase 10-12)
- **frontend**: Auth and layout polish (Phase 7-12)
- **backend**: Config reset endpoint and OCR improvements (Phase 12)
- **events**: Add typed event definitions
- **events**: Add event bus with auto-source detection
- **events**: Add transport interface
- **supabase**: Add Phase 1 (configuration) and Phase 2 (persistence) implementation
- **security**: Add supply chain protection — minimumReleaseAge, block lifecycle scripts
- **backend**: Add Supabase settings, masking utility, and settings repo improvements
- **backend**: Persistence layer — Supabase engine, Alembic migrations, domain objects
- **backend**: API layer — database endpoints, Supabase service, CLI script
- **frontend**: Add database API types and client methods for Supabase endpoints
- **frontend**: Restructure routes into (app)/(standalone) groups with onboarding components and schema docs
- **docker**: Add health checks, dependency ordering, and Supabase compose overlay
- **backend**: ApiModel camelCase serialization for all API models (Session 4-5)
- Add cross-platform start scripts, simplify Getting Started for non-developers
- Add deploy configs for DO/Render/Railway, production Dockerfiles, deploy buttons
- Add ApplicationStartup lifecycle manager and events router
- Terminate orphaned jobs on restart instead of just detecting
- Validate voter list and OCR provider before job creation

### Fixed

- Ensure column_data is sorted by position_idx in OcrMatchResults
- Repair results table with data conversion, pagination, and simulation toggle
- Resolve frontend SSR errors
- Restore VoteCatcher landing page and add lucide-svelte
- Resolve unit test issues and update progress tracking
- Move simulation toggle before Run Matching button + add debug logging
- Simulation mode now bypasses OCR entirely + fix double-slash URL
- Workspace demo page 500 error - ApiResult type mismatch
- Feature flags API call uses PUBLIC_API_URL instead of relative path
- Workspace API endpoint missing /api prefix
- Add missing leading slash to all BASE_URL API paths
- **backend**: Remove hardcoded database credentials from Alembic config
- Remove unused imports in Sidebar test
- **frontend**: Correct sessions store test method names and DOM mocks
- **backend**: Rename logging module to logger_config
- **demo**: Add selective reset and error handling
- **demo**: Display Campaign ID instead of Session ID
- Update demo.test.ts for new loadedSession state shape
- **backend**: Campaign/job/config routers, file service, demo service
- **demo**: Add demo user for petition_scan FK constraint
- API URL issues and double sidebar
- Return error_message from job error_data in API response
- Save PetitionScan and PetitionCrop records to database during upload
- Job pipeline validation and voter import
- E2E tests and WCAG 2.2 compliance
- Use sync sqlite driver in all env files
- Consistent API port 8080 across all frontend pages
- **worker**: Skip crops with existing OcrResults to prevent UNIQUE constraint errors
- **ocr**: Add ocr_index to support multi-entry OCR results (Issue #14)
- **jobs**: Orphan detection, expanded cancel states, OCR caching (Issues #1, #14)
- **metrics**: Deduplicate confidence counts by ocr_result_id (Issue #15)
- **frontend**: Dashboard metrics and job creation UX (Issues #9, #12)
- Polling optimization, flaky test, and documentation sync
- **ui**: Dropdown clipping and results column order
- Complete P4 polish items via parallel subagents (Session 5)
- Address Phase 3 review feedback (F1, F9, N2, N4)
- Restore SvelteKit package.json, tsconfig, and lockfiles; add pytest-benchmark
- Auto-format backend with ruff, use gitleaks CLI in CI
- Add missing deps, bump CI Node to 22, fix secrets-scan and fallow
- Resolve CI check failures — formatting, unused deps, security scans, Dockerfile
- Resolve 6 CI check failures (secrets-scan, sca, lint, typecheck, bandit, container-scan)
- Resolve 4 CI failures (bundle-size, frontend-typecheck, backend-security, update analysis doc)
- Resolve CI failures and set up typecheck baseline
- Oxfmt .fallowrc.json, fix baseline script for CI, update osv-scanner CLI flags
- Resolve backend/frontend security and container scan failures
- Resolve 7 CI failures — generated API module, SCA PATH, env vars, dep upgrades
- Quick CI fixes — lockfile for Python 3.12, typecheck baseline, frontend type errors
- **backend**: Restore missing entry point, fix import chain, and add missing deps (Session 1-2)
- **backend**: Test infrastructure — FK registration, stale patches, env safety (Session 1-2)
- **backend**: Update tests for camelCase API responses, fix SetupStatusResponse dict fields (Session 6)
- **frontend**: Form data contract — snake_case for form fields (Session 11)
- **frontend**: TypeScript type sync and Svelte 5 warning cleanup (Sessions 13-16, 21)
- **backend**: Detect-secrets compliance + demo service tests (Session 23)
- **ci**: Resolve 6 security/lint/SCA CI failures for PR #14
- **ci**: Resolve sca, typecheck, container-scan, frontend-security, and sast failures
- **ci**: Resolve backend-test and dast-smoke pre-existing failures
- **ci**: Add PUBLIC_DEMO_MODE, fix osv-scanner/nuclei CLI flags, relax codecov
- **ci**: Resolve sca, frontend-test, dast-smoke failures
- **ci**: Add --recursive to osv-scanner, mock PUBLIC_DEMO_MODE, disable uv cache in dast-smoke
- **ci**: Osv-scanner scan from repo root with -r flag
- **test**: Resolve all frontend test failures for Svelte 5 + jsdom compatibility
- **ci**: Multi-line cd persists working dir — chain with &&
- **ci**: Same cd persist bug in frontend Test step
- Replace code quality badge with security workflow, sync Makefile
- Provide PUBLIC_API_URL at build time in frontend prod Dockerfile
- Provide all required env vars at build time in frontend prod Dockerfile
- Add DATABASE_URL build arg for frontend prod Dockerfile
- Remove pragma comment from CI build-arg value
- Use adapter-node for Docker prod builds via ADAPTER env var
- Use dot notation for import.meta.env access
- Accept sqlite+aiosqlite scheme in DatabaseConfig validator
- Use sqlite scheme in DAST CI instead of sqlite+aiosqlite

### Performance

- **ci**: Consolidate workflows, merge quality jobs, add failure summaries
- **ci**: Merge container-scan into docker-build, eliminate 2 redundant image builds

### Changed

- Group name columns together for easier comparison
- **settings**: Complete R13 consolidation — merge AppSettings into Settings, delete env_settings.py
- **ocr**: Delete batching module, consolidate to clients/ — commit 7
- **ocr**: Consolidate provider credentials — ProviderConfig, delete settings_repo, remove LangChain
- Rename frontend-svelt/ to frontend/
- **backend**: Remove dotenv dependency, add pure-Python env parser (Session 8)
- **backend**: Extract ResultsQueryService and CampaignQueryService (Sessions 9-10)
- **backend**: Extract JobQueryService and CampaignManagementService (Sessions 12, 18)
- **backend**: Extract SessionService from session_router (Session 19)
- **backend**: Add vulture whitelist and BDD dead-code tests (Session 17)
- **backend**: Extract ConfigService from config_router (Session 20)
- **backend**: Extract DemoOrchestrationService from demo_router (Session 22)
- **backend**: Complete service layer extractions with BDD coverage (Sessions 24-26)
- Pass session to resolve_provider_config

### Reverted

- Remove sqlite+aiosqlite from DatabaseConfig allowlist

### Security

- Add API key redaction to structlog processor

## [Unreleased](https://github.com/civictechdc/votecatcher/compare/)

### Fixed

- **ci**: Pin git-cliff v2.12.0 with versioned asset name, fix edge function TS errors

<!-- generated by git-cliff -->
