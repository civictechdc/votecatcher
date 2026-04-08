"""Tests for configuration and feature flags."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_env(tmp_path: Path, monkeypatch):
    """Set up required environment variables for tests."""
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()

    monkeypatch.setenv("DEV_LOCAL_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("DEV_LOCAL_RUNTIME_DB_DIR", "database")
    monkeypatch.setenv("DEV_LOCAL_BALLOT_CROP_DIR", "crops")
    monkeypatch.setenv("DEV_LOCAL_PETITION_SCAN_DIR", "petitions")
    monkeypatch.setenv("DEV_LOCAL_CAMPAIGNS_DIR", "campaigns")
    monkeypatch.setenv("DEV_LOCAL_VOTER_REGISTRATION_DIR", "registration")
    monkeypatch.setenv("DEV_LOCAL_OCR_DIR", "ocr")

    monkeypatch.delenv("FEATURE_ENABLE_SIMULATION", raising=False)
    monkeypatch.delenv("FEATURE_ENABLE_BETA_FEATURES", raising=False)
    monkeypatch.delenv("FEATURE_ENABLE_DEBUG_MODE", raising=False)
    monkeypatch.delenv("FEATURE_DEMO_MODE", raising=False)
    monkeypatch.delenv("FEATURE_DEMO_RESET", raising=False)
    monkeypatch.setenv("SETTINGS_ENV_FILE", str(tmp_path / ".env.test"))

    from app.settings import get_settings

    get_settings.cache_clear()


@pytest.fixture
def client():
    """Create test client."""
    from app.api import app

    return TestClient(app)


class TestFeatureFlags:
    """Tests for feature flag configuration."""

    def test_settings_default_values(self, tmp_path: Path, monkeypatch):
        """Feature flags should default to False when no env vars are set."""
        from app.settings import get_settings

        monkeypatch.delenv("FEATURE_ENABLE_SIMULATION", raising=False)
        monkeypatch.delenv("FEATURE_ENABLE_BETA_FEATURES", raising=False)
        monkeypatch.delenv("FEATURE_ENABLE_DEBUG_MODE", raising=False)
        monkeypatch.delenv("FEATURE_DEMO_MODE", raising=False)
        monkeypatch.delenv("FEATURE_DEMO_RESET", raising=False)
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.feature_simulation is False
        assert settings.feature_beta is False
        assert settings.feature_debug is False

    def test_settings_can_enable_simulation(self):
        """Feature flag can be enabled via environment."""
        from app.settings import Settings

        settings = Settings(FEATURE_ENABLE_SIMULATION=True)

        assert settings.feature_simulation is True

    def test_settings_can_enable_beta_features(self):
        """Beta features flag can be enabled."""
        from app.settings import Settings

        settings = Settings(FEATURE_ENABLE_BETA_FEATURES=True)

        assert settings.feature_beta is True

    def test_settings_can_enable_debug_mode(self):
        """Debug mode flag can be enabled."""
        from app.settings import Settings

        settings = Settings(FEATURE_ENABLE_DEBUG_MODE=True)

        assert settings.feature_debug is True

    def test_feature_endpoint_returns_simulation_flag(self, client):
        """/config/features should return simulationMode."""
        response = client.get("/config/features")

        assert response.status_code == 200
        data = response.json()
        assert "simulationMode" in data
        assert isinstance(data["simulationMode"], bool)

    def test_feature_endpoint_returns_beta_flag(self, client):
        """/config/features should return betaFeatures."""
        response = client.get("/config/features")

        assert response.status_code == 200
        data = response.json()
        assert "betaFeatures" in data
        assert isinstance(data["betaFeatures"], bool)

    def test_feature_endpoint_returns_debug_flag(self, client):
        """/config/features should return debugMode."""
        response = client.get("/config/features")

        assert response.status_code == 200
        data = response.json()
        assert "debugMode" in data
        assert isinstance(data["debugMode"], bool)

    def test_feature_endpoint_reflects_enabled_simulation(self, client):
        """/config/features should reflect enabled simulation flag."""
        from app.api import app
        from app.settings import Settings, get_settings

        mock_settings = Settings(FEATURE_ENABLE_SIMULATION=True)

        app.dependency_overrides[get_settings] = lambda: mock_settings
        try:
            response = client.get("/config/features")
            data = response.json()

            assert data["simulationMode"] is True
        finally:
            app.dependency_overrides.clear()

    def test_feature_endpoint_reflects_enabled_beta_features(self, client):
        """/config/features should reflect enabled beta features."""
        from app.api import app
        from app.settings import Settings, get_settings

        mock_settings = Settings(FEATURE_ENABLE_BETA_FEATURES=True)

        app.dependency_overrides[get_settings] = lambda: mock_settings
        try:
            response = client.get("/config/features")
            data = response.json()

            assert data["betaFeatures"] is True
        finally:
            app.dependency_overrides.clear()

    def test_feature_endpoint_reflects_enabled_debug_mode(self, client):
        """/config/features should reflect enabled debug mode."""
        from app.api import app
        from app.settings import Settings, get_settings

        mock_settings = Settings(FEATURE_ENABLE_DEBUG_MODE=True)

        app.dependency_overrides[get_settings] = lambda: mock_settings
        try:
            response = client.get("/config/features")
            data = response.json()

            assert data["debugMode"] is True
        finally:
            app.dependency_overrides.clear()

    def test_get_settings_caching(self):
        """get_settings should be cached (singleton)."""
        from app.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
