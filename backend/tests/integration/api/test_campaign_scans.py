"""Integration tests for campaign scans API endpoints (Phase 11).

Tests the petition scan management:
- List scans with file size
- Delete individual scans
"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign


class TestListCampaignScansPhase11:
    """Tests for GET /api/campaigns/{id}/scans with file_size."""

    def test_list_scans_includes_file_size(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should include file_size in scan response."""
        petition_scan = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="petition.pdf",
            stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
            file_hash=f"hash_{uuid.uuid4()}",
            file_size=1024,
        )
        session.add(petition_scan)
        session.commit()

        response = client.get(f"/api/campaigns/{test_campaign.id}/scans")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["scans"][0]["fileSize"] == 1024

    def test_list_scans_file_size_null_when_missing(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return null for file_size if not set (legacy data)."""
        petition_scan = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="petition.pdf",
            stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
            file_hash=f"hash_{uuid.uuid4()}",
        )
        session.add(petition_scan)
        session.commit()

        response = client.get(f"/api/campaigns/{test_campaign.id}/scans")

        assert response.status_code == 200
        data = response.json()
        assert data["scans"][0]["fileSize"] is None


class TestDeleteCampaignScan:
    """Tests for DELETE /api/campaigns/{id}/scans/{scan_id} endpoint."""

    def test_delete_scan_success(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should delete a petition scan."""
        petition_scan = PetitionScan(
            campaign_id=test_campaign.id,
            original_filename="to_delete.pdf",
            stored_path=f"/tmp/test_{uuid.uuid4()}.pdf",
            file_hash=f"hash_{uuid.uuid4()}",
        )
        session.add(petition_scan)
        session.commit()
        session.refresh(petition_scan)
        scan_id = petition_scan.id

        response = client.delete(f"/api/campaigns/{test_campaign.id}/scans/{scan_id}")

        assert response.status_code == 204

        response = client.get(f"/api/campaigns/{test_campaign.id}/scans")
        data = response.json()
        assert data["total"] == 0

    def test_delete_scan_not_found(self, client: TestClient, test_campaign: Campaign):
        """Should return 404 for non-existent scan."""
        response = client.delete(f"/api/campaigns/{test_campaign.id}/scans/99999")

        assert response.status_code == 404

    def test_delete_scan_wrong_campaign(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Should return 404 if scan belongs to different campaign."""
        from app.data.database.model.schema import Region

        other_region = Region(
            region_key="OTHER", region_name="Other Region", country_code="US"
        )
        session.add(other_region)
        session.commit()
        session.refresh(other_region)

        other_campaign = Campaign(
            title="Other Campaign",
            unique_name="other-campaign",
            year="2024",
            region_id=other_region.id,
        )
        session.add(other_campaign)
        session.commit()
        session.refresh(other_campaign)

        petition_scan = PetitionScan(
            campaign_id=other_campaign.id,
            original_filename="other.pdf",
            stored_path=f"/tmp/other_{uuid.uuid4()}.pdf",
            file_hash=f"hash_{uuid.uuid4()}",
        )
        session.add(petition_scan)
        session.commit()
        session.refresh(petition_scan)

        response = client.delete(
            f"/api/campaigns/{test_campaign.id}/scans/{petition_scan.id}"
        )

        assert response.status_code == 404

    def test_delete_scan_campaign_not_found(self, client: TestClient, session: Session):
        """Should return 404 for non-existent campaign."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/campaigns/{fake_id}/scans/1")

        assert response.status_code == 404
