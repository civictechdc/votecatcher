"""Integration tests for campaign setup-status API."""

import io
import uuid

from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign


class TestSetupStatusAPI:
    """Tests for GET /api/campaigns/{id}/setup-status endpoint."""

    def test_setup_status_empty_campaign(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should return all false for campaign with no uploads."""
        response = client.get(f"/api/campaigns/{test_campaign.id}/setup-status")

        assert response.status_code == 200
        data = response.json()

        assert data["voterList"]["exists"] is False
        assert data["petitions"]["exists"] is False
        assert data["jobs"]["total"] == 0
        assert data["state"] == "empty"

    def test_setup_status_campaign_not_found(self, client: TestClient):
        """Should return 404 for non-existent campaign."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/campaigns/{fake_id}/setup-status")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_setup_status_after_voter_list_upload(
        self,
        client: TestClient,
        test_campaign: Campaign,
    ):
        """Should show voter_list.exists=true after uploading voter list.

        This verifies the fix for the dashboard checkbox not updating after upload.
        """
        csv_content = (
            "First_Name,Last_Name,Street,City,State,Zip\n"
            "John,Doe,123 Main St,Washington,DC,20001\n"
        )
        files = {"file": ("voters.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"campaign_id": str(test_campaign.id)}

        upload_response = client.post("/api/upload/voter-list", files=files, data=data)
        assert upload_response.status_code == 201

        status_response = client.get(f"/api/campaigns/{test_campaign.id}/setup-status")

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["voterList"]["exists"] is True, (
            "voterList.exists should be True after upload"
        )
        assert status_data["voterList"]["rowCount"] == 1
        assert status_data["state"] == "voter_only"

    def test_setup_status_after_petition_upload(
        self,
        client: TestClient,
        test_campaign: Campaign,
    ):
        """Should show petitions.exists=true after uploading petition."""
        pdf_content = b"%PDF-1.4\n%fake pdf content\n%%EOF"
        files = {"file": ("petition.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"campaign_id": str(test_campaign.id)}

        upload_response = client.post("/api/upload/petition", files=files, data=data)
        assert upload_response.status_code == 201

        status_response = client.get(f"/api/campaigns/{test_campaign.id}/setup-status")

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["petitions"]["exists"] is True
        assert status_data["petitions"]["fileCount"] == 1
        assert status_data["state"] == "petitions_only"
