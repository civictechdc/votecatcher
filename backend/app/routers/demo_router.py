"""Demo mode endpoints for reset and pre-baked session loading."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, delete

from app.data.database.model.jobs import MatcherJob, OcrJob
from app.data.database.model.match_result import MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.session import Session as SessionModel
from app.data.database.model.session import SessionType
from app.dependencies import get_session
from app.settings.env_settings import Settings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


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
		description="Sample petition from DC with 10 entries and and matching results",
	),
	PrebakedSession(
		id="basic-workflow",
		name="Basic Workflow Demo",
		description="Complete workflow: upload, OCR, matching",
	),
]


@router.get("/sessions", response_model=PrebakedSessionList)
def list_prebaked_sessions(
	settings: SettingsDep,
) -> PrebakedSessionList:
	"""List available pre-baked demo sessions."""
	if not settings.demo_mode:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo mode is not enabled",
		)

	return PrebakedSessionList(sessions=PREBAKED_SESSIONS)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_demo_data(
	session: SessionDep,
	settings: SettingsDep,
) -> None:
	"""Reset all demo data to initial state."""
	if not settings.demo_mode:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo mode is not enabled",
		)

	if not settings.demo_reset:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo reset is not enabled",
		)

	logger.info("Starting demo data reset")

	session.exec(delete(MatchResult))
	session.exec(delete(OcrResult))
	session.exec(delete(PetitionCrop))
	session.exec(delete(OcrJob))
	session.exec(delete(MatcherJob))
	session.exec(delete(PetitionScan))
	session.exec(delete(Campaign))
	session.exec(delete(Region))
	session.exec(delete(SessionModel))
	session.commit()

	logger.info("Demo data reset complete")


@router.post("/sessions/{session_id}/load", status_code=status.HTTP_200_OK)
def load_prebaked_session(
	session_id: str,
	db_session: SessionDep,
	settings: SettingsDep,
) -> dict:
	"""Load a pre-baked demo session."""
	if not settings.demo_mode:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Demo mode is not enabled",
		)

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

	region = Region(
		region_key="DC_DEMO",
		region_name="District of Columbia (Demo)",
		country_code="US",
	)
	db_session.add(region)
	db_session.commit()
	db_session.refresh(region)

	campaign = Campaign(
		unique_name="demo_campaign_2024",
		title="DC Petition Demo 2024",
		year="2024",
		region_id=region.id,
	)
	db_session.add(campaign)
	db_session.commit()
	db_session.refresh(campaign)

	petition_scan = PetitionScan(
		campaign_id=campaign.id,
		file_name="demo_petition.pdf",
		file_path="demo/demo_petition.pdf",
		status="UPLOADED",
	)
	db_session.add(petition_scan)
	db_session.commit()
	db_session.refresh(petition_scan)

	crops = []
	for i in range(1, 6):
		crop = PetitionCrop(
			scan_id=petition_scan.id,
			crop_index=i,
			file_path=f"demo/crop_{i}.png",
			status="PENDING",
		)
		db_session.add(crop)
		crops.append(crop)
	db_session.commit()

	for crop in crops:
		db_session.refresh(crop)

	ocr_results = []
	for crop in crops:
		ocr_result = OcrResult(
			crop_id=crop.id,
			status="COMPLETED",
			extracted_text=(
				f"Demo Voter {crop.crop_index}\n123 Main St NW\nWashington, DC 20001"
			),
			confidence=0.95,
		)
		db_session.add(ocr_result)
		ocr_results.append(ocr_result)
	db_session.commit()

	for ocr in ocr_results:
		db_session.refresh(ocr)

	for ocr in ocr_results:
		match_result = MatchResult(
			ocr_result_id=ocr.id,
			voter_id=f"demo_voter_{ocr.crop_id}",
			match_score=0.92,
			confidence_level="HIGH",
			matched_name=f"Demo Voter {ocr.crop_id}",
			matched_address="123 Main St NW, Washington, DC 20001",
		)
		db_session.add(match_result)
	db_session.commit()

	demo_session = SessionModel(
		name=f"Demo: {session_metadata.name}",
		session_type=SessionType.DEMO,
		campaign_id=campaign.id,
		snapshot_data={
			"prebaked_id": session_id,
			"region_id": str(region.id),
			"campaign_id": str(campaign.id),
			"scan_id": str(petition_scan.id),
			"crop_count": len(crops),
			"ocr_count": len(ocr_results),
		},
	)
	db_session.add(demo_session)
	db_session.commit()
	db_session.refresh(demo_session)

	logger.info(
		"Pre-baked session loaded",
		session_id=session_id,
		campaign_id=campaign.id,
		crop_count=len(crops),
	)

	return {
		"success": True,
		"session_id": demo_session.id,
		"campaign_id": str(campaign.id),
		"message": f"Loaded demo session: {session_metadata.name}",
	}
