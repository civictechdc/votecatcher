"""Unit tests for SessionService.

BDD-style tests describing expected behaviour of the session management service
before the implementation exists. Written using vertical-slice TDD: one test →
implement → verify → next.
"""

import io
import json
import zipfile

import pytest
from sqlmodel import Session

from app.data.database.model.session import Session as SessionModel
from app.data.database.model.session import SessionType


def _seed_session(
    session: Session,
    name: str = "Test Session",
    session_type: SessionType = SessionType.REAL,
    campaign_id=None,
    snapshot_data: dict | None = None,
) -> SessionModel:
    s = SessionModel(
        name=name,
        session_type=session_type,
        campaign_id=campaign_id,
        snapshot_data=snapshot_data or {},
    )
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


class TestCreateSession:
    """Feature: Session creation.

    As an API consumer
    I want to create a session with a name, type, and snapshot data
    So that I can save my workspace state for later restoration.
    """

    def test_creates_session_with_defaults(self, session: Session):
        """Scenario: Create a REAL session with only a name."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        result = service.create_session(name="My Session")

        assert result.name == "My Session"
        assert result.session_type == "REAL"
        assert result.campaign_id is None
        assert result.snapshot_data == {}
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_creates_demo_session_with_snapshot(self, session: Session):
        """Scenario: Create a DEMO session with snapshot data."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        snapshot = {"job_ids": [1, 2], "crop_ids": [3, 4]}
        result = service.create_session(
            name="Demo",
            session_type="DEMO",
            snapshot_data=snapshot,
        )

        assert result.session_type == "DEMO"
        assert result.snapshot_data == snapshot

    def test_rejects_invalid_campaign_id_format(self, session: Session):
        """Scenario: Campaign ID is not a valid UUID string."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        with pytest.raises(ValueError, match="Invalid campaign_id format"):
            service.create_session(name="Bad", campaign_id="not-a-uuid")


class TestListSessions:
    """Feature: Session listing.

    As an API consumer
    I want to list sessions optionally filtered by type
    So that I can browse saved workspace states.
    """

    def test_empty_database_returns_empty(self, session: Session):
        """Scenario: No sessions exist."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        result = service.list_sessions()

        assert result.sessions == []
        assert result.total == 0

    def test_returns_all_sessions_ordered_by_updated_at_desc(self, session: Session):
        """Scenario: Multiple sessions exist, most recently updated first."""
        from app.services.session_service import SessionService

        _seed_session(session, name="Old")
        _seed_session(session, name="New")

        service = SessionService(session)
        result = service.list_sessions()

        assert result.total == 2
        assert len(result.sessions) == 2
        assert result.sessions[0].name == "New"
        assert result.sessions[1].name == "Old"

    def test_filters_by_session_type(self, session: Session):
        """Scenario: Filter to only DEMO sessions."""
        from app.services.session_service import SessionService

        _seed_session(session, name="Real", session_type=SessionType.REAL)
        _seed_session(session, name="Demo", session_type=SessionType.DEMO)

        service = SessionService(session)
        result = service.list_sessions(session_type="DEMO")

        assert result.total == 1
        assert result.sessions[0].session_type == "DEMO"


class TestGetSession:
    """Feature: Session retrieval.

    As an API consumer
    I want to retrieve a single session by ID
    So that I can load a previously saved workspace state.
    """

    def test_returns_session_details(self, session: Session):
        """Scenario: Session exists."""
        from app.services.session_service import SessionService

        seeded = _seed_session(session, name="Detail", snapshot_data={"key": "value"})

        service = SessionService(session)
        result = service.get_session(seeded.id)

        assert result.id == seeded.id
        assert result.name == "Detail"
        assert result.snapshot_data == {"key": "value"}

    def test_nonexistent_session_raises_value_error(self, session: Session):
        """Scenario: Session ID does not exist."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        with pytest.raises(ValueError, match="not found"):
            service.get_session(99999)


class TestDeleteSession:
    """Feature: Session deletion.

    As an API consumer
    I want to delete a session
    So that I can remove workspace states I no longer need.
    """

    def test_deletes_existing_session(self, session: Session):
        """Scenario: Session exists and is deleted."""
        from app.services.session_service import SessionService

        seeded = _seed_session(session, name="Delete Me")

        service = SessionService(session)
        service.delete_session(seeded.id)

        assert session.get(SessionModel, seeded.id) is None

    def test_nonexistent_session_raises_value_error(self, session: Session):
        """Scenario: Session ID does not exist."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        with pytest.raises(ValueError, match="not found"):
            service.delete_session(99999)


class TestExportSession:
    """Feature: Session export.

    As an API consumer
    I want to export a session as a ZIP archive containing session metadata
    So that I can archive or transfer workspace states.
    """

    def test_exports_valid_zip_with_metadata(self, session: Session):
        """Scenario: Export session returns valid ZIP with session.json."""
        from app.services.session_service import SessionService

        snapshot = {"jobs": [1, 2, 3]}
        seeded = _seed_session(session, name="Export Test", snapshot_data=snapshot)

        service = SessionService(session)
        zip_bytes, filename = service.export_session(seeded.id)

        assert "Export Test" in filename
        assert str(seeded.id) in filename
        assert filename.endswith(".zip")

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert "session.json" in zf.namelist()
            metadata = json.loads(zf.read("session.json"))
            assert metadata["name"] == "Export Test"
            assert metadata["snapshot_data"] == snapshot
            assert metadata["session_type"] == "REAL"
            assert "created_at" in metadata
            assert "updated_at" in metadata

    def test_sanitizes_name_in_filename(self, session: Session):
        """Scenario: Session name with special characters is sanitized."""
        from app.services.session_service import SessionService

        seeded = _seed_session(session, name="Test/Session<>Here")

        service = SessionService(session)
        _, filename = service.export_session(seeded.id)

        assert "/" not in filename
        assert "<" not in filename
        assert ">" not in filename

    def test_nonexistent_session_raises_value_error(self, session: Session):
        """Scenario: Session ID does not exist."""
        from app.services.session_service import SessionService

        service = SessionService(session)
        with pytest.raises(ValueError, match="not found"):
            service.export_session(99999)
