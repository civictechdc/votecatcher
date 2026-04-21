# VDD Roast Pass 2: changelog-writing skill (post-fix)

**Context:** Fresh review of rewritten skill incorporating all 14 pass-1 findings.

## Verdict: 2 minor findings, 0 high/medium

### Finding 15 (low): Theme ordering rule is Level 1-specific but written as universal

**Location:** Thematic Grouping → Ordering (line 82)
**Problem:** "Within a theme, narrative paragraph first, technical bullets follow." Level 2 uses only narrative paragraphs — no bullets. An agent reading this literally could add bullets to Level 2 themes. The rule only makes sense for Level 1.
**Fix:** Qualify: "For Level 1 themes, narrative paragraph first, technical bullets follow. Level 2 uses only narrative paragraphs."

### Finding 16 (low): "User" is ambiguous in the fuzzy-case key rule

**Location:** Noise Filtering → Key rule (line 65)
**Problem:** "A user would notice something different" — but Level 1 users are developers (who notice API changes, config format, CLI output) and Level 2 users are organizers (who only notice UI-visible changes). The key rule doesn't distinguish. For Level 1, an API breaking change is observable. For Level 2, it isn't.
**Fix:** "A user at the target audience level would notice something different. For Level 1, this includes API shape, config format, and CLI output. For Level 2, only UI-visible changes."

### Non-findings (checked, confirmed fine)

- R2/R3 split resolves F1 correctly
- Tense table resolves F2 correctly — Level 1 example uses past for actions, present for behavior descriptions (standard)
- R1 word/sentence bounds resolve F3 — all example bullets ≤20 words, narratives 2-3 sentences
- Noise filtering table + key rule together handle F6/F8 better than either alone
- Clustering heuristic (scope AND topic) resolves F9 — examples clear
- Size thresholds resolve F11
- Breaking change examples for both levels resolve F13
- 5 common mistakes resolve F14
- Checklist missing R5 (link-to-docs) — too minor to be a standalone finding but worth noting

## Summary

2 low-severity findings. Adversary is now scraping for minor wording ambiguity — not structural flaws, missing edge cases, or contradictions. All 14 original findings properly addressed.

**Pass 1:** 14 findings (6 high, 7 medium, 1 low)
**Pass 2:** 2 findings (0 high, 0 medium, 2 low)

Convergence: the adversary is close to hallucination threshold. One more pass after these fixes would likely produce only invented problems.
