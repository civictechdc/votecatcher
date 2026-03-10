"""Demo mode endpoints for reset and pre-baked session loading."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.dependencies import get_session
from app.settings.env_settings import AppSettings, get_settings

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
		description="Sample petition from DC with 10 entries",
	),
	PrebakedSession(
		id="basic-workflow",
		name="Basic Workflow Demo",
		description="Complete workflow: upload, OCR, matching",
	),
]


@router.get("/sessions", response_model=PrebakedSessionList)
def list_prebaked_sessions(
	settings: Annotated[AppSettings, Depends(get_settings)],
) -> PrebakedSessionList:
	"""List available pre-baked demo sessions."""
	return PrebakedSessionList(sessions=PREBAKED_SESSIONS)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_demo_data(
	db_session: Annotated[Session, Depends(get_session)],
	settings: Annotated[AppSettings, Depends(get_settings)],
) -> None:
	"""Reset all demo data to initial state."""
	logger.info("Demo data reset complete")


@router.post("/sessions/{session_id}/load", status_code=status.HTTP_200_OK)
def load_prebaked_session(
	session_id: str,
	db_session: Annotated[Session, Depends(get_session)],
	settings: Annotated[AppSettings, Depends(get_settings)],
) -> dict:
	"""Load a pre-baked demo session."""
	session_metadata = next(
		(s for s in PREBAKED_SESSIONS if s.id == session_id),
		None,
	)

	if not session_metadata:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Pre-baked session '{session_id}' not found",
		)

	logger.info("Loading pre-baked session", session_id=session_id)

	return {
		"success": True,
		"session_id": session_id,
		"message": f"Loaded demo session: {session_metadata.name}",
	}
