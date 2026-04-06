"""Tests for config router — settings consolidation (R13)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.settings import Settings, get_settings

RESET_TABLES = [
	"campaigns",
	"match_results",
	"ocr_results",
	"ocr_jobs",
	"matcher_jobs",
	"petition_crops",
	"petition_scans",
]


@pytest.fixture(autouse=True)
def setup_env(tmp_path: Path, monkeypatch):
	monkeypatch.setenv("DEV_LOCAL_RUNTIME_DIR", str(tmp_path / "runtime"))
	monkeypatch.setenv("DEV_LOCAL_RUNTIME_DB_DIR", "database")
	monkeypatch.setenv("DEV_LOCAL_BALLOT_CROP_DIR", "crops")
	monkeypatch.setenv("DEV_LOCAL_PETITION_SCAN_DIR", "petitions")
	monkeypatch.setenv("DEV_LOCAL_CAMPAIGNS_DIR", "campaigns")
	monkeypatch.setenv("DEV_LOCAL_VOTER_REGISTRATION_DIR", "registration")
	monkeypatch.setenv("DEV_LOCAL_OCR_DIR", "ocr")
	get_settings.cache_clear()


@pytest.fixture
def client():
	from app.api import app

	return TestClient(app)


@pytest.fixture
def db_session():
	engine = create_engine(
		"sqlite:///:memory:",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	with Session(engine) as session:
		for table in RESET_TABLES:
			session.exec(
				text(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY)")
			)
		session.commit()
		yield session


class TestResetDataEndpoint:
	"""Verify reset-data endpoint uses Settings (not AppSettings)."""

	def test_reset_rejects_when_no_demo_or_debug(self, client):
		from app.api import app

		mock_settings = Settings(
			FEATURE_ENABLE_SIMULATION=False,
			FEATURE_ENABLE_DEBUG_MODE=False,
			FEATURE_DEMO_MODE=False,
		)
		app.dependency_overrides[get_settings] = lambda: mock_settings
		try:
			response = client.post("/config/reset-data")
			assert response.status_code == 403
		finally:
			app.dependency_overrides.clear()

	def test_reset_accepts_when_demo_mode(self, client, db_session):
		from app.api import app
		from app.dependencies import get_session

		mock_settings = Settings(
			FEATURE_ENABLE_SIMULATION=False,
			FEATURE_ENABLE_DEBUG_MODE=False,
			FEATURE_DEMO_MODE=True,
		)
		app.dependency_overrides[get_settings] = lambda: mock_settings
		app.dependency_overrides[get_session] = lambda: db_session
		try:
			response = client.post("/config/reset-data")
			assert response.status_code == 200
			data = response.json()
			assert "deleted_counts" in data
		finally:
			app.dependency_overrides.clear()

	def test_reset_accepts_when_simulation_mode(self, client, db_session):
		from app.api import app
		from app.dependencies import get_session

		mock_settings = Settings(
			FEATURE_ENABLE_SIMULATION=True,
			FEATURE_ENABLE_DEBUG_MODE=False,
			FEATURE_DEMO_MODE=False,
		)
		app.dependency_overrides[get_settings] = lambda: mock_settings
		app.dependency_overrides[get_session] = lambda: db_session
		try:
			response = client.post("/config/reset-data")
			assert response.status_code == 200
		finally:
			app.dependency_overrides.clear()
