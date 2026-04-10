"""Session management service for CRUD operations and export."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from datetime import datetime
from dataclasses import dataclass

import structlog
from sqlmodel import Session, select

from app.data.database.model.session import Session as SessionModel
from app.data.database.model.session import SessionType

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SessionResponseData:
    id: int
    name: str
    campaign_id: str | None
    session_type: str
    snapshot_data: dict
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SessionListResponseData:
    sessions: list[SessionResponseData]
    total: int


class SessionService:
    """Service for managing workspace session snapshots."""

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _build_response(model: SessionModel) -> SessionResponseData:
        return SessionResponseData(
            id=model.id,
            name=model.name,
            campaign_id=str(model.campaign_id) if model.campaign_id else None,
            session_type=model.session_type.value,
            snapshot_data=model.snapshot_data,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def create_session(
        self,
        name: str,
        session_type: str = "REAL",
        campaign_id: str | None = None,
        snapshot_data: dict | None = None,
    ) -> SessionResponseData:
        st = SessionType.DEMO if session_type == "DEMO" else SessionType.REAL

        campaign_id_uuid = None
        if campaign_id:
            try:
                campaign_id_uuid = uuid.UUID(campaign_id)
            except ValueError:
                raise ValueError(f"Invalid campaign_id format: {campaign_id}") from None

        new_session = SessionModel(
            name=name,
            campaign_id=campaign_id_uuid,
            session_type=st,
            snapshot_data=snapshot_data or {},
        )
        self._session.add(new_session)
        self._session.commit()
        self._session.refresh(new_session)

        logger.info(
            "Created session",
            session_id=new_session.id,
            name=new_session.name,
            session_type=new_session.session_type.value,
        )

        return self._build_response(new_session)

    def list_sessions(self, session_type: str | None = None) -> SessionListResponseData:
        query = select(SessionModel)

        if session_type:
            st = SessionType.DEMO if session_type == "DEMO" else SessionType.REAL
            query = query.where(SessionModel.session_type == st)

        query = query.order_by(SessionModel.updated_at.desc())
        sessions = self._session.exec(query).all()

        return SessionListResponseData(
            sessions=[self._build_response(s) for s in sessions],
            total=len(sessions),
        )

    def get_session(self, session_id: int) -> SessionResponseData:
        saved = self._session.get(SessionModel, session_id)
        if not saved:
            raise ValueError(f"Session {session_id} not found")

        return self._build_response(saved)

    def delete_session(self, session_id: int) -> None:
        saved = self._session.get(SessionModel, session_id)
        if not saved:
            raise ValueError(f"Session {session_id} not found")

        self._session.delete(saved)
        self._session.commit()
        logger.info("Deleted session", session_id=session_id)

    def export_session(self, session_id: int) -> tuple[bytes, str]:
        saved = self._session.get(SessionModel, session_id)
        if not saved:
            raise ValueError(f"Session {session_id} not found")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            metadata = {
                "id": saved.id,
                "name": saved.name,
                "campaign_id": str(saved.campaign_id) if saved.campaign_id else None,
                "session_type": saved.session_type.value,
                "snapshot_data": saved.snapshot_data,
                "created_at": saved.created_at.isoformat(),
                "updated_at": saved.updated_at.isoformat(),
            }
            zip_file.writestr("session.json", json.dumps(metadata, indent=2))

        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in saved.name
        )
        filename = f"{safe_name}_session_{session_id}.zip"

        logger.info("Exporting session", session_id=session_id, filename=filename)

        return zip_buffer.getvalue(), filename
