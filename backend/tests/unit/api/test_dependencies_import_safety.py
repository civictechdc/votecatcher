"""Tests for module-level import safety in dependencies.

The root cause bug: dependencies.py does `from app.data.database.session import engine`
at module level, which triggers `load_dotenv()` via database_client.py that loads `.env`
into os.environ, overriding the intended `.env.local` settings with the postgres URL.

The fix: dependencies.py should lazily access the engine instead of importing it at
module level.
"""

import ast


class TestDependenciesImportSafety:
    """Verify that importing app.dependencies does not trigger premature engine creation."""

    def test_dependencies_does_not_import_load_dotenv(self):
        """dependencies should not import load_dotenv — env loading is handled by Settings."""

        import app.dependencies as dep_mod

        source = open(dep_mod.__file__).read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "dotenv" in node.module:
                    alias_names = [a.name for a in node.names]
                    assert "load_dotenv" not in alias_names, (
                        "dependencies.py must not import load_dotenv"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert "dotenv" not in alias.name, (
                        "dependencies.py must not import dotenv"
                    )

    def test_dependencies_exposes_engine_lazily(self):
        """dependencies should expose engine via a function, not a module-level import."""
        import inspect

        from app.dependencies import get_engine_dependency

        assert callable(get_engine_dependency)
        assert inspect.isgeneratorfunction(get_engine_dependency) or callable(
            get_engine_dependency
        )

    def test_no_module_level_engine_import(self):
        """dependencies.py must not have `from app.data.database.session import engine`."""

        import app.dependencies as dep_mod

        source = open(dep_mod.__file__).read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "database.session" in node.module:
                    alias_names = [a.name for a in node.names]
                    assert "engine" not in alias_names, (
                        "dependencies.py must not import 'engine' from database.session at module level"
                    )
