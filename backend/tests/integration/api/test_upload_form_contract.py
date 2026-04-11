"""BDD contract tests for upload endpoint form data.

Verifies the frontend-backend form data contract for voter list
and petition uploads. Form parameters are matched by exact Python
parameter name — ApiModel aliases do NOT apply to Form() fields.

Feature: Upload form data contract
  As a frontend client
  I want to upload voter lists and petitions via multipart form data
  So that the backend processes them correctly

Scenarios cover:
  - Correct snake_case field names accepted
  - Incorrect field names rejected with 422
  - Missing required fields rejected with 422
  - Response bodies use camelCase (via ApiModel)
"""

import io
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign


def _csv_file(filename: str = "voters.csv") -> tuple[bytes, str]:
    content = b"last_name,first_name\n,Doe,John\n"
    return content, filename


def _pdf_file(filename: str = "petition.pdf") -> tuple[bytes, str]:
    content = b"%PDF-1.4 fake pdf content"
    return content, filename


class TestVoterListUploadFormDataContract:
    """Given a campaign and region exist, the voter list upload endpoint."""

    @patch("app.services.upload_service.FileService")
    def test_accepts_snake_case_campaign_id(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When frontend sends campaign_id in snake_case, the backend accepts it."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.import_voter_list = AsyncMock(return_value=("/tmp/voters.csv", 42))
        content, filename = _csv_file()

        response = client.post(
            "/api/upload/voter-list",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "filePath" in data
        assert "rowCount" in data
        assert "importedCount" in data

    def test_rejects_missing_campaign_id(self, client: TestClient):
        """When frontend omits campaign_id, the backend rejects with 422.

        This documents the bug in uploads.ts store which sends only
        'file' without 'campaign_id' for voter list uploads.
        """
        content, filename = _csv_file()

        response = client.post(
            "/api/upload/voter-list",
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 422

    def test_rejects_region_id_instead_of_campaign_id(
        self, client: TestClient, test_campaign: Campaign
    ):
        """When frontend sends region_id instead of campaign_id, the backend rejects with 422.

        This documents the bug in UploadApi.ts which sends 'region_id'
        for voter list uploads instead of 'campaign_id'.
        """
        content, filename = _csv_file()

        response = client.post(
            "/api/upload/voter-list",
            data={"region_id": str(test_campaign.region_id)},
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 422

    @patch("app.services.upload_service.FileService")
    def test_response_serializes_to_camel_case(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When voter list upload succeeds, response uses camelCase keys."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.import_voter_list = AsyncMock(return_value=("/tmp/voters.csv", 100))
        content, filename = _csv_file()

        response = client.post(
            "/api/upload/voter-list",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "filePath" in data
        assert "rowCount" in data
        assert "importedCount" in data
        assert "file_path" not in data
        assert "row_count" not in data
        assert "imported_count" not in data


class TestPetitionUploadFormDataContract:
    """Given a campaign exists, the petition upload endpoint."""

    @patch("app.services.upload_service.FileService")
    def test_accepts_snake_case_campaign_id(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When frontend sends campaign_id in snake_case, the backend accepts it."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.process_petition_upload = AsyncMock(return_value=(1, 5))
        content, filename = _pdf_file()

        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "scanId" in data
        assert "cropCount" in data

    def test_rejects_missing_campaign_id(self, client: TestClient):
        """When frontend omits campaign_id, the backend rejects with 422."""
        content, filename = _pdf_file()

        response = client.post(
            "/api/upload/petition",
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 422

    @patch("app.services.upload_service.FileService")
    def test_response_serializes_to_camel_case(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When petition upload succeeds, response uses camelCase keys."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.process_petition_upload = AsyncMock(return_value=(10, 3))
        content, filename = _pdf_file()

        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "scanId" in data
        assert "cropCount" in data
        assert "scan_id" not in data
        assert "crop_count" not in data

    @patch("app.services.upload_service.FileService")
    def test_accepts_optional_region_form_field(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When frontend sends optional region field, the backend accepts it."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.process_petition_upload = AsyncMock(return_value=(1, 5))
        content, filename = _pdf_file()

        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id), "region": "NY"},
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 201


class TestApiModelDoesNotApplyToFormData:
    """Verify that ApiModel aliasing is irrelevant for Form() parameters.

    Form() parameters are matched by exact Python function parameter name.
    The camelCase alias_generator only affects JSON response serialization.
    """

    def test_camel_case_campaign_id_rejected(
        self, client: TestClient, test_campaign: Campaign
    ):
        """When frontend sends 'campaignId' (camelCase), the backend rejects with 422.

        This proves Form() fields use exact parameter names, not aliases.
        Frontend must send snake_case 'campaign_id' for form data.
        """
        content, filename = _csv_file()

        response = client.post(
            "/api/upload/voter-list",
            data={"campaignId": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 422
