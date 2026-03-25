# Database models for Votecatcher
# This file exports all SQLModel models for Alembic migration detection

# Existing Models
from app.data.database.model.jobs import (
	JobStatus,
	MatcherJob,
	OcrJob,
	OcrModel,
	OcrProvider,
)
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop

# New Models for Phase 1
from app.data.database.model.petition_scan import PetitionScan

# Voter List Tracking (Phase 13)
from app.data.database.model.region_schema import RegionSchema
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.session import Session, SessionType

# User model (minimal for MVP)
from app.data.database.model.user import User
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload

__all__ = [
	# Existing
	"Region",
	"Campaign",
	# User
	"User",
	# New - Petition processing
	"PetitionScan",
	"PetitionCrop",
	"OcrResult",
	"MatchResult",
	"ConfidenceLevel",
	# New - Job orchestration
	"MatcherJob",
	"OcrJob",
	"OcrProvider",
	"OcrModel",
	"JobStatus",
	# New - Session & Data
	"Session",
	"SessionType",
	"RegisteredVoter",
	# Phase 13 - Voter List Tracking
	"VoterListUpload",
	"UploadStatus",
	"RegionSchema",
]
