"""Integration tests for campaign metrics API."""

import uuid as uuid_module
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api import app
from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign


@pytest.fixture
def client():
	"""Create test client."""
	return TestClient(app)


class TestCampaignMetricsAPI:
	"""Tests for GET /api/campaigns/{id}/metrics endpoint."""

	def test_metrics_empty_campaign(self, client: TestClient, test_campaign: Campaign):
		"""Should return zero metrics for campaign with no data."""
		response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")

		assert response.status_code == 200
		data = response.json()

		assert data["total_signatures"] == 0
		assert data["processed"] == 0
		assert data["high_confidence"] == 0
		assert data["medium_confidence"] == 0
		assert data["low_confidence"] == 0
		assert data["progress_percentage"] == 0.0
		assert data["last_job"] is None

	def test_metrics_campaign_not_found(self, client: TestClient):
		"""Should return 404 for non-existent campaign."""
		fake_id = uuid4()
		response = client.get(f"/api/campaigns/{fake_id}/metrics")

		assert response.status_code == 404
		assert "not found" in response.json()["detail"].lower()

	def test_metrics_with_processed_results(
		self,
		client: TestClient,
		test_campaign: Campaign,
		session: Session,
	):
		"""Should return correct metrics for campaign with results."""
		unique_path = f"/tmp/test_{uuid_module.uuid4().hex}.pdf"
		scan = PetitionScan(
			campaign_id=test_campaign.id,
			original_filename="test.pdf",
			stored_path=unique_path,
			file_hash=uuid_module.uuid4().hex,
			page_count=1,
		)
		session.add(scan)
		session.commit()
		session.refresh(scan)

		crops = []
		for i in range(10):
			crop = PetitionCrop(
				scan_id=scan.id,
				crop_index=i,
				stored_path=f"{unique_path}_crop_{i}.png",
				crop_coordinates={},
				page_number=1,
			)
			session.add(crop)
			crops.append(crop)
		session.commit()
		for crop in crops:
			session.refresh(crop)

		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
			ended_on=datetime.now(UTC),
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		ocr_results = []
		for i, crop in enumerate(crops[:8]):
			ocr = OcrResult(
				crop_id=crop.id,
				ocr_job_id=1,
				extracted_text={"name": f"Name {i}"},
			)
			session.add(ocr)
			ocr_results.append(ocr)
		session.commit()
		for ocr in ocr_results:
			session.refresh(ocr)

		confidence_levels = [
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.MEDIUM,
			ConfidenceLevel.MEDIUM,
			ConfidenceLevel.LOW,
		]
		for i, (ocr, level) in enumerate(
			zip(ocr_results[:6], confidence_levels, strict=False)
		):
			match = MatchResult(
				ocr_result_id=ocr.id,
				matcher_job_id=job.id,
				rank=1,
				voter_id=i + 1,
				similarity_score=0.9,
				confidence_level=level,
			)
			session.add(match)
		session.commit()

		response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")

		assert response.status_code == 200
		data = response.json()

		assert data["total_signatures"] == 10
		assert data["processed"] == 6
		assert data["high_confidence"] == 3
		assert data["medium_confidence"] == 2
		assert data["low_confidence"] == 1
		assert data["progress_percentage"] == 60.0
		assert data["last_job"]["id"] == job.id
		assert data["last_job"]["status"] == "MATCHING_COMPLETED"
