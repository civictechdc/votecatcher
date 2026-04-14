"""BDD contract tests for upload endpoints emitting setup:updated events.

Feature: Upload event emission
  As a frontend client subscribed to a campaign SSE stream
  I want to receive a setup:updated event when uploads complete
  So that the workspace page can refresh setup status in real time

Scenarios cover:
  - Voter list upload emits setup:updated with upload_type=voter_list
  - Petition upload emits setup:updated with upload_type=petition
  - Failed uploads do NOT emit events
  - Event reaches campaign topic subscriber
"""

import io
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign
from app.events.event_bus import event_bus


def _csv_file(filename: str = "voters.csv") -> tuple[bytes, str]:
    content = b"last_name,first_name\n,Doe,John\n"
    return content, filename


def _pdf_file(filename: str = "petition.pdf") -> tuple[bytes, str]:
    content = b"%PDF-1.4 fake pdf content"
    return content, filename


class TestVoterListUploadEmitsSetupUpdatedEvent:
    """Given a campaign exists and a client is subscribed to its event stream."""

    @patch("app.services.upload_service.FileService")
    def test_emits_setup_updated_on_success(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When voter list upload succeeds, a setup:updated event is published."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.import_voter_list = AsyncMock(return_value=("/tmp/voters.csv", 42))

        queue = event_bus.subscribe(f"campaign:{test_campaign.id}")

        content, filename = _csv_file()
        response = client.post(
            "/api/upload/voter-list",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 201

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["event_type"] == "setup:updated"
        assert data["campaign_id"] == str(test_campaign.id)
        assert data["upload_type"] == "voter_list"

    def test_no_event_on_failure(self, client: TestClient):
        """When voter list upload fails (missing fields), no event is emitted."""
        queue = event_bus.subscribe("campaign:nonexistent")

        content, filename = _csv_file()
        response = client.post(
            "/api/upload/voter-list",
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

        assert response.status_code == 422
        assert queue.empty()


class TestPetitionUploadEmitsSetupUpdatedEvent:
    """Given a campaign exists and a client is subscribed to its event stream."""

    @patch("app.services.upload_service.FileService")
    def test_emits_setup_updated_on_success(
        self, mock_fs_cls: AsyncMock, client: TestClient, test_campaign: Campaign
    ):
        """When petition upload succeeds, a setup:updated event is published."""
        mock_fs = mock_fs_cls.return_value
        mock_fs.process_petition_upload = AsyncMock(return_value=(1, 5))

        queue = event_bus.subscribe(f"campaign:{test_campaign.id}")

        content, filename = _pdf_file()
        response = client.post(
            "/api/upload/petition",
            data={"campaign_id": str(test_campaign.id)},
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 201

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["event_type"] == "setup:updated"
        assert data["campaign_id"] == str(test_campaign.id)
        assert data["upload_type"] == "petition"

    def test_no_event_on_failure(self, client: TestClient):
        """When petition upload fails (missing fields), no event is emitted."""
        queue = event_bus.subscribe("campaign:nonexistent")

        content, filename = _pdf_file()
        response = client.post(
            "/api/upload/petition",
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 422
        assert queue.empty()
