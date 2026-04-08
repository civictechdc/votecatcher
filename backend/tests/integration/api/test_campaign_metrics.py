"""Integration tests for campaign metrics API."""

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
from app.data.database.model.schema import Campaign, Region


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
        """Should return correct metrics for campaign with results.

        After Option B: total_signatures counts OCR results (signatures), not crops.
        """
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

        # Create 8 OCR results (1 per crop for first 8 crops)
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

        # Create 6 match results with varying confidence
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
        # 8 OCR results exist, 6 have matches
        assert data["total_signatures"] == 8
        assert data["processed"] == 6
        assert data["high_confidence"] == 3
        assert data["medium_confidence"] == 2
        assert data["low_confidence"] == 1
        assert data["progress_percentage"] == 75.0  # 6/8 = 75%
        assert data["last_job"]["id"] == job.id
        assert data["last_job"]["status"] == "MATCHING_COMPLETED"

    def test_metrics_deduplicated_by_ocr_result_with_multi_entry_ocr(
        self,
        client: TestClient,
        test_campaign: Campaign,
        session: Session,
    ):
        """Confidence counts should be deduplicated by ocr_result_id.

        After Option B: total_signatures counts OCR results (signatures), not crops.
        Each crop can have multiple OCR results representing individual signatures.
        """
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
        for i in range(2):
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

        # Create 6 OCR results (3 per crop = 6 total individual signatures)
        ocr_results = []
        for crop in crops:
            for ocr_idx in range(3):
                ocr = OcrResult(
                    crop_id=crop.id,
                    ocr_job_id=1,
                    ocr_index=ocr_idx,
                    extracted_text={"name": f"Name {crop.id}_{ocr_idx}"},
                )
                session.add(ocr)
                ocr_results.append(ocr)
        session.commit()
        for ocr in ocr_results:
            session.refresh(ocr)

        # Create match results for all 6 OCR results
        for i, ocr in enumerate(ocr_results):
            level = ConfidenceLevel.HIGH if i < 4 else ConfidenceLevel.MEDIUM
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
        # 6 OCR results (individual signatures), all 6 have matches
        assert data["total_signatures"] == 6
        assert data["processed"] == 6
        assert data["high_confidence"] == 4
        assert data["medium_confidence"] == 2
        assert data["low_confidence"] == 0
        assert data["progress_percentage"] == 100.0  # 6/6 = 100%

    def test_metrics_deduplicated_with_duplicate_match_results(
        self,
        client: TestClient,
        test_campaign: Campaign,
        session: Session,
    ):
        """Metrics should handle duplicate match results gracefully.

        If the same OCR result has multiple match results (e.g., from re-running
        a job), only count it once based on unique ocr_result_id.
        """
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
            ocr_index=0,
            extracted_text={"name": "Name 0"},
        )
        session.add(ocr)
        session.commit()
        session.refresh(ocr)

        # Create 3 duplicate match results for the same OCR result
        for _ in range(3):
            match = MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                voter_id=1,
                similarity_score=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
            session.add(match)
        session.commit()

        response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")
        assert response.status_code == 200
        data = response.json()
        # 1 OCR result = 1 unique match
        assert data["total_signatures"] == 1
        assert data["processed"] == 1
        assert data["high_confidence"] == 1

    def test_metrics_voter_list_count(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return voter list count for campaign."""
        response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")
        assert response.status_code == 200
        data = response.json()

        # Initially no voter list uploaded
        assert "voter_list_count" in data
        assert data["voter_list_count"] is None

        # Add registered voters for the campaign's region
        for i in range(100):
            voter = RegisteredVoter(
                region_id=test_campaign.region_id,
                name_data={"first_name": f"First{i}", "last_name": f"Last{i}"},
                address_data={"street": f"{i} Main St", "city": "Test City"},
            )
            session.add(voter)
        session.commit()

        # Check metrics again
        response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["voter_list_count"] == 100

    def test_metrics_voter_list_count_different_region(
        self, client: TestClient, test_campaign: Campaign, session: Session, test_region
    ):
        """Voter list count should only include voters from campaign's region."""
        from uuid import uuid4

        # Create a different region
        other_region = Region(
            region_key=f"OTHER_{uuid4().hex[:8]}",
            region_name="Other Region",
            country_code="US",
        )
        session.add(other_region)
        session.commit()
        session.refresh(other_region)

        # Add voters to campaign's region
        for i in range(50):
            voter = RegisteredVoter(
                region_id=test_campaign.region_id,
                name_data={"first_name": f"First{i}", "last_name": f"Last{i}"},
                address_data={"street": f"{i} Main St", "city": "Test City"},
            )
            session.add(voter)

        # Add voters to other region
        for i in range(75):
            voter = RegisteredVoter(
                region_id=other_region.id,
                name_data={"first_name": f"Other{i}", "last_name": f"Voter{i}"},
                address_data={"street": f"{i} Other St", "city": "Other City"},
            )
            session.add(voter)
        session.commit()

        # Check metrics - should only count campaign's region
        response = client.get(f"/api/campaigns/{test_campaign.id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["voter_list_count"] == 50
