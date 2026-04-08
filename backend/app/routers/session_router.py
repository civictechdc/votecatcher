"""Session management router for save/load/export functionality."""

import io
import json
import uuid
import zipfile
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.data.database.model.session import Session as SessionModel
from app.data.database.model.session import SessionType
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

SessionDep = Annotated[Session, Depends(get_session)]


class CreateSessionRequest(BaseModel):
    """Request schema for saving a session."""

    name: str
    campaign_id: str | None = None
    snapshot_data: dict = {}
    session_type: str = "REAL"


class SessionResponse(BaseModel):
    """Response schema for session."""

    id: int
    name: str
    campaign_id: str | None
    session_type: str
    snapshot_data: dict
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """Response schema for listing sessions."""

    sessions: list[SessionResponse]
    total: int


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(  # nosemgrep: fastapi-unauthenticated-route
    request: CreateSessionRequest,
    session: SessionDep,
) -> SessionResponse:
    """Save current workspace state as a session."""
    session_type = (
        SessionType.DEMO if request.session_type == "DEMO" else SessionType.REAL
    )

    campaign_id_uuid = None
    if request.campaign_id:
        try:
            campaign_id_uuid = uuid.UUID(request.campaign_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign_id format: {request.campaign_id}",
            ) from None

    new_session = SessionModel(
        name=request.name,
        campaign_id=campaign_id_uuid,
        session_type=session_type,
        snapshot_data=request.snapshot_data,
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    logger.info(
        "Created session",
        session_id=new_session.id,
        name=new_session.name,
        session_type=new_session.session_type.value,
    )

    return SessionResponse(
        id=new_session.id,
        name=new_session.name,
        campaign_id=str(new_session.campaign_id) if new_session.campaign_id else None,
        session_type=new_session.session_type.value,
        snapshot_data=new_session.snapshot_data,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
    )


@router.get("", response_model=SessionListResponse)
def list_sessions(  # nosemgrep: fastapi-unauthenticated-route
    session: SessionDep,
    session_type: str | None = None,
) -> SessionListResponse:
    """List all saved sessions."""
    query = select(SessionModel)

    if session_type:
        st = SessionType.DEMO if session_type == "DEMO" else SessionType.REAL
        query = query.where(SessionModel.session_type == st)

    query = query.order_by(SessionModel.updated_at.desc())
    sessions = session.exec(query).all()

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                name=s.name,
                campaign_id=str(s.campaign_id) if s.campaign_id else None,
                session_type=s.session_type.value,
                snapshot_data=s.snapshot_data,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_detail(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> SessionResponse:
    """Load a saved session."""
    saved_session = session.get(SessionModel, session_id)
    if not saved_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return SessionResponse(
        id=saved_session.id,
        name=saved_session.name,
        campaign_id=str(saved_session.campaign_id)
        if saved_session.campaign_id
        else None,
        session_type=saved_session.session_type.value,
        snapshot_data=saved_session.snapshot_data,
        created_at=saved_session.created_at,
        updated_at=saved_session.updated_at,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> None:
    """Delete a session."""
    saved_session = session.get(SessionModel, session_id)
    if not saved_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    session.delete(saved_session)
    session.commit()
    logger.info("Deleted session", session_id=session_id)


@router.get("/{session_id}/export")
def export_session(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> StreamingResponse:
    """Export session as ZIP file."""
    saved_session = session.get(SessionModel, session_id)
    if not saved_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        metadata = {
            "id": saved_session.id,
            "name": saved_session.name,
            "campaign_id": str(saved_session.campaign_id)
            if saved_session.campaign_id
            else None,
            "session_type": saved_session.session_type.value,
            "snapshot_data": saved_session.snapshot_data,
            "created_at": saved_session.created_at.isoformat(),
            "updated_at": saved_session.updated_at.isoformat(),
        }
        zip_file.writestr("session.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)

    safe_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in saved_session.name
    )
    filename = f"{safe_name}_session_{session_id}.zip"

    logger.info("Exporting session", session_id=session_id, filename=filename)

    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
