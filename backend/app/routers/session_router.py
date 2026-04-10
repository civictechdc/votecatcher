"""Session management router for save/load/export functionality."""

import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

SessionDep = Annotated[Session, Depends(get_session)]


class CreateSessionRequest(ApiModel):
    """Request schema for saving a session."""

    name: str
    campaign_id: str | None = None
    snapshot_data: dict = {}
    session_type: str = "REAL"


class SessionResponse(ApiModel):
    """Response schema for session."""

    id: int
    name: str
    campaign_id: str | None
    session_type: str
    snapshot_data: dict
    created_at: datetime
    updated_at: datetime


class SessionListResponse(ApiModel):
    """Response schema for listing sessions."""

    sessions: list[SessionResponse]
    total: int


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(  # nosemgrep: fastapi-unauthenticated-route
    request: CreateSessionRequest,
    session: SessionDep,
) -> SessionResponse:
    """Save current workspace state as a session."""
    service = SessionService(session)
    try:
        result = service.create_session(
            name=request.name,
            session_type=request.session_type,
            campaign_id=request.campaign_id,
            snapshot_data=request.snapshot_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    return SessionResponse(
        id=result.id,
        name=result.name,
        campaign_id=result.campaign_id,
        session_type=result.session_type,
        snapshot_data=result.snapshot_data,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("", response_model=SessionListResponse)
def list_sessions(  # nosemgrep: fastapi-unauthenticated-route
    session: SessionDep,
    session_type: str | None = None,
) -> SessionListResponse:
    """List all saved sessions."""
    service = SessionService(session)
    result = service.list_sessions(session_type=session_type)

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                name=s.name,
                campaign_id=s.campaign_id,
                session_type=s.session_type,
                snapshot_data=s.snapshot_data,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in result.sessions
        ],
        total=result.total,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_detail(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> SessionResponse:
    """Load a saved session."""
    service = SessionService(session)
    try:
        result = service.get_session(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    return SessionResponse(
        id=result.id,
        name=result.name,
        campaign_id=result.campaign_id,
        session_type=result.session_type,
        snapshot_data=result.snapshot_data,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> None:
    """Delete a session."""
    service = SessionService(session)
    try:
        service.delete_session(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None


@router.get("/{session_id}/export")
def export_session(  # nosemgrep: fastapi-unauthenticated-route
    session_id: int,
    session: SessionDep,
) -> StreamingResponse:
    """Export session as ZIP file."""
    service = SessionService(session)
    try:
        zip_bytes, filename = service.export_session(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
