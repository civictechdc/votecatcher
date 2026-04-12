"""Integration tests for job management API endpoints.

Tests the complete job lifecycle:
- Job creation
- Job status retrieval
- Job cancellation
- Job start (Phase 9)
- List campaign scans (Phase 9)
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.llm_provider_config import LlmProviderConfig
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload


def _seed_prerequisites(session: Session, campaign: Campaign) -> None:
    upload = VoterListUpload(
        region_id=campaign.region_id,
        original_filename="voters.csv",
        file_size=1024,
        row_count=100,
        status=UploadStatus.ACTIVE,
    )
    session.add(upload)
    provider = LlmProviderConfig(
        provider="openai",
        api_key="sk-test-key-for-integration-tests",  # pragma: allowlist secret
        model="gpt-4o-mini",
        is_configured=True,
    )
    session.add(provider)
    session.flush()


class TestCreateJob:
    """Tests for POST /api/jobs endpoint."""

    def test_create_job_success(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should create matcher job successfully."""
        _seed_prerequisites(session, test_campaign)
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

        assert "jobId" in data
        assert data["status"] == "NOT_STARTED"
        assert data["providerName"] == "openai"
        assert data["providerModel"] == "gpt-4o"
        assert "createdAt" in data

        job = session.get(MatcherJob, data["jobId"])
        assert job is not None
        assert job.campaign_id == test_campaign.id
        assert job.provider_name == "openai"
        assert job.provider_model == "gpt-4o"

    def test_create_job_without_provider(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should create job with null provider fields if not specified."""
        _seed_prerequisites(session, test_campaign)
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

        assert data["providerName"] is None
        assert data["providerModel"] is None

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


class TestGetJob:
    """Tests for GET /api/jobs/{id} endpoint."""

    def test_get_job_success(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return job details."""
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

        assert data["jobId"] == job.id
        assert data["status"] == "NOT_STARTED"
        assert "createdAt" in data

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

    def test_cancel_job_ocr_completed(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should cancel job in OCR_COMPLETED state (orphaned job recovery)."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.OCR_COMPLETED,
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

    def test_cancel_job_matching_pending(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should cancel job in MATCHING_PENDING state (orphaned job recovery)."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.MATCHING_PENDING,
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

    def test_cancel_job_matching_in_progress(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should cancel job in MATCHING state (orphaned job recovery)."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.MATCHING,
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


class TestListCampaignScans:
    """Tests for GET /api/campaigns/{id}/scans endpoint (Phase 9)."""

    def test_list_scans_success(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should list all petition scans for a campaign."""
        petition_scan1 = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="petition1.pdf",
            stored_path=f"/tmp/test1_{uuid.uuid4()}.pdf",
            file_hash=f"hash1_{uuid.uuid4()}",
        )
        petition_scan2 = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="petition2.pdf",
            stored_path=f"/tmp/test2_{uuid.uuid4()}.pdf",
            file_hash=f"hash2_{uuid.uuid4()}",
        )
        session.add(petition_scan1)
        session.add(petition_scan2)
        session.commit()

        response = client.get(f"/api/campaigns/{test_campaign.id}/scans")

        assert response.status_code == 200
        data = response.json()

        assert "scans" in data
        assert data["total"] == 2
        filenames = [s["originalFilename"] for s in data["scans"]]
        assert "petition1.pdf" in filenames
        assert "petition2.pdf" in filenames

    def test_list_scans_empty(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return empty list when campaign has no scans."""
        response = client.get(f"/api/campaigns/{test_campaign.id}/scans")

        assert response.status_code == 200
        data = response.json()

        assert data["scans"] == []
        assert data["total"] == 0

    def test_list_scans_campaign_not_found(self, client: TestClient):
        """Should return 404 for non-existent campaign."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/campaigns/{fake_id}/scans")

        assert response.status_code == 404


class TestStartJob:
    """Tests for POST /api/jobs/{id}/start endpoint (Phase 9)."""

    def test_start_job_success(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should start a NOT_STARTED job."""
        petition_scan = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="test.pdf",
            stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
            file_hash=f"hash_{uuid.uuid4()}",
        )
        session.add(petition_scan)
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.post(f"/api/jobs/{job.id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["OCR_PENDING", "OCR_STARTED"]

    def test_start_job_not_found(self, client: TestClient):
        """Should return 404 for non-existent job."""
        response = client.post("/api/jobs/99999/start")

        assert response.status_code == 404

    def test_start_job_wrong_state(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return 400 for job not in NOT_STARTED state."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.OCR_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.post(f"/api/jobs/{job.id}/start")

        assert response.status_code == 400

    def test_start_job_no_scans(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return 400 when campaign has no petition scans."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.post(f"/api/jobs/{job.id}/start")

        assert response.status_code == 400


class TestJobOrphanStatus:
    """Tests for is_orphaned field in job response (BUG-01 fix)."""

    def test_job_not_orphaned_in_not_started(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Job in NOT_STARTED state should not be marked as orphaned."""
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
        assert data["isOrphaned"] is False

    def test_job_orphaned_in_ocr_started(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Job in OCR_STARTED state should be marked as orphaned."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.OCR_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["isOrphaned"] is True

    def test_job_orphaned_in_matching(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Job in MATCHING state should be marked as orphaned."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.MATCHING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["isOrphaned"] is True

    def test_job_not_orphaned_in_completed(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Job in MATCHING_COMPLETED state should not be marked as orphaned."""
        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["isOrphaned"] is False
