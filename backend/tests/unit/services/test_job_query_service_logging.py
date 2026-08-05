"""Tests for structured logging in JobQueryService.

Verifies that state-changing operations (create, start, cancel, retry)
emit structured log events with the correct fields.

Uses structlog.testing.capture_logs to assert on log output without
requiring the stdlib logging integration.
"""

from datetime import UTC, datetime, timedelta

import pytest
import structlog
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.llm_provider_config import LlmProviderConfig
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload
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
        unique_name="log-test",
        title="Log Test",
        year="2025",
        region_id=sample_region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def _seed_full_setup(session, campaign):
    """Seed petition scan, voter list, and OCR provider config."""
    region_id = campaign.region_id
    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc123",
        page_count=1,
    )
    session.add(scan)
    upload = VoterListUpload(
        region_id=region_id,
        original_filename="voters.csv",
        file_size=1024,
        row_count=100,
        status=UploadStatus.ACTIVE,
    )
    session.add(upload)
    config = LlmProviderConfig(
        provider="openai",
        api_key="sk-test-key-for-unit-tests",  # pragma: allowlist secret
        model="gpt-4o-mini",
        is_configured=True,
    )
    session.add(config)
    session.commit()


def _create_job(session, campaign, status, **kwargs):
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=status,
        **kwargs,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


class TestCreateJobLogging:
    """Feature: Structured logging for job creation."""

    def test_create_job_logs_event(self, session, sample_campaign):
        _seed_full_setup(session, sample_campaign)
        service = JobQueryService(session)

        with structlog.testing.capture_logs() as cap_logs:
            service.create_job(campaign_id=sample_campaign.id)

        create_logs = [entry for entry in cap_logs if entry["event"] == "Job created"]
        assert len(create_logs) == 1
        log = create_logs[0]
        assert log["job_id"] is not None
        assert log["status"] == "NOT_STARTED"
        assert log["campaign_id"] == str(sample_campaign.id)
        assert log["log_level"] == "info"


class TestCancelJobLogging:
    """Feature: Structured logging for job cancellation."""

    def test_cancel_job_logs_status_transition(self, session, sample_campaign):
        job = _create_job(session, sample_campaign, JobStatus.NOT_STARTED)
        service = JobQueryService(session)

        with structlog.testing.capture_logs() as cap_logs:
            service.cancel_job(job.id)

        cancel_logs = [entry for entry in cap_logs if entry["event"] == "Job cancelled"]
        assert len(cancel_logs) == 1
        log = cancel_logs[0]
        assert log["job_id"] == job.id
        assert log["previous_status"] == "NOT_STARTED"
        assert log["new_status"] == "CANCELLED"
        assert log["log_level"] == "info"


class TestStartJobLogging:
    """Feature: Structured logging for job start."""

    def test_start_job_logs_status_transition(self, session, sample_campaign):
        _seed_full_setup(session, sample_campaign)
        job = _create_job(session, sample_campaign, JobStatus.NOT_STARTED)
        service = JobQueryService(session)

        with structlog.testing.capture_logs() as cap_logs:
            service.start_job(job.id)

        start_logs = [entry for entry in cap_logs if entry["event"] == "Job started"]
        assert len(start_logs) == 1
        log = start_logs[0]
        assert log["job_id"] == job.id
        assert log["previous_status"] == "NOT_STARTED"
        assert log["new_status"] == "OCR_PENDING"
        assert log["log_level"] == "info"


class TestRetryJobLogging:
    """Feature: Structured logging for job retry."""

    def test_retry_job_logs_status_transition(self, session, sample_campaign):
        job = _create_job(
            session,
            sample_campaign,
            JobStatus.OCR_FAILED,
            error_data={"message": "OCR provider error"},
        )
        service = JobQueryService(session)

        with structlog.testing.capture_logs() as cap_logs:
            service.retry_job(job.id)

        retry_logs = [entry for entry in cap_logs if entry["event"] == "Job retried"]
        assert len(retry_logs) == 1
        log = retry_logs[0]
        assert log["job_id"] == job.id
        assert log["previous_status"] == "OCR_FAILED"
        assert log["new_status"] == "NOT_STARTED"
        assert log["log_level"] == "info"

    def test_retry_job_from_orphan_logs_status_transition(
        self, session, sample_campaign
    ):
        job = _create_job(
            session,
            sample_campaign,
            JobStatus.OCR_STARTED,
            started_on=datetime.now(UTC) - timedelta(minutes=6),
        )
        service = JobQueryService(session)

        with structlog.testing.capture_logs() as cap_logs:
            service.retry_job(job.id)

        retry_logs = [entry for entry in cap_logs if entry["event"] == "Job retried"]
        assert len(retry_logs) == 1
        log = retry_logs[0]
        assert log["previous_status"] == "OCR_STARTED"
        assert log["new_status"] == "NOT_STARTED"
