"""Tests for results router — HTTP response wrapping for CSV export."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


@pytest.fixture
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(engine):
    from app.api import app
    from app.dependencies import get_session

    def _override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _seed(session: Session) -> int:
    region = Region(id=uuid4(), region_key="DC", region_name="DC", country_code="US")
    session.add(region)
    session.flush()

    campaign = Campaign(
        id=uuid4(),
        unique_name=f"test-{uuid4().hex[:8]}",
        title="Test",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.flush()

    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="t.pdf",
        stored_path="/tmp/t.pdf",
        file_hash="h",
        page_count=1,
    )
    session.add(scan)
    session.flush()

    job = MatcherJob(
        id=1,
        campaign_id=campaign.id,
        current_status=JobStatus.MATCHING_COMPLETED,
    )
    session.add(job)
    session.flush()

    crop = PetitionCrop(
        scan_id=scan.id,
        crop_index=0,
        stored_path="/tmp/c.png",
        crop_coordinates={"top": 0.0, "bottom": 0.1},
        page_number=1,
    )
    session.add(crop)
    session.flush()

    ocr = OcrResult(crop_id=crop.id, ocr_job_id=1, extracted_text={"name": "A"})
    session.add(ocr)
    session.flush()

    session.add(
        MatchResult(
            matcher_job_id=job.id,
            ocr_result_id=ocr.id,
            voter_id=None,
            rank=1,
            similarity_score=0.9,
            confidence_level=ConfidenceLevel.HIGH,
        )
    )
    session.commit()
    return job.id


class TestExportCsvEndpoint:
    """Feature: CSV export endpoint wraps service result in StreamingResponse."""

    def test_returns_streaming_csv_response(self, client, session):
        """Scenario: Router returns StreamingResponse with correct headers."""
        job_id = _seed(session)

        response = client.get(f"/jobs/{job_id}/results/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert f"job_{job_id}_results.csv" in response.headers.get(
            "content-disposition", ""
        )

    def test_returns_404_for_missing_job(self, client):
        """Scenario: Export for non-existent job returns 404."""
        response = client.get("/jobs/99999/results/export")
        assert response.status_code == 404
