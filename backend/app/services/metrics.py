"""Campaign metrics service for computing signature counts and confidence breakdowns."""

from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import Session, select

from app.data.database.model.jobs import MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan

logger = structlog.get_logger(__name__)


class CampaignMetrics:
	"""Response model for campaign metrics."""

	def __init__(
		self,
		total_signatures: int,
		processed: int,
		high_confidence: int,
		medium_confidence: int,
		low_confidence: int,
		progress_percentage: float,
		last_job: dict | None,
	):
		self.total_signatures = total_signatures
		self.processed = processed
		self.high_confidence = high_confidence
		self.medium_confidence = medium_confidence
		self.low_confidence = low_confidence
		self.progress_percentage = progress_percentage
		self.last_job = last_job

	def to_dict(self) -> dict:
		"""Convert to dictionary for API response."""
		return {
			"total_signatures": self.total_signatures,
			"processed": self.processed,
			"high_confidence": self.high_confidence,
			"medium_confidence": self.medium_confidence,
			"low_confidence": self.low_confidence,
			"progress_percentage": round(self.progress_percentage, 1),
			"last_job": self.last_job,
		}


class MetricsService:
	"""Service for computing campaign metrics."""

	def __init__(self, session: Session):
		self.session = session

	def compute_campaign_metrics(self, campaign_id: UUID) -> dict:
		"""Compute metrics for a campaign.

		Args:
			campaign_id: Campaign UUID

		Returns:
			Dictionary with metrics including total_signatures, processed,
			confidence breakdown, progress percentage, and last job info.
		"""
		total_signatures = self._count_total_signatures(campaign_id)
		processed, confidence_counts = self._count_processed_results(campaign_id)
		progress = self._calculate_progress(total_signatures, processed)
		last_job = self._get_last_job(campaign_id)

		metrics = CampaignMetrics(
			total_signatures=total_signatures,
			processed=processed,
			high_confidence=confidence_counts.get(ConfidenceLevel.HIGH, 0),
			medium_confidence=confidence_counts.get(ConfidenceLevel.MEDIUM, 0),
			low_confidence=confidence_counts.get(ConfidenceLevel.LOW, 0),
			progress_percentage=progress,
			last_job=last_job,
		)

		logger.debug(
			"Computed campaign metrics",
			campaign_id=str(campaign_id),
			total=total_signatures,
			processed=processed,
			progress=progress,
		)

		return metrics.to_dict()

	def _count_total_signatures(self, campaign_id: UUID) -> int:
		"""Count total signature crops for a campaign.

		Args:
			campaign_id: Campaign UUID

		Returns:
			Total number of petition crops across all scans
		"""
		scan_ids = self.session.exec(
			select(PetitionScan.id).where(PetitionScan.campaign_id == campaign_id)
		).all()

		if not scan_ids:
			return 0

		count = self.session.exec(
			select(func.count())
			.select_from(PetitionCrop)
			.where(PetitionCrop.scan_id.in_(scan_ids))
		).one()

		return count or 0

	def _count_processed_results(
		self, campaign_id: UUID
	) -> tuple[int, dict[ConfidenceLevel, int]]:
		"""Count processed results and group by confidence.

		Args:
			campaign_id: Campaign UUID

		Returns:
			Tuple of (processed_count, confidence_counts_dict)
		"""
		job_ids = self.session.exec(
			select(MatcherJob.id).where(MatcherJob.campaign_id == campaign_id)
		).all()

		if not job_ids:
			return 0, {}

		results = self.session.exec(
			select(MatchResult)
			.where(MatchResult.matcher_job_id.in_(job_ids))
			.where(MatchResult.rank == 1)
		).all()

		unique_ocr_ids = {r.ocr_result_id for r in results}
		confidence_counts: dict[ConfidenceLevel, int] = {}

		for result in results:
			level = result.confidence_level
			confidence_counts[level] = confidence_counts.get(level, 0) + 1

		return len(unique_ocr_ids), confidence_counts

	def _calculate_progress(self, total: int, processed: int) -> float:
		"""Calculate progress percentage.

		Args:
			total: Total signatures
			processed: Processed signatures

		Returns:
			Progress percentage (0-100)
		"""
		if total == 0:
			return 0.0
		return (processed / total) * 100

	def _get_last_job(self, campaign_id: UUID) -> dict | None:
		"""Get information about the latest job for a campaign.

		Args:
			campaign_id: Campaign UUID

		Returns:
			Dictionary with job id, status, and completed_at, or None
		"""
		jobs = self.session.exec(
			select(MatcherJob)
			.where(MatcherJob.campaign_id == campaign_id)
			.order_by(MatcherJob.created_at.desc())
		).all()

		if not jobs:
			return None

		last_job = jobs[0]
		return {
			"id": last_job.id,
			"status": last_job.current_status.value,
			"completed_at": last_job.ended_on.isoformat()
			if last_job.ended_on
			else None,
		}
