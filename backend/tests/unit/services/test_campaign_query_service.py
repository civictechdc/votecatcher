"""Unit tests for CampaignQueryService.

BDD-style tests describing expected behaviour of the campaign query service
before the implementation exists.  These tests MUST fail (import error) until
the service is created.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload


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


def _seed_full_chain(session: Session, campaign: Campaign):
    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc123",
        page_count=1,
    )
    session.add(scan)
    session.flush()

    crop = PetitionCrop(
        scan_id=scan.id,
        crop_index=0,
        stored_path="/tmp/crop.png",
        crop_coordinates={"top": 0.0, "bottom": 0.1},
        page_number=1,
    )
    session.add(crop)
    session.flush()

    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=JobStatus.MATCHING_COMPLETED,
        ended_on=datetime.now(UTC),
    )
    session.add(job)
    session.flush()

    ocr = OcrResult(
        crop_id=crop.id,
        ocr_job_id=1,
        extracted_text={"name": "John Smith", "address": "123 Main St"},
    )
    session.add(ocr)
    session.flush()

    voter = RegisteredVoter(
        region_id=campaign.region_id,
        name_data={"first_name": "John", "last_name": "Doe"},
        address_data={
            "street": "456 Oak Ave",
            "city": "DC",
            "state": "DC",
            "zip": "20001",
        },
        data_hash="hash1",
    )
    session.add(voter)
    session.flush()

    match = MatchResult(
        ocr_result_id=ocr.id,
        matcher_job_id=job.id,
        rank=1,
        voter_id=voter.id,
        similarity_score=0.85,
        confidence_level=ConfidenceLevel.HIGH,
    )
    session.add(match)
    session.commit()

    return scan, crop, job, ocr, voter, match


class TestGetCampaignResults:
    """Feature: Campaign results query.

    As an API consumer
    I want to retrieve paginated match results for all jobs in a campaign
    So that I can display signature matching progress across an entire campaign.
    """

    def test_empty_campaign_returns_no_results(self, session: Session):
        """Scenario: Campaign has no jobs."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id)

        assert result.total == 0
        assert result.results == []
        assert result.page_size == 50

    def test_campaign_not_found_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_query_service import CampaignQueryService

        service = CampaignQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.get_campaign_results(uuid.uuid4())

    def test_campaign_with_match_results(self, session: Session):
        """Scenario: Campaign has one job with one match result."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)
        scan, crop, job, ocr, voter, match = _seed_full_chain(session, campaign)

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id)

        assert result.total == 1
        assert len(result.results) == 1

        r = result.results[0]
        assert r.ocr_result_id == ocr.id
        assert r.extracted_name == "John Smith"
        assert r.extracted_address == "123 Main St"
        assert r.crop_id == crop.id
        assert r.job_id == job.id

        assert len(r.predictions) == 1
        pred = r.predictions[0]
        assert pred.voter_name == "John Doe"
        assert pred.voter_address == "456 Oak Ave, DC, DC, 20001"
        assert pred.confidence == "HIGH"
        assert pred.rank == 1

    def test_pagination_splits_results(self, session: Session):
        """Scenario: 5 OCR results with page_size=2 yields 3 pages."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="multi.pdf",
            stored_path="/tmp/multi.pdf",
            file_hash="multi123",
            page_count=1,
        )
        session.add(scan)
        session.flush()

        job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.flush()

        for i in range(5):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/crop_{i}.png",
                crop_coordinates={},
                page_number=1,
            )
            session.add(crop)
            session.flush()

            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Name {i}"},
            )
            session.add(ocr)
            session.flush()

            match = MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                similarity_score=0.5,
                confidence_level=ConfidenceLevel.LOW,
            )
            session.add(match)
        session.commit()

        service = CampaignQueryService(session)

        page1 = service.get_campaign_results(campaign.id, page_size=2)
        assert page1.total == 5
        assert len(page1.results) == 2
        assert page1.page_size == 2
        assert page1.next_cursor is not None

        page2 = service.get_campaign_results(campaign.id, cursor=page1.next_cursor, page_size=2)
        assert page2.total == 5
        assert len(page2.results) == 2
        assert page2.next_cursor is not None

        page3 = service.get_campaign_results(campaign.id, cursor=page2.next_cursor, page_size=2)
        assert page3.total == 5
        assert len(page3.results) == 1
        assert page3.next_cursor is None

    def test_confidence_filter_excludes_non_matching(self, session: Session):
        """Scenario: Filtering by HIGH excludes LOW/MEDIUM results."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="filter.pdf",
            stored_path="/tmp/filter.pdf",
            file_hash="filter123",
            page_count=1,
        )
        session.add(scan)
        session.flush()

        job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.flush()

        levels = [ConfidenceLevel.HIGH, ConfidenceLevel.LOW, ConfidenceLevel.HIGH]
        for i, level in enumerate(levels):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/crop_f{i}.png",
                crop_coordinates={},
                page_number=1,
            )
            session.add(crop)
            session.flush()

            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Name {i}"},
            )
            session.add(ocr)
            session.flush()

            match = MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                similarity_score=0.5,
                confidence_level=level,
            )
            session.add(match)
        session.commit()

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id, confidence="HIGH")

        assert result.total == 2
        for r in result.results:
            assert r.predictions[0].confidence == "HIGH"

    def test_pages_are_disjoint_by_ocr_result_id(self, session: Session):
        """Scenario: Paginated pages never share the same ocr_result_id."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="disjoint.pdf",
            stored_path="/tmp/disjoint.pdf",
            file_hash="dj123",
            page_count=1,
        )
        session.add(scan)
        session.flush()

        job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.flush()

        for i in range(7):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/crop_d{i}.png",
                crop_coordinates={},
                page_number=1,
            )
            session.add(crop)
            session.flush()

            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Name {i}"},
            )
            session.add(ocr)
            session.flush()

            match = MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                similarity_score=0.5,
                confidence_level=ConfidenceLevel.LOW,
            )
            session.add(match)
        session.commit()

        service = CampaignQueryService(session)

        page_size = 3
        all_ids: set[int] = set()
        cursor = None
        while True:
            result = service.get_campaign_results(
                campaign.id, cursor=cursor, page_size=page_size
            )
            page_ids = {r.ocr_result_id for r in result.results}
            assert page_ids.isdisjoint(all_ids), "Cursor page overlaps previous pages"
            all_ids |= page_ids
            if not result.next_cursor:
                break
            cursor = result.next_cursor

        assert len(all_ids) == 7

    def test_multi_job_campaign_returns_only_latest_job_results(self, session: Session):
        """Scenario: Two jobs in same campaign, only latest job's results returned."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="multi_job.pdf",
            stored_path="/tmp/multi_job.pdf",
            file_hash="mj123",
            page_count=1,
        )
        session.add(scan)
        session.flush()

        job1 = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job1)
        session.flush()

        job2 = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job2)
        session.flush()

        for i, job in enumerate([job1, job2]):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/crop_mj{i}.png",
                crop_coordinates={},
                page_number=1,
            )
            session.add(crop)
            session.flush()

            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Name {i}"},
            )
            session.add(ocr)
            session.flush()

            match = MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                similarity_score=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
            session.add(match)
        session.commit()

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id)

        assert result.total == 1
        assert len(result.results) == 1
        assert result.results[0].job_id == job2.id

    def test_results_include_thumbnail_url(self, session: Session):
        """Scenario: Each result includes thumbnailUrl resolved from crop_id."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)
        scan, crop, job, ocr, voter, match = _seed_full_chain(session, campaign)

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id)

        assert len(result.results) == 1
        r = result.results[0]
        assert r.thumbnail_url == f"/api/crops/{crop.id}/image"


class TestGetSetupStatus:
    """Feature: Campaign setup status.

    As an API consumer
    I want to see the setup progress of a campaign
    So that I can guide the user through the workflow steps.
    """

    def test_empty_campaign_state(self, session: Session):
        """Scenario: No voter list, no petitions → state=empty."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "empty"
        assert status.voter_list.exists is False
        assert status.petitions.exists is False
        assert status.petitions.file_count == 0
        assert status.petitions.signature_count == 0

    def test_campaign_not_found_raises_value_error(self, session: Session):
        """Scenario: Campaign UUID does not exist."""
        from app.services.campaign_query_service import CampaignQueryService

        service = CampaignQueryService(session)
        with pytest.raises(ValueError, match="not found"):
            service.get_setup_status(uuid.uuid4())

    def test_voter_only_state(self, session: Session):
        """Scenario: Voter list uploaded, no petitions → state=voter_only."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        upload = VoterListUpload(
            region_id=region.id,
            original_filename="voters.csv",
            file_size=1024,
            row_count=100,
            status=UploadStatus.ACTIVE,
            uploaded_at=datetime.now(UTC),
        )
        session.add(upload)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "voter_only"
        assert status.voter_list.exists is True
        assert status.voter_list.row_count == 100

    def test_petitions_only_state(self, session: Session):
        """Scenario: Petitions uploaded, no voter list → state=petitions_only."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="petitions.pdf",
            stored_path="/tmp/petitions.pdf",
            file_hash="pet123",
            page_count=5,
        )
        session.add(scan)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "petitions_only"
        assert status.petitions.exists is True
        assert status.petitions.file_count == 1
        assert status.petitions.signature_count == 5

    def test_ready_to_process_state(self, session: Session):
        """Scenario: Voter list + petitions, no jobs → state=ready_to_process."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        upload = VoterListUpload(
            region_id=region.id,
            original_filename="voters.csv",
            file_size=1024,
            row_count=100,
            status=UploadStatus.ACTIVE,
            uploaded_at=datetime.now(UTC),
        )
        session.add(upload)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="petitions.pdf",
            stored_path="/tmp/petitions.pdf",
            file_hash="pet123",
            page_count=3,
        )
        session.add(scan)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "ready_to_process"
        assert status.voter_list.exists is True
        assert status.petitions.exists is True
        assert status.jobs.total == 0

    def test_has_jobs_state(self, session: Session):
        """Scenario: Voter list + petitions + jobs → state=has_jobs."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        upload = VoterListUpload(
            region_id=region.id,
            original_filename="voters.csv",
            file_size=1024,
            row_count=100,
            status=UploadStatus.ACTIVE,
            uploaded_at=datetime.now(UTC),
        )
        session.add(upload)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="petitions.pdf",
            stored_path="/tmp/petitions.pdf",
            file_hash="pet123",
            page_count=3,
        )
        session.add(scan)

        job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING,
        )
        session.add(job)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "has_jobs"
        assert status.jobs.total == 1
        assert status.jobs.active == 1

    def test_active_jobs_count_excludes_completed(self, session: Session):
        """Scenario: Mixed job statuses, only active ones counted."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        upload = VoterListUpload(
            region_id=region.id,
            original_filename="voters.csv",
            file_size=1024,
            row_count=100,
            status=UploadStatus.ACTIVE,
            uploaded_at=datetime.now(UTC),
        )
        session.add(upload)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="petitions.pdf",
            stored_path="/tmp/petitions.pdf",
            file_hash="pet123",
            page_count=3,
        )
        session.add(scan)

        active_job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING,
        )
        session.add(active_job)

        completed_job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(completed_job)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.jobs.total == 2
        assert status.jobs.active == 1

    def test_signature_count_handles_none_page_count(self, session: Session):
        """Scenario: PetitionScan with page_count=None contributes 0 to signature_count."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="no_pages.pdf",
            stored_path="/tmp/no_pages.pdf",
            file_hash="np123",
            page_count=None,
        )
        session.add(scan)
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.state == "petitions_only"
        assert status.petitions.file_count == 1
        assert status.petitions.signature_count == 0

    def test_signature_count_mixed_none_and_values(self, session: Session):
        """Scenario: Multiple scans, some None page_count — sums only non-None."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        session.add(
            PetitionScan(
                campaign_id=campaign.id,
                original_filename="a.pdf",
                stored_path="/tmp/a.pdf",
                file_hash="a1",
                page_count=5,
            )
        )
        session.add(
            PetitionScan(
                campaign_id=campaign.id,
                original_filename="b.pdf",
                stored_path="/tmp/b.pdf",
                file_hash="b2",
                page_count=None,
            )
        )
        session.add(
            PetitionScan(
                campaign_id=campaign.id,
                original_filename="c.pdf",
                stored_path="/tmp/c.pdf",
                file_hash="c3",
                page_count=3,
            )
        )
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.petitions.file_count == 3
        assert status.petitions.signature_count == 8

    def test_region_name_none_when_region_deleted(self, session: Session):
        """Scenario: Campaign FK points to deleted Region — region_name is None."""
        from sqlmodel import delete

        from app.services.campaign_query_service import CampaignQueryService

        region, campaign = _seed_campaign(session)

        upload = VoterListUpload(
            region_id=region.id,
            original_filename="voters.csv",
            file_size=512,
            row_count=50,
            status=UploadStatus.ACTIVE,
            uploaded_at=datetime.now(UTC),
        )
        session.add(upload)
        session.exec(delete(Region).where(Region.id == region.id))
        session.commit()

        service = CampaignQueryService(session)
        status = service.get_setup_status(campaign.id)

        assert status.voter_list.region_name is None
