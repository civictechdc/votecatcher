"""Tests for enhanced structured logging in orphan recovery and termination.

Verifies that _terminate_orphans_with_session and _recover_orphaned_jobs_with_session
emit per-job log events with job_id, previous_status, stale_duration_seconds, and reason.

Uses structlog.testing.capture_logs to assert on log output.
"""

from datetime import UTC, datetime, timedelta

import pytest
import structlog
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.schema import Campaign, Region


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
        unique_name="orphan-log-test",
        title="Orphan Log Test",
        year="2025",
        region_id=sample_region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


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


def _create_stale_job(session, campaign, status, minutes_stale=6):
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=status,
        started_on=datetime.now(UTC) - timedelta(minutes=minutes_stale),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


class TestTerminateOrphansLogging:
    """Feature: Enhanced logging for orphan termination on startup."""

    def test_terminate_logs_per_job_fields(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(
            session,
            sample_campaign,
            JobStatus.OCR_STARTED,
            started_on=datetime.now(UTC) - timedelta(minutes=10),
        )
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._terminate_orphans_with_session(session)

        terminate_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job terminated"
        ]
        assert len(terminate_logs) == 1
        log = terminate_logs[0]
        assert log["job_id"] == job.id
        assert log["previous_status"] == "OCR_STARTED"
        assert log["new_status"] == "OCR_FAILED"
        assert log["campaign_id"] == str(job.campaign_id)
        assert log["stale_duration_seconds"] is not None
        assert log["stale_duration_seconds"] > 0
        assert "reason" in log
        assert "OCR_STARTED" in log["reason"]
        assert log["log_level"] == "warning"

    def test_terminate_logs_stale_duration_none_when_no_started_on(
        self, session, sample_campaign
    ):
        from app.jobs.worker import JobWorker

        # Job with no started_on (created but never started processing)
        _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._terminate_orphans_with_session(session)

        terminate_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job terminated"
        ]
        assert len(terminate_logs) == 1
        assert terminate_logs[0]["stale_duration_seconds"] is None

    def test_terminate_logs_reason_mentions_restart(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        _create_job(
            session,
            sample_campaign,
            JobStatus.MATCHING,
            started_on=datetime.now(UTC) - timedelta(minutes=3),
        )
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._terminate_orphans_with_session(session)

        terminate_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job terminated"
        ]
        assert len(terminate_logs) == 1
        assert "restart" in terminate_logs[0]["reason"].lower()

    def test_terminate_no_orphans_no_per_job_logs(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        _create_job(session, sample_campaign, JobStatus.NOT_STARTED)
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._terminate_orphans_with_session(session)

        terminate_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job terminated"
        ]
        assert len(terminate_logs) == 0


class TestRecoverOrphansLogging:
    """Feature: Enhanced logging for periodic orphan recovery."""

    def test_recover_logs_per_job_fields(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_stale_job(
            session, sample_campaign, JobStatus.OCR_STARTED, minutes_stale=6
        )
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._recover_orphaned_jobs_with_session(session)

        recover_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job recovered"
        ]
        assert len(recover_logs) == 1
        log = recover_logs[0]
        assert log["job_id"] == job.id
        assert log["previous_status"] == "OCR_STARTED"
        assert log["new_status"] == "NOT_STARTED"
        assert log["campaign_id"] == str(job.campaign_id)
        assert log["stale_duration_seconds"] is not None
        assert log["stale_duration_seconds"] > 0
        assert "reason" in log
        assert "OCR_STARTED" in log["reason"]

    def test_recover_logs_stale_duration_none_when_no_started_on(
        self, session, sample_campaign
    ):
        from app.jobs.worker import JobWorker

        # Job with null started_on — query hits the `started_on.is_(None)` branch
        job = MatcherJob(
            campaign_id=sample_campaign.id,
            current_status=JobStatus.OCR_STARTED,
            started_on=None,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._recover_orphaned_jobs_with_session(session)

        recover_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job recovered"
        ]
        assert len(recover_logs) == 1
        assert recover_logs[0]["stale_duration_seconds"] is None
        assert "no started_on" in recover_logs[0]["reason"]

    def test_recover_logs_reason_mentions_timeout(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        _create_stale_job(
            session, sample_campaign, JobStatus.MATCHING, minutes_stale=10
        )
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._recover_orphaned_jobs_with_session(session)

        recover_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job recovered"
        ]
        assert len(recover_logs) == 1
        assert "timeout" in recover_logs[0]["reason"].lower()

    def test_recover_no_stale_jobs_no_logs(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        _create_job(
            session,
            sample_campaign,
            JobStatus.OCR_STARTED,
            started_on=datetime.now(UTC) - timedelta(seconds=30),
        )
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._recover_orphaned_jobs_with_session(session)

        recover_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job recovered"
        ]
        assert len(recover_logs) == 0

    def test_recover_multiple_jobs_each_logged(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        _create_stale_job(
            session, sample_campaign, JobStatus.OCR_STARTED, minutes_stale=6
        )
        _create_stale_job(session, sample_campaign, JobStatus.MATCHING, minutes_stale=8)
        worker = JobWorker()

        with structlog.testing.capture_logs() as cap_logs:
            worker._recover_orphaned_jobs_with_session(session)

        recover_logs = [
            entry for entry in cap_logs if entry["event"] == "Orphaned job recovered"
        ]
        assert len(recover_logs) == 2
        statuses = {entry["previous_status"] for entry in recover_logs}
        assert statuses == {"OCR_STARTED", "MATCHING"}
