#!/usr/bin/env python3
"""
Convert justfile to Makefile.

Usage:
    python scripts/just-to-make.py > Makefile
    python scripts/just-to-make.py --check  # Exit 1 if out of sync

This handles the subset of just syntax used in this project:
- Simple recipes with optional dependencies
- Variables (alias := "value")
- Export statements
- Recipe arguments with defaults
- [private] and [group] attributes
- Doc comments (# after recipe name)
"""

import argparse
import re
import sys
from pathlib import Path


def parse_justfile(content: str) -> tuple[list[str], list[dict]]:
    """Parse justfile into variables and recipes."""
    lines = content.split("\n")
    variables = []
    recipes = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines and comments
        if (
            not line.strip()
            or line.strip().startswith("#")
            and ":" not in line.split("#")[0]
        ):
            i += 1
            continue

        # Variable: name := "value" or name := 'value'
        var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:=\s*["\'](.*)["\']', line)
        if var_match:
            variables.append(
                {
                    "name": var_match.group(1),
                    "value": var_match.group(2),
                    "export": line.startswith("export "),
                }
            )
            i += 1
            continue

        # Recipe: name: or name: dep1 dep2 or name arg="default":
        # Handles: name, name(arg="default"), name arg="default":
        recipe_match = re.match(
            r'^([a-zA-Z_][a-zA-Z0-9_-]*)\s*(\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_=\s"]*)?\s*:\s*(.*)$',
            line,
        )
        if recipe_match:
            name = recipe_match.group(1)
            params = recipe_match.group(2) or ""
            rest = recipe_match.group(3).strip()

            # Extract doc comment: name: # Description
            doc = ""
            if " #" in rest:
                rest, doc = rest.rsplit(" #", 1)
                doc = doc.strip()
            elif rest.startswith("#"):
                doc = rest[1:].strip()
                rest = ""

            # Extract dependencies
            deps = rest.split() if rest else []

            # Collect recipe body (indented lines)
            body = []
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i] == ""):
                if lines[i]:
                    body.append(lines[i])
                i += 1

            recipes.append(
                {
                    "name": name,
                    "params": params,
                    "deps": deps,
                    "doc": doc,
                    "body": body,
                }
            )
            continue

        i += 1

    return variables, recipes


def generate_makefile(variables: list[dict], recipes: list[dict]) -> str:
    """Generate Makefile from parsed justfile."""
    lines = [
        "# DO NOT EDIT - Generated from justfile by scripts/just-to-make.py",
        "# To update: python scripts/just-to-make.py > Makefile",
        "",
        ".PHONY: " + " ".join(r["name"] for r in recipes),
        "",
    ]

    # Variables
    for var in variables:
        if var["export"]:
            lines.append(f"export {var['name']} := {var['value']}")
        else:
            lines.append(f"{var['name']} := {var['value']}")

    if variables:
        lines.append("")

    # Recipes
    for recipe in recipes:
        # Header
        deps = " ".join(recipe["deps"])
        doc = f" ## {recipe['doc']}" if recipe["doc"] else ""

        # Handle arguments with defaults
        params_str = ""
        if recipe["params"]:
            # Extract: (arg="default") or arg="default" -> MSG=$(or $(MSG),default)
            param_match = re.findall(
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']*)["\']', recipe["params"]
            )
            if param_match:
                params_str = " ".join(
                    f"{p.upper()}=$(or ${p.upper()},{d})" for p, d in param_match
                )

        header = f"{recipe['name']}:{' ' + params_str if params_str else ''}{' ' + deps if deps else ''}{doc}"
        lines.append(header)

        # Body - convert {{var}} to $(VAR)
        for body_line in recipe["body"]:
            # Convert 4-space indent to tab
            make_line = "\t" + body_line.lstrip()
            # Convert just interpolation {{var}} to Make $(VAR)
            make_line = re.sub(
                r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}",
                lambda m: f"$({m.group(1).upper()})",
                make_line,
            )
            lines.append(make_line)

        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Convert justfile to Makefile")
    parser.add_argument(
        "--check", action="store_true", help="Exit 1 if Makefile is out of sync"
    )
    args = parser.parse_args()

    justfile_path = Path(__file__).parent.parent / "justfile"
    makefile_path = Path(__file__).parent.parent / "Makefile"

    if not justfile_path.exists():
        print("Error: justfile not found", file=sys.stderr)
        sys.exit(1)

    content = justfile_path.read_text()
    variables, recipes = parse_justfile(content)
    generated = generate_makefile(variables, recipes)

    if args.check:
        if not makefile_path.exists():
            print("Error: Makefile does not exist", file=sys.stderr)
            sys.exit(1)

        current = makefile_path.read_text()
        if current != generated:
            print("Error: Makefile is out of sync with justfile", file=sys.stderr)
            print("Run: python scripts/just-to-make.py > Makefile", file=sys.stderr)
            sys.exit(1)
        print("Makefile is in sync")
        sys.exit(0)

    print(generated, end="")


if __name__ == "__main__":
    main()
