# Changelog Summarization Benchmarks

**Date:** 2026-04-16
**Range:** v1.0.0-alpha.3..v1.0.0-alpha.5 (26 commits)
**Prompt:** `scripts/changelog-prompt.md` (current)
**Input:** raw git-cliff output (see `../A-raw-git-cliff.md`)

## Results

| Model | File | Tier | Time | Lines | Bullets | Themes | Leaks | Verdict |
|-------|------|------|------|-------|---------|--------|-------|---------|
| `openai/gpt-4.1` | `bench-gpt-4.1.md` | high | 5s | 51 | 22 | 6 | 3 | Best themes, some refactor leaks |
| `openai/gpt-4.1-mini` | `bench-gpt-4.1-mini.md` | low | 8s | 49 | 20 | 6 | 3 | Best quality/cost ratio |
| `openai/gpt-4o` | `bench-gpt-4o.md` | high | 3s | 44 | 22 | 5 | 4 | Fast, more leaks than 4.1 |
| `openai/gpt-4.1-nano` | `bench-gpt-4.1-nano.md` | low | 3s | 39 | 26 | 4 | 7 | High leak rate |
| `mistral-ai/mistral-small-2503` | `bench-mistral-small-2503.md` | low | 1s | 25 | 13 | 3 | **0** | Fastest, zero leaks, under-filters |
| `deepseek/deepseek-v3-0324` | `bench-deepseek-v3-0324.md` | high | 3s | 33 | 14 | 4 | **0** | Zero leaks, good filtering |
| `meta/llama-4-maverick` | `bench-llama-4-maverick-17b-128e-instruct-fp8.md` | high | 2s | 27 | 12 | 4 | 2 | Decent, moderate leaks |
| `meta/llama-4-scout` | `bench-llama-4-scout-17b-16e-instruct.md` | low | 3s | 52 | 21 | 6 | 8 | Worst leaks |
| `meta/llama-3.1-8b` | `bench-meta-llama-3.1-8b-instruct.md` | low | 3s | 46 | 24 | 7 | 7 | Many leaks |
| `microsoft/phi-4` | — | low | — | — | — | — | — | Failed (empty response) |

## Terminology

- **Tier:** `low` = 15 req/min, 150 req/day. `high` = 10 req/min, 50 req/day (bigger models).
- **Leaks:** Count of internal-only terms in output (extract, refactor, consolidate, cleanup, fixture, yield_per, readability, conftest). Lower is better. Zero = perfect noise filtering.
- **Themes:** Number of `### ` headings. 6 is typical for this input (crop images, sorting, predictions, security, API fixes, performance).

## Recommendations

- **CI default:** `openai/gpt-4.1-mini` — best balance of quality, speed, and rate limits (low tier = more daily calls).
- **Zero-leak alternative:** `deepseek/deepseek-v3-0324` — perfect noise filtering but fewer themes (high tier = fewer daily calls).
- **Avoid:** `phi-4` (broken), `llama-3.1-8b` and `llama-4-scout` (high leak rates).

## Rate Limits (free tier, no Copilot)

| Tier | Req/min | Req/day | Tokens in/out |
|------|---------|---------|---------------|
| low | 15 | 150 | 8K/4K |
| high | 10 | 50 | 8K/4K |

## Re-running

```bash
# Generate raw input
git-cliff --config cliff.toml v1.0.0-alpha.3..v1.0.0-alpha.5 -o /tmp/bench-raw.md

# Test a single model
CHANGELOG_FILE=/tmp/bench-raw.md CHANGELOG_MODEL=openai/gpt-4.1-mini bash scripts/changelog-summarize.sh

# Full benchmark — see bench runner in this directory or re-run via the python script
```
