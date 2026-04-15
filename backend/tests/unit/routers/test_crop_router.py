"""Unit tests for crop image router — GET /api/crops/{crop_id}/image."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

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


def _seed_crop(session: Session, stored_path: str) -> int:
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
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc",
        page_count=1,
    )
    session.add(scan)
    session.flush()
    crop = PetitionCrop(
        scan_id=scan.id,
        crop_index=0,
        stored_path=stored_path,
        crop_coordinates={},
        page_number=1,
    )
    session.add(crop)
    session.flush()
    session.commit()
    return crop.id


class TestCropImageEndpoint:
    """Feature: Crop image serving endpoint.

    As an API consumer
    I want to fetch crop thumbnail images by crop ID
    So that I can display them in the results table.
    """

    def test_returns_200_with_png_for_existing_crop(self, client, session, tmp_path):
        """Scenario: Crop exists with valid PNG file."""
        png_file = tmp_path / "crop_001.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        crop_id = _seed_crop(session, stored_path=str(png_file))

        response = client.get(f"/api/crops/{crop_id}/image")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_cache_control_header_present(self, client, session, tmp_path):
        """Scenario: Response includes immutable cache header."""
        png_file = tmp_path / "crop_002.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        crop_id = _seed_crop(session, stored_path=str(png_file))

        response = client.get(f"/api/crops/{crop_id}/image")

        assert response.status_code == 200
        assert "public" in response.headers["cache-control"]
        assert "max-age=86400" in response.headers["cache-control"]
        assert "immutable" in response.headers["cache-control"]

    def test_returns_404_for_missing_crop(self, client):
        """Scenario: Crop ID not in database."""
        response = client.get("/api/crops/999999/image")

        assert response.status_code == 404

    def test_returns_404_when_file_deleted_from_disk(self, client, session):
        """Scenario: Crop in DB but file missing from disk."""
        crop_id = _seed_crop(session, stored_path="/nonexistent/crop.png")

        response = client.get(f"/api/crops/{crop_id}/image")

        assert response.status_code == 404

    def test_returns_actual_file_bytes(self, client, session, tmp_path):
        """Scenario: Response body matches the file on disk."""
        content = b"\x89PNG\r\n\x1a\n" + bytes(range(256))
        png_file = tmp_path / "crop_003.png"
        png_file.write_bytes(content)
        crop_id = _seed_crop(session, stored_path=str(png_file))

        response = client.get(f"/api/crops/{crop_id}/image")

        assert response.status_code == 200
        assert response.content == content
