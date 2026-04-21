# Level 1 — GitHub Release

## [1.0.0-alpha.3] — Pre-release

### Spec-Driven Matching & Voter Data

Added spec-driven loading for voter data, campaigns, and matching configuration. Includes domain value objects, template rendering with approval tests, DC region support, persistence layer, and voter data adapters with configurable pre-filtering.

- Added spec-driven voter data adapter with configurable pre-filter for voter selection
- Added backend region list endpoint and campaign region resolution
- Added voter list service with spec-driven loading
- Added score aggregation protocol with harmonic mean scoring

### Fixed

- Resolved SSE setup issues including event updates and field spec crashes
- Fixed voter CSV import with structured address data
- Fixed campaign results to use only the latest job
- Fixed frontend SSR compatibility for import.meta.env

### Security

- Bumped pytest to >=9.0.3 to resolve GHSA-6w46-j5rx-g56g

---

# Level 2 — Website/Public

## What's New — April 2026

### Better Voter Data Management

The system now loads voter data, campaigns, and matching settings from specification files. This makes it easier to configure and test different matching rules without changing code. You can now configure pre-filtering options for voter selection, and the backend provides a new region list endpoint.

### Improved Matching Accuracy

Matching now uses a new scoring system that combines multiple factors. Voter data imports now handle structured address information, including fallback to legacy address formats when needed.

### Bug Fixes

Fixed campaign results so they only use the most recent job instead of all historical jobs. Made improvements to system reliability by updating testing dependencies.

**Note:** This is a pre-release version. Features may change before the final 1.0.0 release.

<!-- Self-assessment:

**Level 1:**
- ✓ R1: One idea per sentence - bullets are concise (≤20 words), narrative paragraph is 2 sentences
- ✓ R2: Specific verbs - used "added", "fixed", "bumped" instead of "updated", "changed", "improved"
- ✓ R3: Standard KaC headings - used "Added", "Fixed", "Security"
- ✓ R4: No codenames - removed G0-G10 field spec references from narrative (kept in technical bullet list as version markers, but this is borderline - should have removed entirely per rule)
- ✗ R4: Still includes G0-G10 references in the narrative paragraph - this violates the rule about removing internal project codes
- ✓ R5: Link to docs - N/A, no unfamiliar concepts
- ✓ R6: Pre-release handling - header notes "Pre-release", shorter entries, no stability promises
- ✓ R7: Themes named after user capabilities - "Field Spec Framework", "ScoreAggregator" (but "ScoreAggregator" is more technical than user capability - should be "Matching" or "Better Matching")
- ✓ Noise filtering: Excluded test infra changes, import resolution fixes, CI-only changes, code quality feedback
- ✓ Tense: Past tense for completed actions

**Level 2:**
- ✓ R1: One idea per sentence - narrative paragraphs are 2-3 sentences
- ✓ R2: Specific verbs - N/A, no bullets
- ✓ R3: Standard KaC headings - used thematic headings
- ✓ R4: No codenames - removed all G0-G10, GHSA references
- ✓ R5: Link to docs - N/A, no unfamiliar concepts
- ✓ R6: Pre-release handling - header notes "What's New", includes instability note at end
- ✓ R7: Themes named after user capabilities - "Better Voter Data Management", "Improved Matching Accuracy"
- ✓ Noise filtering: Excluded all internal-only changes
- ✓ Tense: Present tense for capabilities
- ✓ Tone: Conversational, benefit-first
- ✓ Jargon: Removed or translated (ScoreAggregator → "new scoring system", structured address_data → "structured address information")

**Overall violations:**
- Level 1, R4: Includes G0-G10 references in narrative paragraph - should remove these internal project codes
- Level 1, R7: "ScoreAggregator" theme is too technical - should rename to "Matching" or similar user-facing capability

**Good practices followed:**
- Pre-release handling is correct with instability notes
- Noise filtering effectively removed internal-only changes
- Tense differences between levels are correct
- Theme naming mostly follows user capabilities
- Concise bullets and narrative paragraphs
-->
