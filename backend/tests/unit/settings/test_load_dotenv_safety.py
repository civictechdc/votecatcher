"""Tests for module-level load_dotenv safety.

Ensures that no app module calls bare load_dotenv() which would load .env
with incorrect priority, overriding the Settings-managed env file resolution.

The Settings system handles env file priority:
  ENV_FILE env var → .env.dev/.env.local → .env (fallback)

Bare load_dotenv() bypasses this and always loads .env first.
"""

import ast
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
APP_DIR = BACKEND_DIR / "app"

MODULES_WITH_LOAD_DOTENV = [
    "app/data/database_client.py",
    "app/common/data/supabase_client.py",
    "app/matching/fuzzy_match_helper.py",
    "app/ocr/ocr_helper.py",
]


class TestNoBareLoadDotenv:
    """Verify no module calls bare load_dotenv() at module level."""

    @staticmethod
    def _has_bare_load_dotenv(source: str) -> bool:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Name)
                    and func.id == "load_dotenv"
                    and not node.args
                    and not node.keywords
                ):
                    return True
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "load_dotenv"
                    and not node.args
                    and not node.keywords
                ):
                    return True
        return False

    def test_database_client_no_bare_load_dotenv(self):
        path = BACKEND_DIR / "app/data/database_client.py"
        assert not self._has_bare_load_dotenv(path.read_text()), (
            "database_client.py must not call bare load_dotenv()"
        )

    def test_supabase_client_no_bare_load_dotenv(self):
        path = BACKEND_DIR / "app/common/data/supabase_client.py"
        assert not self._has_bare_load_dotenv(path.read_text()), (
            "supabase_client.py must not call bare load_dotenv()"
        )

    def test_fuzzy_match_helper_no_bare_load_dotenv(self):
        path = BACKEND_DIR / "app/matching/fuzzy_match_helper.py"
        assert not self._has_bare_load_dotenv(path.read_text()), (
            "fuzzy_match_helper.py must not call bare load_dotenv()"
        )

    def test_ocr_helper_no_bare_load_dotenv(self):
        path = BACKEND_DIR / "app/ocr/ocr_helper.py"
        assert not self._has_bare_load_dotenv(path.read_text()), (
            "ocr_helper.py must not call bare load_dotenv()"
        )
