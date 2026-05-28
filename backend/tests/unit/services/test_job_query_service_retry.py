"""Tests for JobQueryService.retry_job method.

Scenarios covered:
  - Retry from error state (OCR_FAILED) resets to NOT_STARTED
  - Retry from orphan state (OCR_STARTED) resets to NOT_STARTED
  - Retry from MATCHING state resets to NOT_STARTED
  - Retry on not-found raises ValueError
  - Retry on MATCHING_COMPLETED rejected
  - Retry on CANCELLED rejected
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.schema import Campaign, Region
from app.services.job_query_service import JobQueryService


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def sample_region(session):
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
def sample_campaign(session, sample_region):
    campaign = Campaign(
        unique_name="retry-test",
        title="Retry Test",
        year="2025",
        region_id=sample_region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def _create_job_with_status(session, campaign, status, **kwargs):
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=status,
        **kwargs,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


class TestRetryJobResetsErrorStateToNotStarted:
    def test_ocr_failed_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.OCR_FAILED,
            started_on=datetime.now(UTC) - timedelta(minutes=10),
            ended_on=datetime.now(UTC) - timedelta(minutes=9),
            error_data={"message": "OCR provider error"},
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.started_on is None
        assert job.ended_on is None
        assert job.error_data == {}

    def test_ocr_timeout_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.OCR_TIMEOUT,
            started_on=datetime.now(UTC) - timedelta(minutes=10),
            ended_on=datetime.now(UTC) - timedelta(minutes=9),
            error_data={"message": "OCR timed out"},
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.started_on is None
        assert job.ended_on is None
        assert job.error_data == {}

    def test_matching_error_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.MATCHING_ERROR,
            error_data={"message": "matching failed"},
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.error_data == {}


class TestRetryJobResetsOrphanState:
    def test_ocr_started_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.OCR_STARTED,
            started_on=datetime.now(UTC) - timedelta(minutes=6),
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.started_on is None

    def test_ocr_completed_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.OCR_COMPLETED,
            started_on=datetime.now(UTC) - timedelta(minutes=6),
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.started_on is None

    def test_matching_pending_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.MATCHING_PENDING,
            started_on=datetime.now(UTC) - timedelta(minutes=6),
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value
        session.refresh(job)
        assert job.started_on is None

    def test_matching_to_not_started(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.MATCHING,
            started_on=datetime.now(UTC) - timedelta(minutes=6),
        )
        service = JobQueryService(session)
        result = service.retry_job(job.id)

        assert result.status == JobStatus.NOT_STARTED.value


class TestRetryJobNotFound:
    def test_raises_value_error(self, session):
        service = JobQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.retry_job(99999)


class TestRetryJobTerminalCompleteRejected:
    def test_matching_completed_rejected(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.MATCHING_COMPLETED,
        )
        service = JobQueryService(session)
        with pytest.raises(ValueError, match="cannot be retried"):
            service.retry_job(job.id)


class TestRetryJobCancelledRejected:
    def test_cancelled_rejected(self, session, sample_campaign):
        job = _create_job_with_status(
            session,
            sample_campaign,
            JobStatus.CANCELLED,
        )
        service = JobQueryService(session)
        with pytest.raises(ValueError, match="cannot be retried"):
            service.retry_job(job.id)
