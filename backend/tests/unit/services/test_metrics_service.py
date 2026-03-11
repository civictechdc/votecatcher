"""Unit tests for MetricsService.

Tests cover campaign metrics computation including signature counts,
confidence breakdowns, and progress calculations.
"""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import (
	JobStatus,
	MatcherJob,
)
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


class TestMetricsService:
	"""Test suite for MetricsService."""

	@pytest.fixture
	def engine(self):
		"""Create in-memory SQLite engine for testing."""
		engine = create_engine("sqlite:///:memory:", echo=False)
		SQLModel.metadata.create_all(engine)
		return engine

	@pytest.fixture
	def session(self, engine):
		"""Create database session for each test."""
		with Session(engine) as session:
			yield session

	@pytest.fixture
	def sample_region(self, session):
		"""Create a sample region for testing."""
		region = Region(
			region_key="DC",
			region_name="Washington, DC",
			country_code="US",
		)
		session.add(region)
		session.commit()
		session.refresh(region)
		return region

	@pytest.fixture
	def sample_campaign(self, session, sample_region):
		"""Create a sample campaign for testing."""
		campaign = Campaign(
			unique_name="dc-2024",
			title="DC 2024",
			year="2024",
			region_id=sample_region.id,
		)
		session.add(campaign)
		session.commit()
		session.refresh(campaign)
		return campaign

	@pytest.fixture
	def sample_petition_scan(self, session, sample_campaign):
		"""Create a sample petition scan."""
		scan = PetitionScan(
			campaign_id=sample_campaign.id,
			original_filename="test_petition.pdf",
			stored_path="/tmp/test_petition.pdf",
			file_hash="abc123",
			page_count=3,
		)
		session.add(scan)
		session.commit()
		session.refresh(scan)
		return scan

	@pytest.fixture
	def sample_crops(self, session, sample_petition_scan):
		"""Create sample petition crops (signatures)."""
		crops = []
		for i in range(10):
			crop = PetitionCrop(
				scan_id=sample_petition_scan.id,
				crop_index=i,
				stored_path=f"/tmp/crop_{i}.png",
				crop_coordinates={"top": 0.0, "bottom": 0.1},
				page_number=1,
			)
			session.add(crop)
			crops.append(crop)
		session.commit()
		for crop in crops:
			session.refresh(crop)
		return crops

	@pytest.fixture
	def sample_job(self, session, sample_campaign):
		"""Create a sample matcher job."""
		job = MatcherJob(
			campaign_id=sample_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
			ended_on=datetime.now(UTC),
		)
		session.add(job)
		session.commit()
		session.refresh(job)
		return job

	def test_compute_metrics_empty_campaign(self, session, sample_campaign):
		"""Test metrics for campaign with no data."""
		from app.services.metrics import MetricsService

		service = MetricsService(session)
		metrics = service.compute_campaign_metrics(sample_campaign.id)

		assert metrics["total_signatures"] == 0
		assert metrics["processed"] == 0
		assert metrics["high_confidence"] == 0
		assert metrics["medium_confidence"] == 0
		assert metrics["low_confidence"] == 0
		assert metrics["progress_percentage"] == 0.0
		assert metrics["last_job"] is None

	def test_compute_metrics_with_results(
		self, session, sample_campaign, sample_crops, sample_job
	):
		"""Test metrics for campaign with processed results."""
		from app.services.metrics import MetricsService

		ocr_results = []
		for i, crop in enumerate(sample_crops):
			ocr = OcrResult(
				crop_id=crop.id,
				ocr_job_id=1,
				extracted_text={"name": f"Name {i}"},
			)
			session.add(ocr)
			ocr_results.append(ocr)
		session.commit()
		for ocr in ocr_results:
			session.refresh(ocr)

		confidence_levels = [
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.HIGH,
			ConfidenceLevel.MEDIUM,
			ConfidenceLevel.MEDIUM,
			ConfidenceLevel.LOW,
		]
		for i, (ocr, level) in enumerate(
			zip(ocr_results[:8], confidence_levels, strict=False)
		):
			match = MatchResult(
				ocr_result_id=ocr.id,
				matcher_job_id=sample_job.id,
				rank=1,
				voter_id=i + 1,
				similarity_score=0.9 if level == ConfidenceLevel.HIGH else 0.7,
				confidence_level=level,
			)
			session.add(match)
		session.commit()

		service = MetricsService(session)
		metrics = service.compute_campaign_metrics(sample_campaign.id)

		assert metrics["total_signatures"] == 10
		assert metrics["processed"] == 8
		assert metrics["high_confidence"] == 5
		assert metrics["medium_confidence"] == 2
		assert metrics["low_confidence"] == 1
		assert metrics["progress_percentage"] == 80.0
		assert metrics["last_job"]["id"] == sample_job.id

	def test_compute_metrics_includes_last_job(
		self, session, sample_campaign, sample_crops
	):
		"""Test that metrics include last job information."""
		from app.services.metrics import MetricsService

		job1 = MatcherJob(
			campaign_id=sample_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
			ended_on=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
		)
		session.add(job1)
		session.commit()
		session.refresh(job1)

		job2 = MatcherJob(
			campaign_id=sample_campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
			ended_on=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
		)
		session.add(job2)
		session.commit()
		session.refresh(job2)

		service = MetricsService(session)
		metrics = service.compute_campaign_metrics(sample_campaign.id)

		assert metrics["last_job"]["id"] == job2.id
		assert metrics["last_job"]["status"] == "MATCHING_COMPLETED"

	def test_compute_metrics_no_completed_job_shows_latest(
		self, session, sample_campaign
	):
		"""Test that metrics show latest job even if not completed."""
		from app.services.metrics import MetricsService

		job = MatcherJob(
			campaign_id=sample_campaign.id,
			current_status=JobStatus.MATCHING,
		)
		session.add(job)
		session.commit()
		session.refresh(job)

		service = MetricsService(session)
		metrics = service.compute_campaign_metrics(sample_campaign.id)

		assert metrics["last_job"]["id"] == job.id
		assert metrics["last_job"]["status"] == "MATCHING"
