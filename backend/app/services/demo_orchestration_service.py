"""Demo orchestration service for mode gating and pre-baked session management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from app.settings import Settings

if TYPE_CHECKING:
    from sqlmodel import Session

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PrebakedSessionMeta:
    id: str
    name: str
    description: str


PREBAKED_SESSIONS = [
    PrebakedSessionMeta(
        id="dc-petition-2024",
        name="DC Petition Demo 2024",
        description="Minimal demo session with 10 entries",
    ),
]


class DemoOrchestrationService:
    """Service for demo mode orchestration: gating, session listing, loading."""

    def __init__(
        self,
        settings: Settings,
        db_session: Session | None = None,
    ):
        self._settings = settings
        self._db_session = db_session

    def require_demo_mode(self) -> None:
        if not self._settings.feature_demo:
            raise PermissionError("Demo mode not enabled")

    def require_demo_reset(self) -> None:
        self.require_demo_mode()
        if not self._settings.demo_reset:
            raise PermissionError("Demo reset not enabled")

    def list_prebaked_sessions(self) -> list[PrebakedSessionMeta]:
        return list(PREBAKED_SESSIONS)

    def get_prebaked_session(self, session_id: str) -> PrebakedSessionMeta | None:
        return next(
            (s for s in PREBAKED_SESSIONS if s.id == session_id),
            None,
        )

    def load_prebaked_session(self, session_id: str) -> dict:
        session_metadata = self.get_prebaked_session(session_id)

        if not session_metadata:
            raise ValueError(f"Pre-baked session '{session_id}' not found")

        from app.demo.demo_service import DemoDataService

        demo_service = DemoDataService(self._db_session)
        result = demo_service.load_minimal_session()

        logger.info(
            "Loaded pre-baked session",
            session_id=session_id,
            campaign_id=result.get("campaign_id"),
        )

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Loaded demo session: {session_metadata.name}",
            **result,
        }
