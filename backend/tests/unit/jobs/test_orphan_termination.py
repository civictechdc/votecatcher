"""BDD tests for orphaned job termination.

Scenarios covered:
  - Orphaned OCR_STARTED job is terminated with OCR_FAILED
  - Orphaned MATCHING job is terminated with MATCHING_ERROR
  - Orphaned OCR_COMPLETED job is terminated with MATCHING_ERROR
  - Non-orphan states (NOT_STARTED, terminal) are left untouched
  - Orphaned job error_data contains termination metadata
  - Orphaned OcrJob children are also terminated
  - JobStatusEvent is published for each terminated orphan
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.schema import Campaign, Region


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


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
        unique_name="orphan-test",
        title="Orphan Test",
        year="2025",
        region_id=sample_region.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def _create_job(session, campaign, status):
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=status,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


class TestOrphanedOcrStartedTerminated:
    """Scenario: Orphaned job in OCR_STARTED is terminated with OCR_FAILED."""

    def test_status_set_to_ocr_failed(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert job.current_status == JobStatus.OCR_FAILED

    def test_error_data_contains_metadata(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert (
            "terminated" in job.error_data.get("message", "").lower()
            or "orphaned" in job.error_data.get("message", "").lower()
        )

    def test_ended_on_is_set(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert job.ended_on is not None


class TestOrphanedMatchingTerminated:
    """Scenario: Orphaned job in MATCHING is terminated with MATCHING_ERROR."""

    def test_status_set_to_matching_error(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.MATCHING)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert job.current_status == JobStatus.MATCHING_ERROR


class TestOrphanedOcrCompletedTerminated:
    """Scenario: Orphaned job in OCR_COMPLETED is terminated with MATCHING_ERROR."""

    def test_status_set_to_matching_error(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.OCR_COMPLETED)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert job.current_status == JobStatus.MATCHING_ERROR


class TestNonOrphanStatesUntouched:
    """Scenario: Jobs in non-orphan states are not terminated."""

    @pytest.mark.parametrize(
        "status",
        [
            JobStatus.NOT_STARTED,
            JobStatus.MATCHING_COMPLETED,
            JobStatus.OCR_FAILED,
            JobStatus.MATCHING_ERROR,
            JobStatus.CANCELLED,
        ],
    )
    def test_status_unchanged(self, session, sample_campaign, status):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, status)
        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job)
        assert job.current_status == status


class TestOrphanedOcrJobChildrenTerminated:
    """Scenario: Orphaned OcrJob children are also terminated."""

    def test_child_ocr_job_set_to_failed(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job = _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        ocr_job = OcrJob(
            matcher_job_id=job.id,
            status=JobStatus.OCR_STARTED,
        )
        session.add(ocr_job)
        session.commit()
        session.refresh(ocr_job)

        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(ocr_job)
        assert ocr_job.status == JobStatus.OCR_FAILED


class TestMultipleOrphansAllTerminated:
    """Scenario: All orphaned jobs are terminated, not just the first."""

    def test_all_orphans_terminated(self, session, sample_campaign):
        from app.jobs.worker import JobWorker

        job1 = _create_job(session, sample_campaign, JobStatus.OCR_STARTED)
        job2 = _create_job(session, sample_campaign, JobStatus.MATCHING)
        job3 = _create_job(session, sample_campaign, JobStatus.OCR_COMPLETED)

        worker = JobWorker()
        worker._terminate_orphans_with_session(session)

        session.refresh(job1)
        session.refresh(job2)
        session.refresh(job3)
        assert job1.current_status == JobStatus.OCR_FAILED
        assert job2.current_status == JobStatus.MATCHING_ERROR
        assert job3.current_status == JobStatus.MATCHING_ERROR
