"""Integration tests for job management API endpoints.

Tests the complete job lifecycle:
- Job creation
- Job status retrieval
- Job cancellation
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign


class TestCreateJob:
	"""Tests for POST /api/jobs endpoint."""

	def test_create_job_success(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should create matcher job successfully."""
		petition_scan = PetitionScan(
			campaign_id=test_campaign.id,
			original_filename="test.pdf",
			stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
			file_hash=f"hash_{uuid.uuid4()}",
		)
		session.add(petition_scan)
		session.commit()

		response = client.post(
			"/api/jobs",
			json={
				"campaign_id": str(test_campaign.id),
				"scan_ids": [],
				"provider_name": "openai",
				"provider_model": "gpt-4o",
			},
		)

		assert response.status_code == 201
		data = response.json()

		assert "job_id" in data
		assert data["status"] == "NOT_STARTED"
		assert data["provider_name"] == "openai"
		assert data["provider_model"] == "gpt-4o"
		assert "created_at" in data

		job = session.get(MatcherJob, data["job_id"])
		assert job is not None
		assert job.campaign_id == test_campaign.id
		assert job.provider_name == "openai"
		assert job.provider_model == "gpt-4o"

	def test_create_job_without_provider(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should create job with null provider fields if not specified."""
		petition_scan = PetitionScan(
			campaign_id=test_campaign.id,
			original_filename="test.pdf",
			stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
			file_hash=f"hash_{uuid.uuid4()}",
		)
		session.add(petition_scan)
		session.commit()

		response = client.post(
			"/api/jobs",
			json={
				"campaign_id": str(test_campaign.id),
				"scan_ids": [],
			},
		)

		assert response.status_code == 201
		data = response.json()

		assert data["provider_name"] is None
		assert data["provider_model"] is None

	def test_create_job_no_petition_scans(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should return 400 if campaign has no petition scans."""
		response = client.post(
			"/api/jobs",
			json={
				"campaign_id": str(test_campaign.id),
				"scan_ids": [],
				"provider_name": "openai",
			},
		)

		assert response.status_code == 400
		data = response.json()
		assert "No petition scans" in data["detail"]

	def test_create_job_invalid_campaign(self, client: TestClient, session: Session):
		"""Should return 404 for non-existent campaign."""
		import uuid

		response = client.post(
			"/api/jobs",
			json={
				"campaign_id": str(uuid.uuid4()),
				"scan_ids": [],
				"provider_name": "openai",
			},
		)

		assert response.status_code == 404

	def test_create_job_missing_fields(self, client: TestClient):
		"""Should return 422 for missing required fields."""
		response = client.post("/api/jobs", json={})

		assert response.status_code == 422


class TestGetJob:
	"""Tests for GET /api/jobs/{id} endpoint."""

	def test_get_job_success(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should return job status."""
		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.NOT_STARTED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		response = client.get(f"/api/jobs/{job.id}")

		assert response.status_code == 200
		data = response.json()

		assert data["job_id"] == job.id
		assert data["status"] == "NOT_STARTED"
		assert "created_at" in data

	def test_get_job_not_found(self, client: TestClient):
		"""Should return 404 for non-existent job."""
		response = client.get("/api/jobs/99999")

		assert response.status_code == 404


class TestCancelJob:
	"""Tests for POST /api/jobs/{id}/cancel endpoint."""

	def test_cancel_job_success(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should cancel job in NOT_STARTED state."""
		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.NOT_STARTED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		response = client.post(f"/api/jobs/{job.id}/cancel")

		assert response.status_code == 200
		data = response.json()

		assert data["status"] == "CANCELLED"

		session.refresh(job)
		assert job.current_status == JobStatus.CANCELLED

	def test_cancel_job_not_found(self, client: TestClient):
		"""Should return 404 for non-existent job."""
		response = client.post("/api/jobs/99999/cancel")

		assert response.status_code == 404

	def test_cancel_job_invalid_state(
		self, client: TestClient, test_campaign: Campaign, session: Session
	):
		"""Should return 400 for job in non-cancelable state."""
		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		response = client.post(f"/api/jobs/{job.id}/cancel")

		assert response.status_code == 400
