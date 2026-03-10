"""Tests for configuration and feature flags."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.settings.env_settings import AppSettings, get_settings


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

	get_settings.cache_clear()


@pytest.fixture
def client():
	"""Create test client."""
	from app.api import app

	return TestClient(app)


class TestFeatureFlags:
	"""Tests for feature flag configuration."""

	def test_settings_default_values(self):
		"""Feature flags should default to False."""
		settings = AppSettings()

		assert settings.enable_simulation is False
		assert settings.enable_beta_features is False
		assert settings.enable_debug_mode is False

	def test_settings_can_enable_simulation(self):
		"""Feature flag can be enabled via environment."""
		settings = AppSettings(FEATURE_ENABLE_SIMULATION=True)

		assert settings.enable_simulation is True

	def test_settings_can_enable_beta_features(self):
		"""Beta features flag can be enabled."""
		settings = AppSettings(FEATURE_ENABLE_BETA_FEATURES=True)

		assert settings.enable_beta_features is True

	def test_settings_can_enable_debug_mode(self):
		"""Debug mode flag can be enabled."""
		settings = AppSettings(FEATURE_ENABLE_DEBUG_MODE=True)

		assert settings.enable_debug_mode is True

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
		with patch("app.routers.config_route.get_settings") as mock_get_settings:
			mock_settings = AppSettings(FEATURE_ENABLE_SIMULATION=True)
			mock_get_settings.return_value = mock_settings

			response = client.get("/config/features")
			data = response.json()

			assert data["simulationMode"] is True

	def test_feature_endpoint_reflects_enabled_beta_features(self, client):
		"""/config/features should reflect enabled beta features."""
		with patch("app.routers.config_route.get_settings") as mock_get_settings:
			mock_settings = AppSettings(FEATURE_ENABLE_BETA_FEATURES=True)
			mock_get_settings.return_value = mock_settings

			response = client.get("/config/features")
			data = response.json()

			assert data["betaFeatures"] is True

	def test_feature_endpoint_reflects_enabled_debug_mode(self, client):
		"""/config/features should reflect enabled debug mode."""
		with patch("app.routers.config_route.get_settings") as mock_get_settings:
			mock_settings = AppSettings(FEATURE_ENABLE_DEBUG_MODE=True)
			mock_get_settings.return_value = mock_settings

			response = client.get("/config/features")
			data = response.json()

			assert data["debugMode"] is True

	def test_get_settings_caching(self):
		"""get_settings should be cached (singleton)."""
		# Clear the cache first
		get_settings.cache_clear()

		settings1 = get_settings()
		settings2 = get_settings()

		assert settings1 is settings2
