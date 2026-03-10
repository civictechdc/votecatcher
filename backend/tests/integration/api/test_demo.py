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

	def test_list_prebaked_sessions(self, client: TestClient):
		"""Test listing pre-baked demo sessions."""
		response = client.get("/api/demo/sessions")

		assert response.status_code == 200
		data = response.json()
		assert "sessions" in data
		assert len(data["sessions"]) >= 2

	def test_get_demo_status(self, client: TestClient):
		"""Test getting demo mode status."""
		response = client.get("/api/demo/status")

		assert response.status_code == 200
		data = response.json()
		assert "demo_mode_enabled" in data

	def test_load_prebaked_session(self, client: TestClient):
		"""Test loading a pre-baked demo session."""
		response = client.post("/api/demo/sessions/dc-petition-2024/load")

		assert response.status_code == 200
		data = response.json()
		assert data["name"] == "DC Petition Demo 2024"

	def test_reset_demo_data(self, client: TestClient):
		"""Test resetting demo data."""
		response = client.post("/api/demo/reset")

		assert response.status_code == 200
		data = response.json()
		assert data["message"] == "Demo data reset successfully"
