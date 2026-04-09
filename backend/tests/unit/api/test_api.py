"""Tests for app.api module — FastAPI application entry point."""

import importlib


class TestAppCreation:
    """Tests for FastAPI app instance creation."""

    def test_api_module_imports_successfully(self):
        """app.api module must be importable."""
        mod = importlib.import_module("app.api")
        assert hasattr(mod, "app")

    def test_app_is_fastapi_instance(self):
        """app must be a FastAPI instance."""
        from fastapi import FastAPI

        from app.api import app

        assert isinstance(app, FastAPI)

    def test_app_has_root_path_api(self):
        """App must have root_path=/api configured."""
        from app.api import app

        assert app.root_path == "/api"

    def test_app_has_cors_middleware(self):
        """App must have CORS middleware configured."""
        from app.api import app

        cors_middleware = [m for m in app.user_middleware if "CORSMiddleware" in str(m)]
        assert len(cors_middleware) > 0

    def test_app_has_health_endpoint(self):
        """App must expose a /health endpoint."""
        from app.api import app

        route_paths = [r.path for r in app.routes]
        assert "/health" in route_paths

    def test_app_includes_all_routers(self):
        """App must include all expected routers."""
        from app.api import app

        route_paths = [r.path for r in app.routes]
        expected_prefixes = [
            "/campaigns",
            "/config",
            "/database",
            "/demo",
            "/jobs",
            "/settings/providers",
            "/sessions",
            "/upload",
        ]
        for prefix in expected_prefixes:
            matching = [p for p in route_paths if p.startswith(prefix)]
            assert matching, f"No routes found for prefix {prefix}"
