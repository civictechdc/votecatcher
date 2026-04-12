"""BDD tests: application settings layer must not depend on dotenv directly.

The `dotenv` package (PyPI) is a thin wrapper around `python-dotenv` and is
redundant — `pydantic-settings` already depends on `python-dotenv` for its
own DotEnvSettingsSource.  Our application code should use a pure-Python
.env parser instead of importing from `dotenv`.
"""

import ast
from pathlib import Path

import tomli

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
PYPROJECT = BACKEND_DIR / "pyproject.toml"
ENV_LOADER = BACKEND_DIR / "app" / "settings" / "env_loader.py"
ENV_FILE_SOURCE = BACKEND_DIR / "app" / "settings" / "sources" / "env_file.py"


def _imports_dotenv(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "dotenv" in node.module:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "dotenv" in alias.name:
                    return True
    return False


class TestEnvLoaderDoesNotImportDotenv:
    """env_loader must use a pure-Python .env parser, not dotenv."""

    def test_no_dotenv_import(self):
        source = ENV_LOADER.read_text()
        assert not _imports_dotenv(source), "env_loader.py must not import from dotenv"


class TestEnvFileSourceDoesNotImportDotenv:
    """EnvFileSource must use a pure-Python .env parser, not dotenv."""

    def test_no_dotenv_import(self):
        source = ENV_FILE_SOURCE.read_text()
        assert not _imports_dotenv(source), "env_file.py must not import from dotenv"


class TestPyprojectHasNoDotenvDep:
    """pyproject.toml must not list `dotenv` as a direct dependency."""

    def test_dotenv_not_in_dependencies(self):
        with open(PYPROJECT, "rb") as f:
            data = tomli.load(f)
        deps = data.get("project", {}).get("dependencies", [])
        for dep in deps:
            name = dep.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
            assert name not in ("dotenv", "python-dotenv"), (
                f"Remove `{dep}` from dependencies — "
                f"pydantic-settings brings python-dotenv transitively"
            )
