#!/usr/bin/env bash
# rename-fallow-recipes.py — Rename fallow-svelte-* → fallow-* in justfile
# Usage: python3 scripts/frontend-rename/rename-fallow-recipes.py

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

renames = {
    "fallow-svelte": "fallow",
    "fallow-svelte-dead-code": "fallow-dead-code",
    "fallow-svelte-dupes": "fallow-dupes",
    "fallow-svelte-health": "fallow-health",
    "fallow-svelte-audit": "fallow-audit",
}


def process_justfile():
    path = REPO_ROOT / "justfile"
    print(f"Processing {path.relative_to(REPO_ROOT)}...")
    content = path.read_text()

    for old, new in renames.items():
        if old in content:
            content = content.replace(old, new)
            print(f"  {old} → {new}")
        else:
            print(f"  WARNING: {old} not found")

    # Update comments: "(SvelteKit)" qualifiers can be simplified
    content = content.replace(
        "# Run fallow analysis on frontend-svelt (SvelteKit)",
        "# Run fallow analysis on frontend",
    )
    content = content.replace(
        "# Run fallow dead-code only (frontend-svelt — SvelteKit)",
        "# Run fallow dead-code analysis",
    )
    content = content.replace(
        "# Run fallow duplication only (frontend-svelt — SvelteKit)",
        "# Run fallow duplication analysis",
    )
    content = content.replace(
        "# Run fallow complexity only (frontend-svelt — SvelteKit)",
        "# Run fallow health check",
    )
    content = content.replace(
        "# Run fallow audit for PRs (frontend-svelt — SvelteKit)",
        "# Run fallow audit for PRs",
    )

    path.write_text(content)
    print("  Done")


def main():
    print("=== Renaming fallow-svelte-* recipes → fallow-* ===")
    process_justfile()


if __name__ == "__main__":
    main()
