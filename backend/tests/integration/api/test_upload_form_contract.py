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
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign


@pytest.fixture(autouse=True)
def tmp_upload_dir(tmp_path, monkeypatch):
    """Route all upload disk writes into tmp_path, not backend/uploads."""
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    return upload_dir


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
    def test_rejects_unsupported_region_form_field(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """Only DC is supported; other regions are rejected with 400 before
        any file processing."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.process_petition_upload = AsyncMock(return_value=(1, 5))
        content, filename = _pdf_file()

        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id), "region": "NY"},
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 400
        assert "DC" in response.json()["detail"]
        mock_fs.process_petition_upload.assert_not_awaited()


class TestPetitionUploadRejectsInvalidFiles:
    """Petition uploads with non-PDF content must fail loudly, not 201."""

    def test_garbage_body_named_pdf_rejected_with_400(
        self, client: TestClient, test_campaign: Campaign
    ):
        """A .pdf-named file with garbage bytes must 400 with detail, never 201."""
        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={
                "file": (
                    (
                        "fake.pdf",
                        io.BytesIO(b"not a pdf at all"),
                        "application/pdf",
                    )
                )
            },
        )

        assert response.status_code == 400
        assert response.status_code != 201
        assert "invalid" in response.json()["detail"].lower()

    def test_wrong_content_type_rejected_with_400(
        self, client: TestClient, test_campaign: Campaign
    ):
        """text/plain content type must 400 even with a .pdf filename."""
        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": ("fake.pdf", io.BytesIO(b"%PDF-1.4 fake"), "text/plain")},
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_missing_pdf_magic_rejected_with_400(
        self, client: TestClient, test_campaign: Campaign
    ):
        """application/pdf content type without %PDF- magic must 400."""
        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": ("fake.pdf", io.BytesIO(b"junk data"), "application/pdf")},
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_nonexistent_campaign_rejected_with_404(self, client: TestClient):
        """A well-formed but unknown campaign ID must 404, not touch the FS."""
        from uuid import uuid4

        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(uuid4())},
            files={
                "file": ("fake.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")
            },
        )

        assert response.status_code == 404

    def test_filename_with_path_separator_rejected_with_400(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Client filenames containing path separators must 400."""
        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={
                "file": ("../evil.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")
            },
        )

        assert response.status_code == 400

    def test_same_filename_reuploads_produce_distinct_scans(
        self,
        client: TestClient,
        test_campaign: Campaign,
        tmp_upload_dir: Path,
    ):
        """Re-uploading the same filename must not overwrite on disk."""
        from unittest.mock import MagicMock, patch

        pdf_content = b"%PDF-1.4\n%fake pdf\n%%EOF"

        def _fake_image():
            image = MagicMock()
            image.size = (1000, 1500)
            return image

        with patch("app.files.file_service.convert_from_path") as mock_convert:
            mock_convert.return_value = [_fake_image()]
            responses = [
                client.post(
                    "/api/upload/petition",
                    data={"campaign_id": str(test_campaign.id)},
                    files={
                        "file": (
                            "same_name.pdf",
                            io.BytesIO(pdf_content),
                            "application/pdf",
                        )
                    },
                )
                for _ in range(2)
            ]

        assert all(r.status_code == 201 for r in responses)
        scan_ids = {r.json()["scanId"] for r in responses}
        assert len(scan_ids) == 2

        petition = tmp_upload_dir / "campaigns" / test_campaign.id.hex / "petitions"
        stored_names = [
            name for name in petition.iterdir() if name.name == "same_name.pdf"
        ]
        assert stored_names == [], "original filename must never become a path"


class TestVoterListUploadRejectsInvalidFiles:
    """Voter list uploads get the same path-hardening as petitions."""

    def test_filename_with_path_separator_rejected_with_400(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Client filenames containing path separators must 400."""
        response = client.post(
            "/api/upload/voter-list",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": ("../evil.csv", io.BytesIO(b"junk"), "text/csv")},
        )

        assert response.status_code == 400
        assert "filename" in response.json()["detail"].lower()

    def test_same_filename_reuploads_stored_path_distinct(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Re-uploading the same filename must not overwrite on disk."""
        csv_content = (
            "First_Name,Last_Name,Street,City,State,Zip\n"
            "John,Doe,123 Main St,Washington,DC,20001\n"
        )

        def _upload() -> str:
            response = client.post(
                "/api/upload/voter-list",
                data={"campaign_id": str(test_campaign.id)},
                files={
                    "file": (
                        "voters.csv",
                        io.BytesIO(csv_content.encode()),
                        "text/csv",
                    )
                },
            )
            assert response.status_code == 201
            return response.json()["filePath"]

        file_paths = {_upload(), _upload()}
        assert len(file_paths) == 2, "same-name re-upload must not overwrite"

        for file_path in file_paths:
            stored_name = Path(file_path).name
            assert stored_name != "voters.csv", (
                "original filename must never become a path"
            )
            assert stored_name.lower().endswith(".csv")

    def test_malformed_campaign_id_rejected_with_400(self, client: TestClient):
        """Malformed campaign UUID is a 400, not the pre-fix 404 path."""
        response = client.post(
            "/api/upload/voter-list",
            data={"campaign_id": "not-a-campaign-id"},
            files={"file": ("voters.csv", io.BytesIO(b"junk"), "text/csv")},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid campaign ID"


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
