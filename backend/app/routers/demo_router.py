"""Demo mode endpoints for reset and pre-baked session loading."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.demo.demo_service import DemoDataService
from app.dependencies import get_session
from app.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class PrebakedSession(BaseModel):
	"""Pre-baked demo session metadata."""

	id: str
	name: str
	description: str


class PrebakedSessionList(BaseModel):
	"""List of pre-baked sessions."""

	sessions: list[PrebakedSession]


PREBAKED_SESSIONS = [
	PrebakedSession(
		id="dc-petition-2024",
		name="DC Petition Demo 2024",
		description="Minimal demo session with 10 entries",
	),
]


def check_demo_mode(settings: Settings) -> None:
	"""Check if demo mode is enabled."""
	if not settings.feature_demo:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo mode not enabled",
		)


def check_demo_reset(settings: Settings) -> None:
	"""Check if demo mode and reset are enabled."""
	check_demo_mode(settings)
	if not settings.demo_reset:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo reset not enabled",
		)


@router.get("/sessions", response_model=PrebakedSessionList)
def list_prebaked_sessions(
	settings: Annotated[Settings, Depends(get_settings)],
) -> PrebakedSessionList:
	"""List available pre-baked demo sessions."""
	check_demo_mode(settings)
	return PrebakedSessionList(sessions=PREBAKED_SESSIONS)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_demo_data(
	db_session: Annotated[Session, Depends(get_session)],
	settings: Annotated[Settings, Depends(get_settings)],
) -> None:
	"""Reset all demo data to initial state."""
	check_demo_reset(settings)

	service = DemoDataService(db_session)
	service.reset()
	logger.info("Demo data reset complete")


@router.post("/sessions/{session_id}/load", status_code=status.HTTP_200_OK)
def load_prebaked_session(
	session_id: str,
	db_session: Annotated[Session, Depends(get_session)],
	settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
	"""Load a pre-baked demo session."""
	check_demo_mode(settings)

	session_metadata = next(
		(s for s in PREBAKED_SESSIONS if s.id == session_id),
		None,
	)

	if not session_metadata:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Pre-baked session '{session_id}' not found",
		)

	service = DemoDataService(db_session)
	result = service.load_minimal_session()

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
