# VDD Adversarial Roast: changelog-writing skill

## Bead #40: Writing Rules — Contradictions and Gaps

### Finding 1: Verb rule contradicts category headings
**Location:** Rule 3 vs Level 1 Structure
**Problem:** Rule 3 says "not 'Updated' or 'Changed'" but Keep a Changelog uses "Changed" as a legitimate category heading. The GitHub Release example uses `### Fixed` as a heading. The rule conflates sentence-level verbs with section headings.
**Fix:** Split into two rules: "Use specific verbs in bullet items" and "Use standard KaC category names for headings."

### Finding 2: Tense rules are level-specific but written as universal
**Location:** Rule 9, Level 1 example
**Problem:** Rule 9 says "present tense for capabilities" but Level 1 examples use past tense ("Sanitized all HTML output", "Added client-side sorting"). Level 2 examples correctly use present tense ("Results load faster").
**Fix:** Level 1 uses past tense for completed actions. Level 2 uses present tense for capabilities. Make this explicit.

### Finding 3: No sentence length guidance
**Location:** Writing Rules section
**Problem:** Google Technical Writing has an entire module on short sentences. Rule 2 says "one idea per sentence" but gives no concrete bound. A changelog bullet should be one line, one idea. Narrative paragraphs should be 2-3 sentences max.
**Fix:** Add: "Bullet items: aim for ≤20 words. Narrative paragraphs: 2-3 sentences."

### Finding 4: "Define new terms" is wrong for changelogs
**Location:** Rule 5
**Problem:** Changelogs don't teach — they announce. Defining terms inline bloats entries. The correct action is linking to documentation.
**Fix:** Replace with: "Link to documentation for unfamiliar concepts. Don't define terms inline."

### Finding 5: Missing pre-release guidance
**Location:** Entire skill
**Problem:** Keep a Changelog explicitly says "nothing counts before 1.0.0." Pre-release changelogs (alpha, beta) should be shorter, less formal, and acknowledge instability. The skill treats alpha.3 the same as a 2.0.0 release.
**Fix:** Add a "Pre-release handling" section: shorter entries, no promises about stability, note that features may change.

---

## Bead #41: Noise Filtering Matrix — Edge Cases

### Finding 6: "User-facing" vs "internal" distinction requires judgment the matrix can't encode
**Location:** Noise Filtering Matrix rows for `fix(x): fix Y`
**Problem:** The matrix has two rows: `fix(x): fix Y (user-facing)` → Yes, `fix(x): fix Y (internal)` → No. But the ONLY way to tell them apart is semantic judgment the agent must make. The matrix pretends to be deterministic but requires exactly the fuzzy human judgment it's supposed to replace.
**Fix:** Replace the two rows with a single rule: "Include fixes that change observable behavior. Exclude fixes that only affect test infrastructure, import resolution, or internal error paths."

### Finding 7: `refactor(x): speed up Y 10x` has no threshold
**Location:** Matrix row for refactor with performance
**Problem:** What counts as "speed up"? 10x is obvious. 1.2x? Is that a performance improvement or just optimization? The matrix has no threshold for when a refactor becomes a performance entry.
**Fix:** Add: "Include refactor commits that mention specific performance improvements (faster, speedup, latency, memory). Exclude generic 'optimize' or 'clean up'."

### Finding 8: Missing row for `feat(x): add Y` that's purely internal
**Location:** Matrix
**Problem:** Not all `feat:` commits are user-facing. `feat(ci): add new workflow` is a feature commit but purely internal. The matrix says `feat(x): add Y` → Yes for both audiences. Wrong.
**Fix:** Add row: `feat(ci/build/deps): add Y` → GitHub Release: only if it changes the build experience. Website: No.

---

## Bead #42: Thematic Grouping Algorithm — Ambiguity

### Finding 9: "2+ related commits → theme" is too vague
**Location:** Thematic grouping rule 1
**Problem:** "Related" by what metric? Same scope? Same keyword? Same feature area? The agent needs a clustering heuristic, not a vague instruction. Current rule would let an agent group `feat(results): add sort` with `fix(results): fix pagination` because they share scope `results` — but they're unrelated features.
**Fix:** "Cluster commits that contribute to the same user capability. Signals: shared scope AND shared topic keyword (crop, sort, export, match). Two commits sharing only scope but not topic → separate items."

### Finding 10: No ordering guidance within a version
**Location:** Thematic grouping algorithm
**Problem:** After clustering, what order do themes appear? Most impactful first? Alphabetical? Chronological? The skill says nothing.
**Fix:** Add: "Order themes by impact — new features first, then improvements, then fixes. Within a theme, narrative paragraph first, technical bullets follow."

### Finding 11: No guidance on when NOT to use themes
**Location:** Thematic grouping rules
**Problem:** A version with 2 commits doesn't need themes. A version with 40 commits might need sub-themes. The skill has no guidance on minimum version size for thematic grouping vs flat bullets.
**Fix:** Add: "If a version has ≤5 commits, use flat category bullets (no themes). If 6-15 commits, use themes. If 16+, consider sub-grouping within themes."

---

## Bead #43: Examples vs Real Output

### Finding 12: Level 2 example violates own rules
**Location:** Level 2 example, "Bug Fixes" section
**Problem:** Rule says "narrative paragraphs over bullet lists" but the Bug Fixes section uses bullet lists. And "Improved security for image handling and modal dialogs" is vague — violates the "concrete examples" rule.
**Fix:** Either convert Bug Fixes to a narrative paragraph or add an exception: "Minor fixes may use bullets if they don't share a theme."

### Finding 13: No example of a breaking change
**Location:** Both Level 1 and Level 2 sections
**Problem:** The include lists mention "Breaking changes (always, with migration guidance)" but no example shows how to write one. This is the single most important category to get right — it prevents upgrade disasters.
**Fix:** Add breaking change example to both levels:
```
### Breaking Changes

**Campaign results endpoint now returns paginated responses.**
Previously returned all results as a single array. Migration: add `?page=1&limit=50`
query parameters. See [docs link] for full migration guide.
```

### Finding 14: No negative examples
**Location:** Entire skill
**Problem:** The skill only shows what TO do. No examples of what NOT to do. Google Technical Writing explicitly uses before/after examples. The OpenSSL CHANGES.md we reviewed is a perfect negative example — drowning in API function names.
**Fix:** Add "Common mistakes" section with before/after examples.

---

## Summary: 14 Findings, 0 Hallucinated

All findings are concrete, locatable in the skill text, and fixable. The adversary has NOT reached hallucination — these are real gaps. Need one more pass after fixes.
