"""Feature flag hygiene enforcement — runs in CI.

Three checks on transitional flags:
1. DEAD: flag referenced nowhere outside its definition -> remove it
2. OSSIFIED: flag checked in code but no else/fallback branch -> flag has no effect
3. ORPHAN: domain file exists but not registered in AllFeatures, or vice versa

Permanent flags are exempt from all checks.

Usage-based, not date-based. A flag is dead when code no longer references it.
A flag is ossified when disabling it would not change behavior (no fallback path).
"""

import re
from pathlib import Path


from app.settings.providers.features import AllFeatures

BACKEND_APP = Path(__file__).resolve().parents[3] / "app"

FEATURES_DIR = BACKEND_APP / "settings" / "providers" / "features"

EXCLUDE_DIRS = {"__pycache__", ".venv", "settings/providers/features"}


def _collect_py_files() -> list[Path]:
    return [
        p
        for p in BACKEND_APP.rglob("*.py")
        if not any(part in EXCLUDE_DIRS for part in p.parts)
    ]


def _grep_codebase(pattern: str) -> list[tuple[Path, int, str]]:
    results = []
    for py_file in _collect_py_files():
        text = py_file.read_text()
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                results.append((py_file, i, line.strip()))
    return results


def _flag_has_else_branch(domain: str, name: str) -> bool:
    for py_file in _collect_py_files():
        text = py_file.read_text()
        lines = text.splitlines()
        pattern = rf"features\.{domain}\.{name}\.enabled"
        for i, line in enumerate(lines):
            if not re.search(pattern, line):
                continue
            if_indent = len(line) - len(line.lstrip())
            for j in range(i + 1, min(i + 30, len(lines))):
                stripped = lines[j].strip()
                if not stripped or stripped.startswith("#"):
                    continue
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                if line_indent < if_indent:
                    break
                if line_indent == if_indent and stripped.startswith("else"):
                    return True
    return False


class TestFeatureFlagHygiene:
    def test_no_dead_transitional_flags(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        dead = []
        for domain, name, flag in transitional:
            if flag.meta.phase.value == "defined":
                continue
            pattern = rf"features\.{domain}\.{name}\.enabled"
            refs = _grep_codebase(pattern)
            if not refs:
                dead.append(f"  features.{domain}.{name}: no code references .enabled")
        assert not dead, (
            "Dead transitional flags found — no code references .enabled. "
            "Remove the flag and its definition:\n" + "\n".join(dead)
        )

    def test_no_ossified_transitional_flags(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        ossified = []
        for domain, name, flag in transitional:
            if flag.meta.phase.value == "defined":
                continue
            pattern = rf"features\.{domain}\.{name}\.enabled"
            refs = _grep_codebase(pattern)
            if not refs:
                continue
            if not _flag_has_else_branch(domain, name):
                ossified.append(
                    f"  features.{domain}.{name}: checked but no else/fallback branch"
                )
        assert not ossified, (
            "Ossified flags found — checked in code but disabling has no effect. "
            "Either add an else branch with the old code path or remove the flag:\n"
            + "\n".join(ossified)
        )

    def test_transitional_flags_have_issue(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        missing = []
        for domain, name, flag in transitional:
            if flag.meta.issue is None:
                missing.append(f"  features.{domain}.{name}")
        assert not missing, (
            "Transitional flags must reference the GitHub issue that introduced them:\n"
            + "\n".join(missing)
        )

    def test_domain_files_match_registry(self):
        domain_files = {
            p.stem
            for p in FEATURES_DIR.glob("*.py")
            if p.stem not in ("__init__", "_base")
        }
        registered = set(AllFeatures.model_fields.keys())
        assert domain_files == registered, (
            f"Mismatch between files on disk and AllFeatures registry.\n"
            f"  Files on disk: {sorted(domain_files)}\n"
            f"  Registered:    {sorted(registered)}\n"
            "Add the file to AllFeatures or remove the orphan file."
        )
