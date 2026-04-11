"""Demo mode endpoints for reset and pre-baked session loading."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
from app.services.demo_orchestration_service import DemoOrchestrationService
from app.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class PrebakedSession(ApiModel):
    """Pre-baked demo session metadata."""

    id: str
    name: str
    description: str


class PrebakedSessionList(ApiModel):
    """List of pre-baked sessions."""

    sessions: list[PrebakedSession]


@router.get(  # nosemgrep: fastapi-unauthenticated-route
    "/sessions", response_model=PrebakedSessionList
)
def list_prebaked_sessions(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PrebakedSessionList:
    """List available pre-baked demo sessions."""
    service = DemoOrchestrationService(settings=settings)
    try:
        service.require_demo_mode()
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    sessions = service.list_prebaked_sessions()
    return PrebakedSessionList(
        sessions=[
            PrebakedSession(id=s.id, name=s.name, description=s.description)
            for s in sessions
        ]
    )


@router.post(  # nosemgrep: fastapi-unauthenticated-route
    "/reset", status_code=status.HTTP_204_NO_CONTENT
)
def reset_demo_data(
    db_session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Reset all demo data to initial state."""
    service = DemoOrchestrationService(settings=settings, db_session=db_session)
    try:
        service.require_demo_reset()
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    from app.demo.demo_service import DemoDataService

    demo_service = DemoDataService(db_session)
    demo_service.reset()
    logger.info("Demo data reset complete")


@router.post(  # nosemgrep: fastapi-unauthenticated-route
    "/sessions/{session_id}/load", status_code=status.HTTP_200_OK
)
def load_prebaked_session(
    session_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Load a pre-baked demo session."""
    service = DemoOrchestrationService(settings=settings, db_session=db_session)
    try:
        service.require_demo_mode()
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    try:
        return service.load_prebaked_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
