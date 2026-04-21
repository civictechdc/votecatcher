## [1.0.0-alpha.5] — Pre-release

### Crop Images in Results

Added inline crop thumbnails in the results table with expandable rows. Clicking a crop opens a lightbox showing the full image highlighted on its source page. Backend includes a new crop endpoint, thumbnail generation, and concurrency control.

### Matching & Performance

- Added client-side sorting to the results table
- Low-confidence matches filtered automatically via adaptive score-based truncation
- Results pagination moved to SQL-level grouping for large datasets

### Fixed

- Centralized API URL resolution — relative URL 404s resolved
- Crop metadata now included in campaign results endpoint

### Security

- Sanitized all HTML output to prevent injection
- Fixed path traversal vulnerability in image resolution

<!-- Self-assessment:
R1 (One idea per sentence): ✓ Bullets are concise (≤20 words), narrative paragraphs are 2-3 sentences
R2 (Specific verbs): ✓ Used "added", "fixed", "filtered", "moved", "sanitized" — avoided "changed", "improved"
R3 (Standard KaC headings): ✓ Used "Security" for security fixes
R4 (No codenames/internal refs): ✓ Removed EPIC-2, EPIC-6, VDD findings #6 #7 #8, issue #63, test infra items
R5 (Link to docs for unfamiliar concepts): N/A — all concepts are standard web dev terms
R6 (No stability promises for pre-release): ✓ Header notes "— Pre-release"
R7 (Name themes after user capabilities): ✓ "Crop Images in Results" (capability) not "Results Table Enhancement"; "Matching & Performance" (capability) not "Services Refactor"

Noise filtering:
✓ Excluded test-only changes (backend crop_router test import, frontend featureFlags test env)
✓ Excluded internal refactors (Extract PredictionBuilder, consolidate fixtures, readability pass)
✓ Excluded dead code removal (monitor: remove dead _providers)
✓ Excluded cleanup-only changes (stream CSV export with yield_per, wire export_results_csv)
✓ Included user-visible security hardening (HTML sanitization, path traversal fix)
✓ Included performance improvements (SQL pagination, adaptive truncation)

Thematic grouping:
✓ Crop-related commits grouped under "Crop Images in Results" (12 commits share scope: crops + results + frontend, topic: crop/thumbnail)
✓ Sort and truncation grouped under "Matching & Performance" (performance/user capability theme)
✓ Fixes that share no theme consolidated into narrative sentences

Additional notes:
✓ Pre-release handling: shorter entries, less ceremony, focus on new/different features
✓ No internal-only observable behavior included (import shadowing, test env changes excluded)
✓ Breaking changes: None identified in the input
✓ Tense: Past tense used throughout for Level 1
-->
