"""Tests for OCR simulate endpoint."""

import os
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

	from app.settings.env_settings import get_settings

	get_settings.cache_clear()


@pytest.fixture
def client():
	"""Create test client."""
	from app.api import app

	return TestClient(app)


def test_simulate_returns_200(client):
	"""Simulate endpoint should return 200."""
	response = client.get("/workspace/ocr/simulate/test-task-id")
	assert response.status_code == 200


def test_simulate_returns_valid_schema(client):
	"""Simulate should return valid OcrMatchResults schema."""
	response = client.get("/workspace/ocr/simulate/test-task-id")
	data = response.json()

	assert "results" in data
	assert "column_data" in data["results"]
	assert "result_data" in data["results"]
	assert isinstance(data["results"]["column_data"], list)
	assert isinstance(data["results"]["result_data"], list)


def test_simulate_column_data_has_correct_position_idx(client):
	"""Column data should have sequential position_idx."""
	response = client.get("/workspace/ocr/simulate/test-task-id")
	data = response.json()

	positions = [col["position_idx"] for col in data["results"]["column_data"]]
	assert positions == sorted(positions)


def test_simulate_result_count_in_expected_range(client):
	"""Should generate between 50-200 rows."""
	response = client.get("/workspace/ocr/simulate/test-task-id")
	data = response.json()

	assert len(data["results"]["result_data"]) >= 50
	assert len(data["results"]["result_data"]) <= 200


def test_simulate_stats_includes_simulated_flag(client):
	"""Response should include simulated flag in stats."""
	response = client.get("/workspace/ocr/simulate/test-task-id")
	data = response.json()

	assert "stats" in data
	assert data["stats"].get("simulated") is True
