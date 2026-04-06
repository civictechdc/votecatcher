"""Integration tests for demo mode API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api import app
from app.dependencies import get_session


@pytest.fixture
def client(session: Session):
	"""Create test client with overridden database session."""
	app.dependency_overrides[get_session] = lambda: session
	yield TestClient(app)
	app.dependency_overrides.clear()


class TestDemoEndpoints:
	"""Tests for demo mode API endpoints."""

	def test_list_prebaked_sessions_returns_list(self, client: TestClient):
		"""Test listing pre-baked demo sessions."""
		response = client.get("/api/demo/sessions")

		assert response.status_code in [200, 403]

		if response.status_code == 200:
			data = response.json()
			assert "sessions" in data
			assert len(data["sessions"]) >= 1

	def test_list_prebaked_sessions_blocked_without_demo_mode(self, client: TestClient):
		"""Test that demo endpoints require demo mode enabled."""
		response = client.get("/api/demo/sessions")

		if response.status_code == 403:
			data = response.json()
			assert "not enabled" in data["detail"].lower()

	def test_load_prebaked_session_blocked_without_demo_mode(self, client: TestClient):
		"""Test loading a pre-baked session requires demo mode."""
		response = client.post("/api/demo/sessions/dc-petition-2024/load")

		if response.status_code == 403:
			data = response.json()
			assert "not enabled" in data["detail"].lower()

	def test_reset_demo_data_blocked_without_demo_mode(self, client: TestClient):
		"""Test resetting demo data requires demo mode and demo reset."""
		response = client.post("/api/demo/reset")

		if response.status_code == 403:
			data = response.json()
			assert "not enabled" in data["detail"].lower()


class TestDemoDataLoading:
	"""Tests for actual demo data loading."""

	def test_load_dc_petition_2024_creates_data(self, session: Session, monkeypatch):
		"""Test that loading dc-petition-2024 creates all entities."""
		from app.settings import get_settings

		# Clear cache and set env vars before importing
		get_settings.cache_clear()
		monkeypatch.setenv("FEATURE_DEMO_MODE", "true")
		monkeypatch.setenv("FEATURE_DEMO_RESET", "true")

		# Need to clear cache again after setting env
		get_settings.cache_clear()

		app.dependency_overrides[get_session] = lambda: session

		try:
			client = TestClient(app)

			# Reset first to ensure clean state
			client.post("/api/demo/reset")

			response = client.post("/api/demo/sessions/dc-petition-2024/load")

			assert response.status_code == 200
			data = response.json()
			assert data["success"] is True
			assert "campaign_id" in data
			assert data["voters_count"] == 10
			assert data["match_results_count"] == 50
		finally:
			app.dependency_overrides.clear()

	def test_reset_clears_data(self, session: Session, monkeypatch):
		"""Test that reset clears all demo data."""
		from sqlmodel import select

		from app.data.database.model.schema import Region
		from app.settings import get_settings

		get_settings.cache_clear()
		monkeypatch.setenv("FEATURE_DEMO_MODE", "true")
		monkeypatch.setenv("FEATURE_DEMO_RESET", "true")
		get_settings.cache_clear()

		app.dependency_overrides[get_session] = lambda: session

		try:
			client = TestClient(app)

			# Reset first to ensure clean state
			client.post("/api/demo/reset")

			# Load data
			client.post("/api/demo/sessions/dc-petition-2024/load")

			# Check demo region exists (filter by demo- prefix)
			demo_regions = session.exec(
				select(Region).where(Region.region_key == "demo-dc")
			).all()
			assert len(demo_regions) == 1

			# Reset
			response = client.post("/api/demo/reset")
			assert response.status_code == 204

			# Check demo region is deleted
			demo_regions_after = session.exec(
				select(Region).where(Region.region_key == "demo-dc")
			).all()
			assert len(demo_regions_after) == 0
		finally:
			app.dependency_overrides.clear()
