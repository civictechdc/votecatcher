#!/usr/bin/env bash
# remove-nextjs-ci.py — Surgically remove Next.js frontend CI jobs and justfile recipes
# Usage: python3 scripts/frontend-rename/remove-nextjs-ci.py
#
# Handles structural edits that can't be done with simple find-replace:
#   1. Remove frontend-fallow and frontend-next from ci.yml
#   2. Remove Next.js fallow job from code-quality.yml
#   3. Remove old fallow recipes from justfile (the ones targeting cd frontend)
#   4. Remove Next.js launch config from .vscode/launch.json

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def remove_block(content: str, start_pattern: str, end_pattern: str, label: str) -> str:
    lines = content.split("\n")
    new_lines = []
    skip = False
    found = False
    for i, line in enumerate(lines):
        if not skip and re.search(start_pattern, line):
            skip = True
            found = True
            print(f"  Removing {label} at line {i + 1}")
            continue
        if skip:
            if re.search(end_pattern, line):
                skip = False
            continue
        new_lines.append(line)
    if not found:
        print(f"  WARNING: {label} not found")
    return "\n".join(new_lines)


def process_ci_yml():
    path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    print(f"\nProcessing {path.relative_to(REPO_ROOT)}...")
    content = path.read_text()

    # Remove frontend-next output line
    content = re.sub(
        r"\n\s+frontend-next: \$\{\{ steps\.filter\.outputs\.frontend-next \}\}\n",
        "\n",
        content,
    )

    # Remove frontend-next filter block
    content = re.sub(
        r"\n\s+frontend-next:\n\s+- 'frontend/\*\*'\n",
        "\n",
        content,
    )

    # Remove frontend-fallow job (entire job block)
    content = re.sub(
        r"\n  frontend-fallow:\n    needs: \[changes\].*?(?=\n  \w)",
        "",
        content,
        flags=re.DOTALL,
    )

    # Remove frontend-svelt-fallow job (will be recreated by bulk-replace for ci group)
    # Actually we keep it — it just gets renamed. Skip.

    # Remove frontend-fallow from docker-build needs and condition
    content = content.replace("frontend-fallow, ", "")
    content = content.replace("needs.frontend-fallow.result == 'success' && ", "")

    path.write_text(content)
    print("  Done")


def process_code_quality_yml():
    path = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"
    print(f"\nProcessing {path.relative_to(REPO_ROOT)}...")
    content = path.read_text()

    # Remove the Next.js fallow job block
    content = re.sub(
        r"\n  # Fallow analysis on frontend \(Next\.js\).*?(?=\n  #|\n  -|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    # Also try alternate pattern
    content = re.sub(
        r"\n  fallow-frontend:.*?(?=\n  \w|\n  -|\n#[^\n]*\n  \w|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

    path.write_text(content)
    print("  Done (review manually — YAML block removal is approximate)")


def process_justfile():
    path = REPO_ROOT / "justfile"
    print(f"\nProcessing {path.relative_to(REPO_ROOT)}...")
    content = path.read_text()

    # Remove old fallow recipes that target Next.js frontend/
    # These are the ones with comments like "(frontend — Next.js)"
    recipes_to_remove = [
        r"# Run fallow analysis on frontend \(Next\.js\)\n+fallow:\n\s+cd frontend && npx fallow\n+",
        r"# Run fallow dead-code only \(frontend — Next\.js\)\n+fallow-dead-code:\n\s+cd frontend && npx fallow dead-code\n+",
        r"# Run fallow duplication only \(frontend — Next\.js\)\n+fallow-dupes:\n\s+cd frontend && npx fallow dupes\n+",
        r"# Run fallow complexity only \(frontend — Next\.js\)\n+fallow-health:\n\s+cd frontend && npx fallow health\n+",
        r"# Run fallow audit for PRs \(frontend — Next\.js\)\n+fallow-audit:\n\s+cd frontend && npx fallow audit --base main\n+",
    ]

    for pattern in recipes_to_remove:
        new_content = re.sub(pattern, "", content)
        if new_content != content:
            print(f"  Removed recipe matching: {pattern[:60]}...")
            content = new_content
        else:
            print(f"  WARNING: Recipe not found: {pattern[:60]}...")

    path.write_text(content)
    print("  Done")


def process_vscode_launch():
    path = REPO_ROOT / ".vscode" / "launch.json"
    print(f"\nProcessing {path.relative_to(REPO_ROOT)}...")
    content = path.read_text()

    # Remove the Next.js debug config block (the one with cwd: frontend/)
    # This is approximate — review manually
    content = re.sub(
        r",\s*\{[^}]*\"cwd\"[^}]*frontend/[^}]*\}",
        "",
        content,
        flags=re.DOTALL,
    )

    path.write_text(content)
    print("  Done (review manually)")


def main():
    print("=== Removing Next.js CI/automation references ===")

    process_ci_yml()
    process_code_quality_yml()
    process_justfile()
    process_vscode_launch()

    print("\n=== Done. Review changes with: git diff ===")
    print("NOTE: Some YAML block removals are approximate — verify manually.")


if __name__ == "__main__":
    main()
