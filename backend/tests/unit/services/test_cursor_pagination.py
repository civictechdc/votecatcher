"""BDD behavioral tests for keyset (cursor) pagination.

RED phase: Tests reference cursor/next_cursor which do not exist yet.
All tests must FAIL until implementation is added.
"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


def _seed_region(session: Session) -> Region:
    region = Region(
        id=uuid4(), region_key="DC", region_name="Washington, DC", country_code="US"
    )
    session.add(region)
    session.flush()
    return region


def _seed_campaign(session: Session, region: Region) -> Campaign:
    campaign = Campaign(
        id=uuid4(),
        unique_name=f"cursor-test-{uuid4().hex[:8]}",
        title="Cursor Test",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.flush()
    return campaign


def _seed_scan(session: Session, campaign: Campaign) -> PetitionScan:
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


def _seed_job(session: Session, campaign: Campaign) -> MatcherJob:
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=JobStatus.MATCHING_COMPLETED,
    )
    session.add(job)
    session.flush()
    return job


def _build_ocr_chain(
    session: Session, job: MatcherJob, scan: PetitionScan, n: int
) -> list[OcrResult]:
    """Create n crops + OCR results + 1 match result each."""
    ocr_results = []
    for i in range(n):
        crop = PetitionCrop(
            scan_id=scan.id,
            crop_index=i,
            stored_path=f"/tmp/crop_{i}.png",
            crop_coordinates={"top": 0.0, "bottom": 0.1},
            page_number=1,
        )
        session.add(crop)
        session.flush()

        ocr = OcrResult(
            crop_id=crop.id,
            ocr_job_id=1,
            extracted_text={"name": f"Signature {i}"},
        )
        session.add(ocr)
        session.flush()
        ocr_results.append(ocr)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.85,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
    session.commit()
    return ocr_results


class TestKeysetPaginationJobResults:
    """Feature: Cursor-based pagination for job results.

    As an API consumer
    I want to paginate results using a cursor instead of page offset
    So that performance stays constant regardless of position in the result set.
    """

    def test_cursor_returns_first_page_when_none(self, session):
        """Scenario: No cursor provided returns first page."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 10)

        service = ResultsQueryService(session)
        result = service.get_results(job.id, cursor=None, page_size=3)

        assert len(result.results) == 3
        assert result.total == 10

    def test_cursor_returns_next_page_after_given_id(self, session):
        """Scenario: Cursor set to last OCR ID of page 1 returns page 2."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 10)

        service = ResultsQueryService(session)
        page1 = service.get_results(job.id, cursor=None, page_size=3)

        last_ocr_id = page1.results[-1].ocr_result_id
        page2 = service.get_results(job.id, cursor=last_ocr_id, page_size=3)

        assert len(page2.results) == 3
        assert all(r.ocr_result_id > last_ocr_id for r in page2.results)

    def test_cursor_returns_empty_beyond_last_page(self, session):
        """Scenario: Cursor beyond all results returns empty with null next_cursor."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        ocr_results = _build_ocr_chain(session, job, scan, 5)

        max_ocr_id = max(o.id for o in ocr_results)
        service = ResultsQueryService(session)
        result = service.get_results(job.id, cursor=max_ocr_id, page_size=3)

        assert len(result.results) == 0
        assert result.next_cursor is None

    def test_next_cursor_populated_when_more_results_exist(self, session):
        """Scenario: Response includes next_cursor when more pages available."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 10)

        service = ResultsQueryService(session)
        result = service.get_results(job.id, cursor=None, page_size=3)

        assert result.next_cursor is not None
        assert result.next_cursor == result.results[-1].ocr_result_id

    def test_next_cursor_null_on_last_page(self, session):
        """Scenario: Last page has next_cursor = None."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 5)

        service = ResultsQueryService(session)
        result = service.get_results(job.id, cursor=None, page_size=5)

        assert result.next_cursor is None

    def test_cursor_zero_returns_first_page(self, session):
        """Scenario: cursor=0 is equivalent to no cursor (first page)."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 5)

        service = ResultsQueryService(session)
        result = service.get_results(job.id, cursor=0, page_size=3)

        assert len(result.results) == 3
        assert result.total == 5

    def test_cursor_pages_cover_all_results_without_gaps(self, session):
        """Scenario: Walking all cursor pages covers every OCR result exactly once."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 10)

        service = ResultsQueryService(session)
        all_ids: set[int] = set()
        cursor = None

        while True:
            result = service.get_results(job.id, cursor=cursor, page_size=3)
            page_ids = {r.ocr_result_id for r in result.results}
            assert page_ids.isdisjoint(all_ids), "Cursor pages must not overlap"
            all_ids |= page_ids
            if result.next_cursor is None:
                break
            cursor = result.next_cursor

        assert len(all_ids) == 10

    def test_cursor_with_confidence_filter(self, session):
        """Scenario: Cursor pagination works with confidence filter."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        crop = PetitionCrop(
            scan_id=scan.id,
            crop_index=0,
            stored_path="/tmp/crop_h.png",
            crop_coordinates={},
            page_number=1,
        )
        session.add(crop)
        session.flush()
        ocr_high = OcrResult(
            crop_id=crop.id, ocr_job_id=1, extracted_text={"name": "High"}
        )
        session.add(ocr_high)
        session.flush()

        crop2 = PetitionCrop(
            scan_id=scan.id,
            crop_index=1,
            stored_path="/tmp/crop_l.png",
            crop_coordinates={},
            page_number=1,
        )
        session.add(crop2)
        session.flush()
        ocr_low = OcrResult(
            crop_id=crop2.id, ocr_job_id=1, extracted_text={"name": "Low"}
        )
        session.add(ocr_low)
        session.flush()

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr_high.id,
                voter_id=None,
                rank=1,
                similarity_score=0.95,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr_low.id,
                voter_id=None,
                rank=1,
                similarity_score=0.40,
                confidence_level=ConfidenceLevel.LOW,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(
            job.id, cursor=None, page_size=10, confidence=ConfidenceLevel.HIGH
        )

        assert result.total == 1
        assert len(result.results) == 1
        assert result.results[0].predictions[0].confidence == "HIGH"


class TestKeysetPaginationCampaignResults:
    """Feature: Cursor-based pagination for campaign results.

    Same cursor contract as job results, applied to the campaign endpoint.
    """

    def _build_campaign_chain(
        self, session: Session, n: int
    ) -> tuple[Region, Campaign, MatcherJob]:
        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, n)
        return region, campaign, job

    def test_campaign_cursor_first_page(self, session):
        """Scenario: No cursor returns first page of campaign results."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign, job = self._build_campaign_chain(session, 10)

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id, cursor=None, page_size=3)

        assert len(result.results) == 3
        assert result.total == 10

    def test_campaign_cursor_next_page(self, session):
        """Scenario: Cursor returns page 2 of campaign results."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign, job = self._build_campaign_chain(session, 10)

        service = CampaignQueryService(session)
        page1 = service.get_campaign_results(campaign.id, cursor=None, page_size=3)
        cursor = page1.results[-1].ocr_result_id
        page2 = service.get_campaign_results(campaign.id, cursor=cursor, page_size=3)

        assert len(page2.results) == 3
        assert all(r.ocr_result_id > cursor for r in page2.results)

    def test_campaign_next_cursor_field(self, session):
        """Scenario: Campaign response includes next_cursor."""
        from app.services.campaign_query_service import CampaignQueryService

        region, campaign, job = self._build_campaign_chain(session, 10)

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id, cursor=None, page_size=3)

        assert result.next_cursor is not None
        assert result.next_cursor == result.results[-1].ocr_result_id


class TestAdversarialFindings:
    """Tests from adversarial review (#61) — edge cases and validation gaps.

    RED phase: These tests expose bugs found during adversarial review.
    """

    def test_negative_cursor_rejected(self, session):
        """Scenario: Negative cursor raises ValueError instead of returning page 1."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 5)

        service = ResultsQueryService(session)
        with pytest.raises(ValueError, match="cursor must be non-negative"):
            service.get_results(job.id, cursor=-1, page_size=3)

    def test_page_size_above_max_rejected(self, session):
        """Scenario: page_size > 1000 raises ValueError."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 5)

        service = ResultsQueryService(session)
        with pytest.raises(ValueError, match="page_size must be between"):
            service.get_results(job.id, page_size=10000)

    def test_page_size_zero_rejected(self, session):
        """Scenario: page_size=0 raises ValueError."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        service = ResultsQueryService(session)
        with pytest.raises(ValueError, match="page_size must be between"):
            service.get_results(job.id, page_size=0)

    def test_campaign_invalid_confidence_rejected(self, session):
        """Scenario: Invalid confidence string raises ValueError, not silently ignored."""
        from app.services.campaign_query_service import CampaignQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        _build_ocr_chain(session, job, scan, 5)

        service = CampaignQueryService(session)
        with pytest.raises(ValueError, match="Invalid confidence"):
            service.get_campaign_results(campaign.id, confidence="INVALID", page_size=3)

    def test_campaign_uses_latest_job_only(self, session):
        """Scenario: Campaign results reflect only the latest (max ID) job, not all jobs."""
        from app.services.campaign_query_service import CampaignQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan1 = _seed_scan(session, campaign)

        job1 = _seed_job(session, campaign)
        _build_ocr_chain(session, job1, scan1, 3)

        scan2 = PetitionScan(
            campaign_id=campaign.id,
            original_filename="test2.pdf",
            stored_path="/tmp/test2.pdf",
            file_hash="def456",
            page_count=1,
        )
        session.add(scan2)
        session.flush()

        job2 = _seed_job(session, campaign)
        for i in range(5):
            crop = PetitionCrop(
                scan_id=scan2.id,
                crop_index=i,
                stored_path=f"/tmp/scan2_crop_{i}.png",
                crop_coordinates={"top": 0.0, "bottom": 0.1},
                page_number=1,
            )
            session.add(crop)
            session.flush()
            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Scan2 Sig {i}"},
            )
            session.add(ocr)
            session.flush()
            session.add(
                MatchResult(
                    matcher_job_id=job2.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=1,
                    similarity_score=0.85,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = CampaignQueryService(session)
        result = service.get_campaign_results(campaign.id, cursor=None, page_size=50)

        assert result.total == 5
        assert len(result.results) == 5

    def test_next_cursor_with_confidence_filter_no_false_positive(self, session):
        """Scenario: next_cursor is None when filtered results exhausted, even if
        unfiltered results remain."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        for i in range(4):
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
                extracted_text={"name": f"Sig {i}"},
            )
            session.add(ocr)
            session.flush()

            level = ConfidenceLevel.HIGH if i < 2 else ConfidenceLevel.LOW
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=1,
                    similarity_score=0.85,
                    confidence_level=level,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(
            job.id, cursor=None, page_size=10, confidence=ConfidenceLevel.HIGH
        )

        assert result.total == 2
        assert len(result.results) == 2
        assert result.next_cursor is None
