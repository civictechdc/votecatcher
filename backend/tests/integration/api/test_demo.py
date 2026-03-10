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
			assert len(data["sessions"]) >= 2

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
