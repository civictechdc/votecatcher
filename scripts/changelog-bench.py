#!/usr/bin/env python3
"""Benchmark changelog summarization across GitHub Models.

Compares free GitHub Models on their ability to transform raw git-cliff output
into a thematic Level 1 (GitHub Release) changelog. Measures quality (leaks,
themes) and latency.

Usage:
    python scripts/changelog-bench.py                         # all free models
    python scripts/changelog-bench.py deepseek/deepseek-v3    # single model
    python scripts/changelog-bench.py --list                  # list available models
    python scripts/changelog-bench.py --range v1..v2          # custom git range

Output:
    .agent-workspace/changelog-samples/benchmarks/bench-<name>.md  — per-model output
    .agent-workspace/changelog-samples/benchmarks/README.md        — summary table

Prerequisites:
    - gh auth login (or GITHUB_TOKEN set)
    - git-cliff installed
    - Run scripts/changelog-models-list.sh first to populate free-models.json
"""

import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

BENCHMARKS_DIR = Path(".agent-workspace/changelog-samples/benchmarks")
MODELS_FILE = BENCHMARKS_DIR / "free-models.json"
PROMPT_FILE = Path("scripts/changelog-prompt.md")
CLIFF_CONFIG = Path("cliff.toml")

LEAK_KEYWORDS = [
    "extract",
    "refactor",
    "consolidat",
    "cleanup",
    "fixture",
    "yield_per",
    "readability",
    "conftest",
    "dead._provider",
    "PredictionBuilder",
    "OcrTextParser",
]


def get_token():
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception:
        pass
    print()
    print("[ERROR] No authentication token found.", file=sys.stderr)
    print("        Run 'gh auth login' or set GITHUB_TOKEN.", file=sys.stderr)
    print()
    sys.exit(1)


def call_model(token, model, system_prompt, user_message, timeout=90):
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
    )
    start = time.time()
    result = subprocess.run(
        [
            "curl",
            "-s",
            "--max-time",
            str(timeout),
            "-X",
            "POST",
            "https://models.github.ai/inference/chat/completions",
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Content-Type: application/json",
            "-H",
            "Accept: application/vnd.github+json",
            "-d",
            payload,
        ],
        capture_output=True,
        text=True,
    )
    elapsed = round(time.time() - start)
    try:
        resp = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "fail",
            "error": f"API returned non-JSON (HTTP {result.returncode}). Raw output: {result.stdout[:200]}",
            "elapsed": elapsed,
        }
    content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        err = resp.get("error", {}).get("message", "empty response")
        code = resp.get("error", {}).get("code", "N/A")
        return {
            "status": "fail",
            "error": f"{err} (code: {code})",
            "elapsed": elapsed,
        }
    return {"status": "ok", "content": content, "elapsed": elapsed}


def count_metrics(content):
    lines = content.count("\n") + 1
    bullets = content.count("\n- ")
    themes = content.count("\n### ")
    leaks = sum(content.lower().count(kw.lower()) for kw in LEAK_KEYWORDS)
    return {"lines": lines, "bullets": bullets, "themes": themes, "leaks": leaks}


def load_models():
    if not MODELS_FILE.exists():
        print()
        print(f"[ERROR] Model catalog not found: {MODELS_FILE}", file=sys.stderr)
        print("        Run this first:", file=sys.stderr)
        print("          bash scripts/changelog-models-list.sh", file=sys.stderr)
        print()
        sys.exit(1)
    with open(MODELS_FILE) as f:
        models = json.load(f)
    if not models:
        print(
            "[ERROR] Model catalog is empty. Re-run scripts/changelog-models-list.sh.",
            file=sys.stderr,
        )
        sys.exit(1)
    return models


def generate_raw(range_spec=None):
    cmd = ["git-cliff", "--config", str(CLIFF_CONFIG)]
    if range_spec:
        cmd.append(range_spec)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] git-cliff failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    raw = result.stdout
    commits = raw.count("\n- ")
    print(
        f"[INFO] Generated raw changelog: {commits} commits, {len(raw.splitlines())} lines"
    )
    return raw


def write_readme(results, range_label):
    tier_limits = {"low": "15/min · 150/day", "high": "10/min · 50/day"}
    rows = []
    for r in results:
        tier_note = tier_limits.get(r["tier"], r["tier"])
        if r["status"] == "fail":
            rows.append(
                f"| `{r['model']}` | — | {r['tier']} | {tier_note} | {r['elapsed']}s | "
                f"— | — | — | — | Failed: {r['error']} |"
            )
            continue
        m = r["metrics"]
        leak_display = f"**{m['leaks']}**" if m["leaks"] == 0 else str(m["leaks"])
        rows.append(
            f"| `{r['model']}` | `bench-{r['short']}.md` | {r['tier']} | {tier_note} | {r['elapsed']}s "
            f"| {m['lines']} | {m['bullets']} | {m['themes']} | {leak_display} | {r['verdict']} |"
        )

    today = date.today().isoformat()
    readme = f"""# Changelog Summarization Benchmarks

**Date:** {today}
**Range:** {range_label}
**Prompt:** `scripts/changelog-prompt.md`
**Leak keywords:** {", ".join(LEAK_KEYWORDS)}

## Results

| Model | File | Tier | Limits | Time | Lines | Bullets | Themes | Leaks | Verdict |
|-------|------|------|--------|------|-------|---------|--------|-------|---------|
{chr(10).join(rows)}

## Terminology

- **Tier / Limits:** Free rate limits (no Copilot subscription needed).
  - `low`: 15 req/min, 150 req/day, 8K tokens in / 4K out
  - `high`: 10 req/min, 50 req/day, 8K tokens in / 4K out
- **Leaks:** Occurrences of internal-only terms (refactor, cleanup, extract, etc).
  Lower is better. **0** = perfect noise filtering.
- **Themes:** Number of `### ` headings (~6 expected for the benchmark input).

## Recommendations

- **CI default:** `deepseek/deepseek-v3-0324` — zero leaks, good filtering, high tier.
- **Fallback:** `openai/gpt-4.1-mini` — low tier (more daily calls), minor refactor leaks.
- **Fastest:** `mistral-ai/mistral-small-2503` — 1s response, zero leaks, under-filters.

## Configuration (CI)

Override the CI model via GitHub org/repo variables:
- `CHANGELOG_MODEL` — model ID (default: `deepseek/deepseek-v3-0324`)
- `CHANGELOG_MIN_COMMITS` — summarization threshold (default: `6`)

## Re-running

```bash
# 1. Update the free model catalog
bash scripts/changelog-models-list.sh

# 2. Run full benchmark (all free models)
python scripts/changelog-bench.py

# 3. Test a single model
python scripts/changelog-bench.py deepseek/deepseek-v3-0324

# 4. Custom git range
python scripts/changelog-bench.py --range v1.0.0-alpha.1..v1.0.0-alpha.5

# 5. List available models
python scripts/changelog-bench.py --list
```
"""
    readme_path = BENCHMARKS_DIR / "README.md"
    readme_path.write_text(readme)
    print(f"\n[OK] Summary written to {readme_path}")


def main():
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)

    # ── Handle --list ──────────────────────────────────────────
    if "--list" in sys.argv:
        models = load_models()
        print(f"{'Model':<50} {'Tier':<6} {'Limits'}")
        print("-" * 80)
        tier_limits = {"low": "15/min · 150/day", "high": "10/min · 50/day"}
        for m in models:
            limits = tier_limits.get(m.get("tier", ""), "?")
            print(f"  {m['id']:<48} {m.get('tier', '?'):<6} {limits}")
        print(f"\n  {len(models)} models. Source: {MODELS_FILE}")
        return

    token = get_token()

    # ── Parse args ─────────────────────────────────────────────
    range_spec = None
    range_label = "latest tag"
    for i, arg in enumerate(sys.argv):
        if arg == "--range" and i + 1 < len(sys.argv):
            range_spec = sys.argv[i + 1]
            range_label = range_spec

    target_model = None
    for arg in sys.argv:
        if arg.startswith("--"):
            continue
        if "/" in arg:
            target_model = arg

    # ── Load models ────────────────────────────────────────────
    models = load_models()
    if target_model:
        models = [m for m in models if target_model in m["id"]]
        if not models:
            print(
                f"\n[ERROR] No model matching '{target_model}' in {MODELS_FILE}",
                file=sys.stderr,
            )
            print("        Run with --list to see available models.", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Testing single model: {models[0]['id']}")

    # ── Generate raw input ─────────────────────────────────────
    prompt = PROMPT_FILE.read_text()
    raw = generate_raw(range_spec)
    user_msg = (
        "Transform this raw git-cliff changelog into a Level 1 GitHub Release changelog "
        "following the rules above. Output ONLY the changelog markdown, no explanation.\n\n---\n\n"
        + raw
    )

    # ── Run benchmarks ─────────────────────────────────────────
    print(f"\n[INFO] Benchmarking {len(models)} models on {range_label}...\n")
    header = f"{'Model':<50} {'Time':>5} {'Lines':>6} {'Bullets':>8} {'Themes':>7} {'Leaks':>7}  Verdict"
    print(header)
    print("-" * len(header))

    results = []
    for m in models:
        model_id = m["id"]
        short = model_id.split("/")[-1]
        tier = m.get("tier", "?")

        res = call_model(token, model_id, prompt, user_msg)
        res["model"] = model_id
        res["short"] = short
        res["tier"] = tier

        if res["status"] == "fail":
            print(
                f"{model_id:<50} {res['elapsed']:>4}s  {'FAIL':>44}  {res['error'][:60]}"
            )
            res["verdict"] = f"Failed: {res['error']}"
            results.append(res)
            continue

        metrics = count_metrics(res["content"])
        res["metrics"] = metrics

        if metrics["leaks"] == 0:
            verdict = "Zero leaks"
        elif metrics["leaks"] <= 3:
            verdict = "Minor leaks"
        elif metrics["leaks"] <= 6:
            verdict = "Moderate leaks"
        else:
            verdict = "High leaks"
        res["verdict"] = verdict

        leak_display = (
            f"**{metrics['leaks']}**"
            if metrics["leaks"] == 0
            else str(metrics["leaks"])
        )
        print(
            f"{model_id:<50} {res['elapsed']:>4}s  {metrics['lines']:>6}  "
            f"{metrics['bullets']:>8}  {metrics['themes']:>7}  {leak_display:>7}  {verdict}"
        )

        (BENCHMARKS_DIR / f"bench-{short}.md").write_text(res["content"])
        results.append(res)

    # ── Write summary ──────────────────────────────────────────
    write_readme(results, range_label)


if __name__ == "__main__":
    main()
