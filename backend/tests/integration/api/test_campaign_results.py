"""Integration tests for campaign results API."""

import uuid as uuid_module
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign


class TestCampaignResultsAPI:
	"""Tests for GET /api/campaigns/{id}/results endpoint."""

	def test_results_empty_campaign(self, client: TestClient, test_campaign: Campaign):
		"""Should return empty results for campaign with no data."""
		response = client.get(f"/api/campaigns/{test_campaign.id}/results")

		assert response.status_code == 200
		data = response.json()

		assert data["results"] == []
		assert data["total"] == 0
		assert data["page"] == 1
		assert data["page_size"] == 50

	def test_results_campaign_not_found(self, client: TestClient):
		"""Should return 404 for non-existent campaign."""
		fake_id = uuid4()
		response = client.get(f"/api/campaigns/{fake_id}/results")

		assert response.status_code == 404
		assert "not found" in response.json()["detail"].lower()

	def test_results_with_match_results(
		self,
		client: TestClient,
		test_campaign: Campaign,
		session: Session,
	):
		"""Should return results with extracted name and address."""
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

		crop = PetitionCrop(
			scan_id=scan.id,
			crop_index=0,
			stored_path=f"{unique_path}_crop_0.png",
			crop_coordinates={},
			page_number=1,
		)
		session.add(crop)
		session.commit()
		session.refresh(crop)

		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
			ended_on=datetime.now(UTC),
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		ocr = OcrResult(
			crop_id=crop.id,
			ocr_job_id=1,
			extracted_text={"name": "John Smith", "address": "123 Main St"},
		)
		session.add(ocr)
		session.commit()
		session.refresh(ocr)

		voter = RegisteredVoter(
			region_id=test_campaign.region_id,
			name_data={"first_name": "John", "last_name": "Small"},
			address_data={
				"street": "456 Oak Ave",
				"city": "DC",
				"state": "DC",
				"zip": "20001",
			},
		)
		session.add(voter)
		session.commit()
		session.refresh(voter)

		match = MatchResult(
			ocr_result_id=ocr.id,
			matcher_job_id=job.id,
			rank=1,
			voter_id=voter.id,
			similarity_score=0.85,
			confidence_level=ConfidenceLevel.HIGH,
		)
		session.add(match)
		session.commit()

		response = client.get(f"/api/campaigns/{test_campaign.id}/results")

		assert response.status_code == 200
		data = response.json()

		assert data["total"] == 1
		assert len(data["results"]) == 1

		result = data["results"][0]
		assert result["extracted_name"] == "John Smith"
		assert result["extracted_address"] == "123 Main St"
		assert result["job_id"] == job.id

		assert len(result["predictions"]) == 1
		prediction = result["predictions"][0]
		assert prediction["voter_name"] == "John Small"
		assert prediction["voter_address"] == "456 Oak Ave, DC, DC, 20001"
		assert prediction["confidence"] == "HIGH"

	def test_results_pagination(
		self,
		client: TestClient,
		test_campaign: Campaign,
		session: Session,
	):
		"""Should paginate results correctly."""
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

		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		for i in range(5):
			crop = PetitionCrop(
				scan_id=scan.id,
				crop_index=i,
				stored_path=f"{unique_path}_crop_{i}.png",
				crop_coordinates={},
				page_number=1,
			)
			session.add(crop)
			session.commit()
			session.refresh(crop)

			ocr = OcrResult(
				crop_id=crop.id,
				ocr_job_id=1,
				extracted_text={"name": f"Name {i}", "address": f"Address {i}"},
			)
			session.add(ocr)
			session.commit()
			session.refresh(ocr)

			match = MatchResult(
				ocr_result_id=ocr.id,
				matcher_job_id=job.id,
				rank=1,
				voter_id=None,
				similarity_score=0.5,
				confidence_level=ConfidenceLevel.LOW,
			)
			session.add(match)
		session.commit()

		response = client.get(
			f"/api/campaigns/{test_campaign.id}/results",
			params={"page": 1, "page_size": 2},
		)

		assert response.status_code == 200
		data = response.json()

		assert data["total"] == 5
		assert len(data["results"]) == 2
		assert data["page"] == 1
		assert data["page_size"] == 2

		response2 = client.get(
			f"/api/campaigns/{test_campaign.id}/results",
			params={"page": 2, "page_size": 2},
		)

		assert response2.status_code == 200
		data2 = response2.json()

		assert data2["total"] == 5
		assert len(data2["results"]) == 2
		assert data2["page"] == 2

	def test_results_confidence_filter(
		self,
		client: TestClient,
		test_campaign: Campaign,
		session: Session,
	):
		"""Should filter by confidence level."""
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

		job = MatcherJob(
			campaign_id=test_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		levels = [ConfidenceLevel.HIGH, ConfidenceLevel.LOW, ConfidenceLevel.HIGH]
		for i, level in enumerate(levels):
			crop = PetitionCrop(
				scan_id=scan.id,
				crop_index=i,
				stored_path=f"{unique_path}_crop_{i}.png",
				crop_coordinates={},
				page_number=1,
			)
			session.add(crop)
			session.commit()
			session.refresh(crop)

			ocr = OcrResult(
				crop_id=crop.id,
				ocr_job_id=1,
				extracted_text={"name": f"Name {i}"},
			)
			session.add(ocr)
			session.commit()
			session.refresh(ocr)

			match = MatchResult(
				ocr_result_id=ocr.id,
				matcher_job_id=job.id,
				rank=1,
				voter_id=None,
				similarity_score=0.5,
				confidence_level=level,
			)
			session.add(match)
		session.commit()

		response = client.get(
			f"/api/campaigns/{test_campaign.id}/results",
			params={"confidence": "HIGH"},
		)

		assert response.status_code == 200
		data = response.json()

		assert data["total"] == 2
		for result in data["results"]:
			assert result["predictions"][0]["confidence"] == "HIGH"
