# Changelog Format Comparison

## Files

| File | Model/Agent | Range | Notes |
|------|------------|-------|-------|
| `A-raw-git-cliff.md` | — | alpha.3..alpha.5 | Raw git-cliff baseline |
| `B-github-release.md` | agent v1 | alpha.3..alpha.5 | Original skill output |
| `B-github-release-v2.md` | agent v2 | alpha.3..alpha.5 | Post-VDD-fix skill output |
| `C-website-public.md` | agent v1 | alpha.3..alpha.5 | Original L2 output |
| `C-website-public-v2.md` | agent v2 | alpha.3..alpha.5 | Post-VDD-fix L2 output |
| `D-alpha1-to-alpha3.md` | agent v2 | alpha.1..alpha.3 | Stress test, both levels |
| `E-gpt4.1-mini-output.md` | gpt-4.1-mini | alpha.3..alpha.5 | CI default model |
| `E-gpt4.1-output.md` | gpt-4.1 | alpha.3..alpha.5 | Full model, cleaner themes |
| `F-final-format-preview.md` | gpt-4.1 | alpha.3..alpha.5 | Final format (cleaned header, KaC in footer) |
| `VDD-adversarial-roast.md` | — | — | Pass 1: 14 findings |
| `VDD-roast-pass2.md` | — | — | Pass 2: 2 minor, converged |
| `subagent-test-results.md` | — | alpha.5 | docs-writer validation |

## What gets filtered at each level

| Change type | A (raw) | B (GitHub Release) | C (Website) |
|------------|:-------:|:------------------:|:-----------:|
| New feature | Yes | Yes | Yes |
| Bug fix (user-facing) | Yes | Yes | Yes |
| Performance improvement | Yes | Yes | Yes |
| Security hardening | Yes | Yes (brief) | Only if user-visible |
| Internal refactoring | Yes | No | No |
| Test reorganization | Yes | No | No |
| Import renames | Yes | No | No |
| Lint/formatting | Yes | No | No |
| CI/build fixes | Yes | No | No |
| Codenames (EPIC, G-series) | In message | Removed | Removed |

## GitHub Copilot for Auto-Summarization

### Free tier
- **Copilot Free**: 50 agent/chat requests per month, 2000 completions. No cloud agent.
- Too limited for automated CI changelog summarization.

### Paid options
| Plan | Cost | What you get | Viable for auto-changelog? |
|------|------|-------------|--------------------------|
| **Copilot Free** | $0 | 50 chat requests/mo | Barely — 1-2 releases/mo is fine, but no API access |
| **Copilot Pro** | $10/user/mo | 300 premium requests, cloud agent, unlimited mini-model | Yes — cloud agent could run as GitHub Action |
| **Copilot Pro+** | $39/user/mo | More premium requests, all models | Overkill for this |

### Most practical option: Copilot Pro ($10/mo)
- Copilot cloud agent can be triggered from GitHub Issues or Actions
- Could be wired to auto-summarize on tag push
- Uses GitHub Actions runners (included)

### Free alternative: GitHub Models API
- GitHub offers free model inference through [GitHub Models](https://github.com/features/models)
- Can call GPT-4o-mini or similar from a GitHub Action workflow
- No Copilot subscription needed
- Would need a custom Action that calls the Models API with the raw changelog
- Free tier has rate limits but sufficient for release-time summarization

### Bottom line
- **Free**: GitHub Models API from a GitHub Action — viable, needs custom script
- **$10/mo**: Copilot Pro — cloud agent handles it natively
- **Already works**: An agent running locally (opencode, Copilot CLI) does it for free during the release workflow
