from pathlib import Path

import structlog
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.campaign.campaign_repository import CampaignRepository
from app.data.database.local.demo_campaign_repo import DemoCampaignRepository
from app.data.database.local.demo_local_db import (
	LocalRegisteredVoterRepository,
	get_db_session,
)
from app.data.database.local.demo_local_job_monitor import DemoMatchingTaskMonitor
from app.data.database.local.demo_match_repo import DemoEntryMatchRepository
from app.data.database.local.demo_match_task_repo import DemoMatchTaskRepository
from app.data.database.local.demo_ocr_repo import (
	DemoOcrJobRepository,
	DemoOcrProviderRepo,
)
from app.data.database.local.demo_ocr_results import DemoOcrResultsRepo
from app.data.database.local.demo_petition_repo import DemoScannedPetitionRepository
from app.data.database.model.ocr_model import OcrProviderRepository
from app.events.matching_task_events import MatchingTaskMonitor
from app.files.file_repository import (
	RegisteredVoterRepository,
	ScannedPetitionRepository,
)
from app.matching.match_repository import EntryMatchRepository, MatchTaskRepository
from app.ocr.data.ocr_repository import OcrJobRepository
from app.ocr.ocr_manager import OcrHandler
from app.ocr.ocr_result_repo import OcrResultRepository
from app.settings.env_settings import AppSettings, get_settings

load_dotenv()

logger = structlog.get_logger(__name__)

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
	tokenUrl="/api/token", scheme_name="JWT", refreshUrl=""
)


demo_petition_path: Path = Path("temp")


def get_file_repository(
	session: Session = Depends(get_db_session),
) -> RegisteredVoterRepository:
	return LocalRegisteredVoterRepository(session)


def get_scanned_documents_repository(
	session: Session = Depends(get_db_session),
) -> ScannedPetitionRepository:
	return DemoScannedPetitionRepository(session)


def get_ocr_job_repository(
	session: Session = Depends(get_db_session),
) -> OcrJobRepository:
	return DemoOcrJobRepository(session)


def get_matching_results_repository(
	session: Session = Depends(get_db_session),
) -> EntryMatchRepository:
	return DemoEntryMatchRepository(session)


def get_campaign_repository(
	session: Session = Depends(get_db_session),
) -> CampaignRepository:
	return DemoCampaignRepository(session)


def get_matching_task_repository(
	session: Session = Depends(get_db_session),
) -> MatchTaskRepository:
	return DemoMatchTaskRepository(session)


def get_ocr_provider_repository(
	session: Session = Depends(get_db_session),
) -> OcrProviderRepository:
	return DemoOcrProviderRepo(session)


def get_ocr_results_repository(
	session: Session = Depends(get_db_session),
) -> OcrResultRepository:
	return DemoOcrResultsRepo(session)


def get_matching_task_monitor(
	match_task_repo: MatchTaskRepository = Depends(get_matching_task_repository),
	ocr_provider: OcrProviderRepository = Depends(get_ocr_provider_repository),
) -> MatchingTaskMonitor:
	return DemoMatchingTaskMonitor(
		matching_task_repository=match_task_repo,
		ocr_provider_repository=ocr_provider,
	)


def get_ocr_handler(
	matching_task_monitor: MatchingTaskMonitor = Depends(get_matching_task_monitor),
	ocr_provider_repo: OcrProviderRepository = Depends(get_ocr_provider_repository),
	matching_task_repo: MatchTaskRepository = Depends(get_matching_task_repository),
	ocr_result_repo: OcrResultRepository = Depends(get_ocr_results_repository),
	ocr_job_repo: OcrJobRepository = Depends(get_ocr_job_repository),
	settings: AppSettings = Depends(get_settings),
) -> OcrHandler:
	from app.ocr.clients.batch_ocr_manager import BatchOcrHandler

	return BatchOcrHandler(
		settings=settings,
		ocr_job_repo=ocr_job_repo,
		ocr_provider_repo=ocr_provider_repo,
		matching_task_repo=matching_task_repo,
		matching_task_monitor=matching_task_monitor,
		ocr_result_repo=ocr_result_repo,
	)
