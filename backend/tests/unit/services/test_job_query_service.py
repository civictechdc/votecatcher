"""Unit tests for JobQueryService.

BDD-style tests describing expected behaviour of the job query service
before the implementation exists.  These tests MUST fail (import error) until
the service is created.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


def _seed_campaign(session: Session) -> tuple[Region, Campaign]:
    region = Region(
        region_key="DC",
        region_name="Washington, DC",
        country_code="US",
    )
    session.add(region)
    session.flush()
    campaign = Campaign(
        unique_name="dc-2024",
        title="DC 2024",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.flush()
    return region, campaign


def _seed_petition_scan(session: Session, campaign: Campaign) -> PetitionScan:
    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc123",
        page_count=1,
    )
    session.add(scan)
    session.flush()
    return scan


def _seed_voter_list_upload(session: Session, region_id) -> None:
    from app.data.database.model.voter_list_upload import (
        UploadStatus,
        VoterListUpload,
    )

    upload = VoterListUpload(
        region_id=region_id,
        original_filename="voters.csv",
        file_size=1024,
        row_count=100,
        status=UploadStatus.ACTIVE,
    )
    session.add(upload)
    session.flush()


def _seed_llm_provider(session: Session) -> None:
    from app.data.database.model.llm_provider_config import LlmProviderConfig

    config = LlmProviderConfig(
        provider="openai",
        api_key="sk-test-key-for-unit-tests",  # pragma: allowlist secret
        model="gpt-4o-mini",
        is_configured=True,
    )
    session.add(config)
    session.flush()


def _seed_job(
    session: Session,
    campaign: Campaign,
    status: JobStatus = JobStatus.NOT_STARTED,
    **kwargs,
) -> MatcherJob:
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=status,
        **kwargs,
    )
    session.add(job)
    session.flush()
    return job


class TestListJobs:
    """Feature: Job listing.

    As an API consumer
    I want to list all matcher jobs
    So that I can see job status across campaigns.
    """

    def test_empty_database_returns_empty_list(self, session: Session):
        """Scenario: No jobs exist."""
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        result = service.list_jobs()

        assert result.jobs == []
        assert result.total == 0

    def test_single_job_returns_list_of_one(self, session: Session):
        """Scenario: One job exists."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign)

        service = JobQueryService(session)
        result = service.list_jobs()

        assert result.total == 1
        assert len(result.jobs) == 1
        assert result.jobs[0].job_id == job.id
        assert result.jobs[0].status == "NOT_STARTED"

    def test_multiple_jobs_returns_all(self, session: Session):
        """Scenario: Multiple jobs across campaigns."""
        from app.services.job_query_service import JobQueryService

        region1, campaign1 = _seed_campaign(session)

        region2 = Region(
            region_key="VA",
            region_name="Virginia",
            country_code="US",
        )
        session.add(region2)
        session.flush()
        campaign2 = Campaign(
            unique_name="va-2024",
            title="VA 2024",
            year="2024",
            region_id=region2.id,
        )
        session.add(campaign2)
        session.flush()

        _seed_job(session, campaign1)
        _seed_job(session, campaign2, status=JobStatus.OCR_STARTED)

        service = JobQueryService(session)
        result = service.list_jobs()

        assert result.total == 2
        statuses = {j.status for j in result.jobs}
        assert "NOT_STARTED" in statuses
        assert "OCR_STARTED" in statuses


class TestGetJob:
    """Feature: Single job retrieval.

    As an API consumer
    I want to retrieve a specific job by ID
    So that I can check its detailed status.
    """

    def test_existing_job_returns_details(self, session: Session):
        """Scenario: Job exists in database."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, provider_name="openai")

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.job_id == job.id
        assert result.status == "NOT_STARTED"
        assert result.campaign_id == campaign.id
        assert result.campaign_name == "dc-2024"
        assert result.provider_name == "openai"

    def test_nonexistent_job_raises_value_error(self, session: Session):
        """Scenario: Job ID does not exist."""
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.get_job(99999)


class TestCreateJob:
    """Feature: Job creation.

    As an API consumer
    I want to create a new matcher job for a campaign
    So that OCR and matching can be initiated.
    """

    def test_create_job_success(self, session: Session):
        """Scenario: Valid campaign with petition scans."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        _seed_petition_scan(session, campaign)
        _seed_voter_list_upload(session, region.id)
        _seed_llm_provider(session)

        service = JobQueryService(session)
        result = service.create_job(
            campaign_id=campaign.id,
            provider_name="openai",
            provider_model="gpt-4o",
        )

        assert result.status == "NOT_STARTED"
        assert result.campaign_id == campaign.id
        assert result.campaign_name == "dc-2024"
        assert result.provider_name == "openai"
        assert result.provider_model == "gpt-4o"
        assert result.is_orphaned is False

    def test_create_job_campaign_not_found(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.create_job(campaign_id=uuid.uuid4())

    def test_create_job_no_petition_scans(self, session: Session):
        """Scenario: Campaign exists but has no petition scans."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="No petition scans"):
            service.create_job(campaign_id=campaign.id)

    def test_create_job_with_force_reprocess(self, session: Session):
        """Scenario: Create job with force_reprocess flag."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        _seed_petition_scan(session, campaign)
        _seed_voter_list_upload(session, region.id)
        _seed_llm_provider(session)

        service = JobQueryService(session)
        result = service.create_job(
            campaign_id=campaign.id,
            force_reprocess=True,
        )

        assert result.force_reprocess is True


class TestCreateJobPrerequisites:
    """Feature: Job creation pre-flight validation.

    As the system
    I want to reject job creation when prerequisites are missing
    So that jobs never enter a state where they'll immediately fail.

    Background:
        Given a campaign with petition scans
    """

    @pytest.fixture
    def _seeded(self, session: Session):
        region, campaign = _seed_campaign(session)
        _seed_petition_scan(session, campaign)
        return campaign

    def test_rejects_when_no_voter_list_uploaded(self, session: Session, _seeded):
        """Scenario: Campaign has no voter list uploaded for its region.

        Given a campaign with scans but no voter list
        When create_job is called
        Then it raises ValueError mentioning voter list.
        """
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="voter list"):
            service.create_job(campaign_id=_seeded.id)

    def test_rejects_when_no_ocr_provider_configured(self, session: Session, _seeded):
        """Scenario: No OCR provider is configured in DB or env.

        Given a campaign with scans and voter list but no provider
        When create_job is called
        Then it raises ValueError mentioning OCR provider.
        """
        from app.services.job_query_service import JobQueryService

        from app.data.database.model.voter_list_upload import (
            UploadStatus,
            VoterListUpload,
        )

        upload = VoterListUpload(
            region_id=_seeded.region_id,
            original_filename="voters.csv",
            file_size=1024,
            row_count=100,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload)
        session.commit()

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="OCR provider"):
            service.create_job(campaign_id=_seeded.id)


class TestCancelJob:
    """Feature: Job cancellation.

    As an API consumer
    I want to cancel a running or pending job
    So that I can stop processing and free resources.
    """

    def test_cancel_not_started_job(self, session: Session):
        """Scenario: Cancel a NOT_STARTED job."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.NOT_STARTED)

        service = JobQueryService(session)
        result = service.cancel_job(job.id)

        assert result.status == "CANCELLED"
        assert result.is_orphaned is False

    def test_cancel_ocr_started_job(self, session: Session):
        """Scenario: Cancel an OCR_STARTED (orphaned) job."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.OCR_STARTED)

        service = JobQueryService(session)
        result = service.cancel_job(job.id)

        assert result.status == "CANCELLED"

    def test_cancel_matching_job(self, session: Session):
        """Scenario: Cancel a MATCHING (in-progress) job."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.MATCHING)

        service = JobQueryService(session)
        result = service.cancel_job(job.id)

        assert result.status == "CANCELLED"

    def test_cancel_completed_job_raises_value_error(self, session: Session):
        """Scenario: Cannot cancel a completed job."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.MATCHING_COMPLETED)

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="cannot be cancelled"):
            service.cancel_job(job.id)

    def test_cancel_nonexistent_job_raises_value_error(self, session: Session):
        """Scenario: Job ID does not exist."""
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.cancel_job(99999)


class TestStartJob:
    """Feature: Job start.

    As an API consumer
    I want to start a NOT_STARTED job
    So that OCR and matching pipeline begins.
    """

    def test_start_job_success(self, session: Session):
        """Scenario: NOT_STARTED job with petition scans."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        _seed_petition_scan(session, campaign)
        job = _seed_job(session, campaign, status=JobStatus.NOT_STARTED)

        service = JobQueryService(session)
        result = service.start_job(job.id)

        assert result.status == "OCR_PENDING"
        assert result.is_orphaned is False

    def test_start_job_not_found(self, session: Session):
        """Scenario: Job ID does not exist."""
        from app.services.job_query_service import JobQueryService

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.start_job(99999)

    def test_start_job_wrong_state(self, session: Session):
        """Scenario: Job is already in progress."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.OCR_STARTED)

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="cannot be started"):
            service.start_job(job.id)

    def test_start_job_no_scans(self, session: Session):
        """Scenario: Campaign has no petition scans."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.NOT_STARTED)

        service = JobQueryService(session)
        with pytest.raises(ValueError, match="no petition scans"):
            service.start_job(job.id)


class TestBuildJobResponse:
    """Feature: Job response formatting.

    As the system
    I want to consistently format MatcherJob records into API responses
    So that the frontend receives predictable data structures.
    """

    def test_error_data_message_extraction(self, session: Session):
        """Scenario: error_data contains 'message' key."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(
            session,
            campaign,
            status=JobStatus.OCR_FAILED,
        )
        job.error_data = {"message": "API rate limit exceeded"}
        session.add(job)
        session.commit()

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.error_message == "API rate limit exceeded"

    def test_error_data_error_key_extraction(self, session: Session):
        """Scenario: error_data contains 'error' key instead of 'message'."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(
            session,
            campaign,
            status=JobStatus.OCR_FAILED,
        )
        job.error_data = {"error": "Connection timeout"}
        session.add(job)
        session.commit()

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.error_message == "Connection timeout"

    def test_error_data_empty_returns_none(self, session: Session):
        """Scenario: error_data is empty dict."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.NOT_STARTED)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.error_message is None

    def test_orphaned_detection_ocr_started(self, session: Session):
        """Scenario: Job in OCR_STARTED state is orphaned."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.OCR_STARTED)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.is_orphaned is True

    def test_orphaned_detection_matching_pending(self, session: Session):
        """Scenario: Job in MATCHING_PENDING state is orphaned."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.MATCHING_PENDING)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.is_orphaned is True

    def test_orphaned_detection_matching(self, session: Session):
        """Scenario: Job in MATCHING state is orphaned."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.MATCHING)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.is_orphaned is True

    def test_not_orphaned_in_completed(self, session: Session):
        """Scenario: Job in MATCHING_COMPLETED is not orphaned."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(
            session,
            campaign,
            status=JobStatus.MATCHING_COMPLETED,
            ended_on=datetime.now(UTC),
        )

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.is_orphaned is False

    def test_not_orphaned_in_not_started(self, session: Session):
        """Scenario: Job in NOT_STARTED is not orphaned."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign, status=JobStatus.NOT_STARTED)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.is_orphaned is False

    def test_campaign_name_included(self, session: Session):
        """Scenario: Job response includes campaign unique_name."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign)

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.campaign_name == "dc-2024"

    def test_campaign_name_none_when_missing(self, session: Session):
        """Scenario: Campaign has been deleted (orphan FK)."""
        from app.services.job_query_service import JobQueryService

        region, campaign = _seed_campaign(session)
        job = _seed_job(session, campaign)
        session.delete(campaign)
        session.commit()

        service = JobQueryService(session)
        result = service.get_job(job.id)

        assert result.campaign_name is None


class TestGetPhase:
    """Feature: Phase determination from status string.

    As the system
    I want to map job statuses to human-readable phases
    So that the SSE stream can communicate progress clearly.
    """

    def test_ocr_statuses_map_to_ocr_phase(self):
        """Scenario: OCR-related statuses return 'ocr'."""
        from app.services.job_query_service import JobQueryService

        assert JobQueryService.get_phase("OCR_STARTED") == "ocr"
        assert JobQueryService.get_phase("OCR_PENDING") == "ocr"
        assert JobQueryService.get_phase("OCR_COMPLETED") == "ocr"

    def test_matching_statuses_map_to_matching_phase(self):
        """Scenario: MATCHING-related statuses return 'matching'."""
        from app.services.job_query_service import JobQueryService

        assert JobQueryService.get_phase("MATCHING_PENDING") == "matching"
        assert JobQueryService.get_phase("MATCHING") == "matching"

    def test_completed_maps_to_complete_phase(self):
        """Scenario: MATCHING_COMPLETED returns 'complete'."""
        from app.services.job_query_service import JobQueryService

        assert JobQueryService.get_phase("MATCHING_COMPLETED") == "complete"

    def test_error_statuses_map_to_error_phase(self):
        """Scenario: Error/failure/timeout statuses return 'error'."""
        from app.services.job_query_service import JobQueryService

        assert JobQueryService.get_phase("OCR_FAILED") == "error"
        assert JobQueryService.get_phase("OCR_TIMEOUT") == "error"
        assert JobQueryService.get_phase("MATCHING_ERROR") == "error"

    def test_unknown_status(self):
        """Scenario: Unrecognized status returns 'unknown'."""
        from app.services.job_query_service import JobQueryService

        assert JobQueryService.get_phase("NOT_STARTED") == "unknown"
        assert JobQueryService.get_phase("CANCELLED") == "unknown"
