"""Background worker for processing OCR and matching jobs.

Simple async worker that polls for NOT_STARTED jobs and processes them
through the OCR → Matching pipeline.

For MVP/demo purposes, this worker operates in simulation mode when
OCR_PROVIDER_API_KEY is not configured or SIMULATION_MODE is enabled.
"""

import asyncio
import random
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlmodel import Session, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign
from app.data.database.session import engine
from app.settings.env_settings import get_settings

if TYPE_CHECKING:
	from app.settings.env_settings import AppSettings

logger = structlog.get_logger(__name__)

POLL_INTERVAL_SECONDS = 2.0
OCR_SIMULATION_DELAY_SECONDS = 1.0
MATCHING_DELAY_SECONDS = 0.5


class JobWorker:
	"""Background worker for processing MatcherJobs.

	Polls for jobs in NOT_STARTED state and processes them through:
	1. OCR phase (simulated or real)
	2. Matching phase (fuzzy matching against voter DB)

	Attributes:
		settings: Application settings
		running: Flag to control worker loop
	"""

	def __init__(self, settings: "AppSettings | None" = None) -> None:
		self.settings = settings or get_settings()
		self.running = False

	async def start(self) -> None:
		"""Start the worker loop."""
		self.running = True
		logger.info(
			"Job worker started", simulation_mode=self.settings.enable_simulation
		)

		while self.running:
			try:
				await self._process_pending_jobs()
			except Exception as e:
				logger.error("Worker error", error=str(e))

			await asyncio.sleep(POLL_INTERVAL_SECONDS)

	async def stop(self) -> None:
		"""Stop the worker loop."""
		self.running = False
		logger.info("Job worker stopped")

	async def _process_pending_jobs(self) -> None:
		"""Process all pending jobs in NOT_STARTED state."""
		with Session(engine) as session:
			statement = select(MatcherJob).where(
				MatcherJob.current_status == JobStatus.NOT_STARTED
			)
			jobs = session.exec(statement).all()

			for job in jobs:
				try:
					await self._process_job(session, job)
				except Exception as e:
					logger.error(
						"Failed to process job",
						job_id=job.id,
						error=str(e),
					)
					job.current_status = JobStatus.MATCHING_ERROR
					job.error_data = {
						"message": str(e),
						"timestamp": datetime.now(UTC).isoformat(),
					}
					session.commit()

	async def _process_job(self, session: Session, job: MatcherJob) -> None:
		"""Process a single job through OCR and matching phases.

		Args:
			session: Database session
			job: MatcherJob to process
		"""
		logger.info("Processing job", job_id=job.id)

		job.current_status = JobStatus.OCR_STARTED
		job.started_on = datetime.now(UTC)
		session.commit()

		crops = list(
			session.exec(
				select(PetitionCrop)
				.join(PetitionScan, PetitionCrop.scan_id == PetitionScan.id)
				.where(PetitionScan.campaign_id == job.campaign_id)
			).all()
		)

		if not crops:
			logger.warning("No crops found for job", job_id=job.id)
			job.current_status = JobStatus.MATCHING_ERROR
			job.error_data = {
				"message": "No petition crops found for campaign",
				"timestamp": datetime.now(UTC).isoformat(),
			}
			session.commit()
			return

		ocr_job = OcrJob(
			matcher_job_id=job.id,
			status=JobStatus.OCR_STARTED,
		)
		session.add(ocr_job)
		session.commit()
		session.refresh(ocr_job)

		await self._run_ocr_phase(session, job, ocr_job, crops)
		await self._run_matching_phase(session, job, ocr_job)

		job.current_status = JobStatus.MATCHING_COMPLETED
		job.ended_on = datetime.now(UTC)
		session.commit()

		logger.info(
			"Job completed",
			job_id=job.id,
			status=job.current_status,
		)

	async def _run_ocr_phase(
		self,
		session: Session,
		job: MatcherJob,
		ocr_job: OcrJob,
		crops: list[PetitionCrop],
	) -> None:
		"""Run OCR phase (simulated for MVP).

		Creates OcrResult records with simulated extracted text.

		Args:
			session: Database session
			job: MatcherJob being processed
			ocr_job: OcrJob for this phase
			crops: List of PetitionCrop records to process
		"""
		logger.info(
			"Starting OCR phase",
			job_id=job.id,
			crop_count=len(crops),
		)

		for i, crop in enumerate(crops):
			await asyncio.sleep(OCR_SIMULATION_DELAY_SECONDS)

			extracted_text = self._simulate_ocr_result(i)

			ocr_result = OcrResult(
				crop_id=crop.id,
				ocr_job_id=ocr_job.id,
				extracted_text=extracted_text,
				confidence_score=random.uniform(0.75, 0.95),  # nosec B311 # Simulation only
			)
			session.add(ocr_result)

			progress = (i + 1) / len(crops) * 100
			logger.debug(
				"OCR progress",
				job_id=job.id,
				crop_index=i + 1,
				total=len(crops),
				progress=f"{progress:.0f}%",
			)

		ocr_job.status = JobStatus.OCR_COMPLETED
		job.current_status = JobStatus.OCR_COMPLETED
		session.commit()

		logger.info(
			"OCR phase completed",
			job_id=job.id,
			ocr_results=len(crops),
		)

	async def _run_matching_phase(
		self,
		session: Session,
		job: MatcherJob,
		ocr_job: OcrJob,
	) -> None:
		"""Run matching phase against voter database.

		For each OCR result, finds top 5 matching voters using fuzzy matching.

		Args:
			session: Database session
			job: MatcherJob being processed
			ocr_job: OcrJob with completed OCR results
		"""
		logger.info("Starting matching phase", job_id=job.id)

		job.current_status = JobStatus.MATCHING
		session.commit()

		ocr_results = session.exec(
			select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id)
		).all()

		campaign = session.get(Campaign, job.campaign_id)
		if not campaign:
			raise ValueError(f"Campaign not found: {job.campaign_id}")

		voters = session.exec(
			select(RegisteredVoter).where(
				RegisteredVoter.region_id == campaign.region_id
			)
		).all()

		if not voters:
			logger.warning(
				"No voters found for region",
				job_id=job.id,
				region_id=str(campaign.region_id),
			)
			return

		for ocr_result in ocr_results:
			await asyncio.sleep(MATCHING_DELAY_SECONDS)

			matches = self._find_top_matches(ocr_result, voters, top_n=5)

			for rank, match in enumerate(matches, start=1):
				match_result = MatchResult(
					ocr_result_id=ocr_result.id,
					matcher_job_id=job.id,
					rank=rank,
					voter_id=match["voter_id"],
					similarity_score=match["similarity_score"],
					confidence_level=match["confidence_level"],
					field_scores=match["field_scores"],
				)
				session.add(match_result)

		session.commit()

		logger.info(
			"Matching phase completed",
			job_id=job.id,
			ocr_results_processed=len(ocr_results),
		)

	def _simulate_ocr_result(self, index: int) -> dict[str, str]:
		"""Generate simulated OCR result.

		Args:
			index: Crop index for generating varied results

		Returns:
			Dictionary with simulated extracted text
		"""
		sample_names = [
			"John Smith",
			"Maria Garcia",
			"Robert Johnson",
			"Sarah Williams",
			"David Brown",
			"Jennifer Davis",
			"Michael Miller",
			"Lisa Wilson",
			"James Taylor",
			"Emily Anderson",
		]
		sample_addresses = [
			"123 Main St NW",
			"456 Oak Ave NE",
			"789 Pine St SW",
			"321 Elm Blvd SE",
			"654 Cedar Ln NW",
			"987 Maple Dr NE",
			"147 Birch Ave NW",
			"258 Walnut Way SE",
			"369 Cherry Ct NW",
			"741 Spruce Pl NE",
		]

		name_idx = index % len(sample_names)
		address_idx = index % len(sample_addresses)

		return {
			"name": sample_names[name_idx],
			"address": sample_addresses[address_idx],
		}

	def _find_top_matches(
		self,
		ocr_result: OcrResult,
		voters: list[RegisteredVoter],
		top_n: int = 5,
	) -> list[dict]:
		"""Find top matching voters for an OCR result.

		Uses simple string similarity for MVP. Can be enhanced with
		RapidFuzz for production.

		Args:
			ocr_result: OCR result to match
			voters: List of registered voters to match against
			top_n: Number of top matches to return

		Returns:
			List of match dictionaries with voter_id, similarity_score,
			confidence_level, and field_scores
		"""
		from rapidfuzz import fuzz

		ocr_name = str(ocr_result.extracted_text.get("name", ""))
		ocr_address = str(ocr_result.extracted_text.get("address", ""))

		matches = []
		for voter in voters:
			name_data = voter.name_data or {}
			address_data = voter.address_data or {}

			voter_name = " ".join(
				[
					name_data.get("first_name") or "",
					name_data.get("last_name") or "",
				]
			).strip()

			voter_address = " ".join(
				[
					address_data.get("street") or "",
					address_data.get("city") or "",
					address_data.get("state") or "",
					address_data.get("zip") or "",
				]
			).strip()

			name_score = fuzz.ratio(ocr_name, voter_name) / 100.0
			address_score = fuzz.ratio(ocr_address, voter_address) / 100.0

			if name_score + address_score > 0:
				similarity = (2 * name_score * address_score) / (
					name_score + address_score
				)
			else:
				similarity = 0.0

			if similarity >= 0.85:
				confidence = ConfidenceLevel.HIGH
			elif similarity >= 0.60:
				confidence = ConfidenceLevel.MEDIUM
			else:
				confidence = ConfidenceLevel.LOW

			matches.append(
				{
					"voter_id": voter.id,
					"similarity_score": similarity,
					"confidence_level": confidence,
					"field_scores": {
						"name": name_score,
						"address": address_score,
					},
				}
			)

		matches.sort(key=lambda x: x["similarity_score"], reverse=True)
		return matches[:top_n]


_worker: JobWorker | None = None


async def start_worker() -> None:
	"""Start the global job worker."""
	global _worker
	if _worker is None:
		_worker = JobWorker()
		await _worker.start()


async def stop_worker() -> None:
	"""Stop the global job worker."""
	global _worker
	if _worker:
		await _worker.stop()
		_worker = None
