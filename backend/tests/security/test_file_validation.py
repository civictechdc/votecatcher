import io

from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign


class TestFileValidation:
    """Tests for file upload validation security."""

    def test_voter_list_rejects_non_csv(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject non-CSV file for voter list upload."""
        non_csv_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        files = {
            "file": (
                "malware.exe",
                io.BytesIO(non_csv_content),
                "application/x-msdownload",
            )
        }
        data = {"campaign_id": str(test_campaign.id)}

        response = client.post("/api/upload/voter-list", files=files, data=data)

        assert response.status_code == 400

    def test_voter_list_rejects_empty_file(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject empty file for voter list upload."""
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        data = {"campaign_id": str(test_campaign.id)}

        response = client.post("/api/upload/voter-list", files=files, data=data)

        assert response.status_code == 400

    def test_voter_list_rejects_missing_campaign_id(self, client: TestClient):
        """Should reject upload without campaign_id."""
        files = {"file": ("test.csv", io.BytesIO(b"test"), "text/csv")}

        response = client.post("/api/upload/voter-list", files=files)

        assert response.status_code == 422

    def test_petition_rejects_non_pdf(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject non-PDF file for petition upload."""
        non_pdf_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        files = {
            "file": (
                "malware.exe",
                io.BytesIO(non_pdf_content),
                "application/x-msdownload",
            )
        }
        data = {"campaign_id": str(test_campaign.id), "region": "DC"}

        response = client.post("/api/upload/petition", files=files, data=data)

        assert response.status_code == 400

    def test_petition_rejects_empty_file(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject empty file for petition upload."""
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        data = {"campaign_id": str(test_campaign.id), "region": "DC"}

        response = client.post("/api/upload/petition", files=files, data=data)

        assert response.status_code == 400

    def test_voter_list_rejects_oversized_filename(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject upload with extremely long filename (path traversal test)."""
        long_filename = "a" * 1000 + "../../../../etc/passwd"
        files = {"file": (long_filename, io.BytesIO(b"test,data\n"), "text/csv")}
        data = {"campaign_id": str(test_campaign.id)}

        response = client.post("/api/upload/voter-list", files=files, data=data)

        assert response.status_code in [400, 422]
