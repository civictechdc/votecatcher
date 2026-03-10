"""Integration tests for session management API endpoints."""

import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api import app
from app.data.database.model.session import Session as SessionModel
from app.data.database.model.session import SessionType
from app.dependencies import get_session


@pytest.fixture
def client(session: Session):
	"""Create test client with overridden database session."""
	app.dependency_overrides[get_session] = lambda: session
	yield TestClient(app)
	app.dependency_overrides.clear()


def test_create_session_success(client: TestClient, test_campaign):
	"""Test creating a new session."""
	response = client.post(
		"/api/sessions",
		json={
			"name": "Test Session",
			"campaign_id": str(test_campaign.id),
			"snapshot_data": {"job_ids": [1, 2], "crop_ids": [3, 4]},
			"session_type": "REAL",
		},
	)

	assert response.status_code == 201
	data = response.json()
	assert data["name"] == "Test Session"
	assert data["campaign_id"] == str(test_campaign.id)
	assert data["session_type"] == "REAL"
	assert data["snapshot_data"] == {"job_ids": [1, 2], "crop_ids": [3, 4]}
	assert "id" in data
	assert "created_at" in data


def test_create_demo_session(client: TestClient):
	"""Test creating a demo session."""
	response = client.post(
		"/api/sessions",
		json={
			"name": "Demo Session",
			"session_type": "DEMO",
			"snapshot_data": {"demo": True},
		},
	)

	assert response.status_code == 201
	data = response.json()
	assert data["session_type"] == "DEMO"


def test_list_sessions(client: TestClient, session: Session):
	"""Test listing all sessions."""
	new_session1 = SessionModel(
		name="List Test Session 1",
		session_type=SessionType.REAL,
		snapshot_data={"test": 1},
	)
	new_session2 = SessionModel(
		name="List Test Session 2",
		session_type=SessionType.DEMO,
		snapshot_data={"test": 2},
	)
	session.add(new_session1)
	session.add(new_session2)
	session.commit()

	response = client.get("/api/sessions")

	assert response.status_code == 200
	data = response.json()
	assert data["total"] >= 2
	assert len(data["sessions"]) >= 2
	session_names = [s["name"] for s in data["sessions"]]
	assert "List Test Session 1" in session_names
	assert "List Test Session 2" in session_names


def test_list_sessions_filter_by_type(client: TestClient, session: Session):
	"""Test listing sessions filtered by type."""
	new_session = SessionModel(
		name="Unique Demo Session Filter Test",
		session_type=SessionType.DEMO,
		snapshot_data={},
	)
	session.add(new_session)
	session.commit()

	response = client.get("/api/sessions?session_type=DEMO")

	assert response.status_code == 200
	data = response.json()
	assert data["total"] >= 1
	for s in data["sessions"]:
		assert s["session_type"] == "DEMO"
	session_names = [s["name"] for s in data["sessions"]]
	assert "Unique Demo Session Filter Test" in session_names


def test_get_session_success(client: TestClient, session: Session):
	"""Test getting a specific session."""
	new_session = SessionModel(
		name="Get Test Session",
		session_type=SessionType.REAL,
		snapshot_data={"key": "value"},
	)
	session.add(new_session)
	session.commit()
	session.refresh(new_session)

	response = client.get(f"/api/sessions/{new_session.id}")

	assert response.status_code == 200
	data = response.json()
	assert data["id"] == new_session.id
	assert data["name"] == "Get Test Session"
	assert data["snapshot_data"] == {"key": "value"}


def test_get_session_not_found(client: TestClient):
	"""Test getting a non-existent session."""
	response = client.get("/api/sessions/99999")

	assert response.status_code == 404
	assert "not found" in response.json()["detail"]


def test_delete_session_success(client: TestClient, session: Session):
	"""Test deleting a session."""
	new_session = SessionModel(
		name="To Delete",
		session_type=SessionType.REAL,
		snapshot_data={},
	)
	session.add(new_session)
	session.commit()
	session.refresh(new_session)
	session_id = new_session.id

	response = client.delete(f"/api/sessions/{session_id}")

	assert response.status_code == 204

	session.expire_all()
	deleted = session.get(SessionModel, session_id)
	assert deleted is None


def test_delete_session_not_found(client: TestClient):
	"""Test deleting a non-existent session."""
	response = client.delete("/api/sessions/99999")

	assert response.status_code == 404


def test_export_session_success(client: TestClient, session: Session):
	"""Test exporting a session as ZIP."""
	new_session = SessionModel(
		name="Export Test",
		session_type=SessionType.REAL,
		snapshot_data={"jobs": [1, 2, 3]},
	)
	session.add(new_session)
	session.commit()
	session.refresh(new_session)

	response = client.get(f"/api/sessions/{new_session.id}/export")

	assert response.status_code == 200
	assert response.headers["content-type"] == "application/zip"
	assert "attachment" in response.headers["content-disposition"]

	zip_buffer = io.BytesIO(response.content)
	with zipfile.ZipFile(zip_buffer, "r") as zip_file:
		assert "session.json" in zip_file.namelist()

		metadata = json.loads(zip_file.read("session.json"))
		assert metadata["name"] == "Export Test"
		assert metadata["snapshot_data"] == {"jobs": [1, 2, 3]}


def test_export_session_not_found(client: TestClient):
	"""Test exporting a non-existent session."""
	response = client.get("/api/sessions/99999/export")

	assert response.status_code == 404
