"""Unit tests for DemoOrchestrationService.

BDD-style tests describing expected behaviour of the demo orchestration
service before the implementation exists. Written using vertical-slice TDD:
one test → implement → verify → next.
"""

import pytest

from app.settings.settings import Settings


_K = "test-" + "secret-" + "key-for-testing-only"


def _make_settings(**overrides) -> Settings:
    defaults = {
        "database_url": "sqlite:///:memory:",
        "secret_key": _K,
        "feature_demo": False,
        "demo_reset": False,
    }
    defaults.update(overrides)
    return Settings.model_construct(**defaults)


class TestRequireDemoMode:
    """Feature: Demo mode gate.

    As an API consumer
    I want demo endpoints to be gated behind a feature flag
    So that demo functionality is only available when explicitly enabled.
    """

    def test_raises_when_demo_mode_disabled(self):
        """Scenario: Demo mode is off, accessing demo endpoint raises PermissionError."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=False)
        service = DemoOrchestrationService(settings=settings)

        with pytest.raises(PermissionError, match="Demo mode not enabled"):
            service.require_demo_mode()

    def test_passes_silently_when_demo_mode_enabled(self):
        """Scenario: Demo mode is on, accessing demo endpoint succeeds."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings)

        service.require_demo_mode()


class TestRequireDemoReset:
    """Feature: Demo reset gate.

    As an API consumer
    I want demo reset to be gated behind a separate flag
    So that reset is only available when both demo mode and reset are enabled.
    """

    def test_raises_when_demo_mode_disabled(self):
        """Scenario: Demo mode off, reset raises PermissionError."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=False, demo_reset=True)
        service = DemoOrchestrationService(settings=settings)

        with pytest.raises(PermissionError, match="Demo mode not enabled"):
            service.require_demo_reset()

    def test_raises_when_demo_reset_disabled(self):
        """Scenario: Demo mode on but reset off, reset raises PermissionError."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True, demo_reset=False)
        service = DemoOrchestrationService(settings=settings)

        with pytest.raises(PermissionError, match="Demo reset not enabled"):
            service.require_demo_reset()

    def test_passes_silently_when_both_enabled(self):
        """Scenario: Both flags on, reset succeeds."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True, demo_reset=True)
        service = DemoOrchestrationService(settings=settings)

        service.require_demo_reset()


class TestListPrebakedSessions:
    """Feature: Prebaked session listing.

    As an API consumer
    I want to list available pre-baked demo sessions
    So that I can choose one to load.
    """

    def test_returns_list_of_prebaked_sessions(self):
        """Scenario: At least one prebaked session is defined."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings)

        sessions = service.list_prebaked_sessions()

        assert len(sessions) >= 1
        assert all(s.id for s in sessions)
        assert all(s.name for s in sessions)
        assert all(s.description for s in sessions)

    def test_includes_dc_petition_2024_session(self):
        """Scenario: The default DC petition demo session is present."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings)

        sessions = service.list_prebaked_sessions()
        ids = [s.id for s in sessions]

        assert "dc-petition-2024" in ids


class TestGetPrebakedSession:
    """Feature: Prebaked session lookup.

    As an API consumer
    I want to look up a specific pre-baked session by ID
    So that I can load it for demo purposes.
    """

    def test_returns_session_when_found(self):
        """Scenario: Valid session ID returns the session metadata."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings)

        session = service.get_prebaked_session("dc-petition-2024")

        assert session is not None
        assert session.id == "dc-petition-2024"
        assert session.name == "DC Petition Demo 2024"

    def test_returns_none_when_not_found(self):
        """Scenario: Invalid session ID returns None."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings)

        session = service.get_prebaked_session("nonexistent-session")

        assert session is None


class TestLoadPrebakedSession:
    """Feature: Prebaked session loading.

    As an API consumer
    I want to load a pre-baked demo session
    So that I can see a complete demo workflow.
    """

    def test_loads_session_with_valid_id(self, session):
        """Scenario: Valid session ID loads demo data and returns result."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings, db_session=session)

        result = service.load_prebaked_session("dc-petition-2024")

        assert result["success"] is True
        assert "campaign_id" in result
        assert result["voters_count"] == 10

    def test_raises_value_error_for_invalid_id(self, session):
        """Scenario: Invalid session ID raises ValueError."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings, db_session=session)

        with pytest.raises(ValueError, match="not found"):
            service.load_prebaked_session("nonexistent-session")

    def test_returns_session_metadata_in_result(self, session):
        """Scenario: Load result includes session metadata."""
        from app.services.demo_orchestration_service import DemoOrchestrationService

        settings = _make_settings(feature_demo=True)
        service = DemoOrchestrationService(settings=settings, db_session=session)

        result = service.load_prebaked_session("dc-petition-2024")

        assert result["session_id"] == "dc-petition-2024"
        assert result["message"] == "Loaded demo session: DC Petition Demo 2024"
