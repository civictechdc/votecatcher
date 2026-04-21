"""BDD tests for shared results helpers module.

RED phase: Tests reference app.services.results_shared which does not exist yet.
All tests must FAIL until the shared module is created.
"""

import uuid

import pytest
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region


def _seed_region(session: Session) -> Region:
    region = Region(
        region_key="DC", region_name="Washington, DC", country_code="US"
    )
    session.add(region)
    session.flush()
    return region


def _seed_campaign(session: Session, region: Region) -> Campaign:
    campaign = Campaign(
        unique_name=f"shared-test-{uuid.uuid4().hex[:8]}",
        title="Shared Test",
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


def _seed_crop(session: Session, scan: PetitionScan, index: int = 0) -> PetitionCrop:
    crop = PetitionCrop(
        scan_id=scan.id,
        crop_index=index,
        stored_path=f"/tmp/crop_{index}.png",
        crop_coordinates={"top": 0.0, "bottom": 0.1},
        page_number=1,
    )
    session.add(crop)
    session.flush()
    return crop


def _seed_job(session: Session, campaign: Campaign) -> MatcherJob:
    job = MatcherJob(
        campaign_id=campaign.id,
        current_status=JobStatus.MATCHING_COMPLETED,
    )
    session.add(job)
    session.flush()
    return job


class TestValidatePaginationParams:
    """Feature: Pagination parameter validation.

    As the results service
    I want shared validation for cursor and page_size
    So that both job and campaign endpoints enforce the same constraints.
    """

    def test_negative_cursor_raises(self):
        """Scenario: Negative cursor raises ValueError."""
        from app.services.results_shared import validate_pagination_params

        with pytest.raises(ValueError, match="cursor must be non-negative"):
            validate_pagination_params(cursor=-1, page_size=50)

    def test_page_size_zero_raises(self):
        """Scenario: page_size=0 raises ValueError."""
        from app.services.results_shared import validate_pagination_params

        with pytest.raises(ValueError, match="page_size must be between"):
            validate_pagination_params(cursor=None, page_size=0)

    def test_page_size_above_max_raises(self):
        """Scenario: page_size > 1000 raises ValueError."""
        from app.services.results_shared import validate_pagination_params

        with pytest.raises(ValueError, match="page_size must be between"):
            validate_pagination_params(cursor=None, page_size=10001)

    def test_valid_params_pass(self):
        """Scenario: Valid cursor and page_size do not raise."""
        from app.services.results_shared import validate_pagination_params

        validate_pagination_params(cursor=None, page_size=50)
        validate_pagination_params(cursor=100, page_size=1)
        validate_pagination_params(cursor=0, page_size=1000)


class TestBuildPredictions:
    """Feature: Shared prediction building.

    As both query services
    I want a single function to build predictions from match results
    So that prediction construction is identical across endpoints.
    """

    def test_empty_match_results_returns_empty(self, session: Session):
        """Scenario: No match results yields empty dict."""
        from app.services.results_shared import build_predictions

        result = build_predictions(session, [])

        assert result == {}

    def test_predictions_with_voter_data(self, session: Session):
        """Scenario: Match result with voter builds named prediction."""
        from app.services.results_shared import build_predictions

        region = _seed_region(session)
        voter = RegisteredVoter(
            region_id=region.id,
            name_data={"first_name": "Alice", "last_name": "Smith"},
            address_data={"street": "1 Oak St", "city": "DC", "state": "DC", "zip": "20001"},
            data_hash="h1",
        )
        session.add(voter)
        session.flush()

        match = MatchResult(
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=voter.id,
            rank=1,
            similarity_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        session.add(match)
        session.commit()

        result = build_predictions(session, [match])

        assert 10 in result
        assert len(result[10]) == 1
        assert result[10][0].rank == 1
        assert result[10][0].voter_name == "Alice Smith"
        assert result[10][0].confidence == ConfidenceLevel.HIGH

    def test_predictions_without_voter(self, session: Session):
        """Scenario: Match result with no voter_id yields empty name/address."""
        from app.services.results_shared import build_predictions

        match = MatchResult(
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=None,
            rank=1,
            similarity_score=0.5,
            confidence_level=ConfidenceLevel.LOW,
        )
        session.add(match)
        session.commit()

        result = build_predictions(session, [match])

        assert result[10][0].voter_name == ""
        assert result[10][0].voter_address == ""

    def test_predictions_sorted_by_rank(self, session: Session):
        """Scenario: Multiple predictions per OCR sorted by rank ascending."""
        from app.services.results_shared import build_predictions

        region = _seed_region(session)
        voter = RegisteredVoter(
            region_id=region.id,
            name_data={"first_name": "A", "last_name": "B"},
            address_data={},
            data_hash="h1",
        )
        session.add(voter)
        session.flush()

        for rank in [3, 1, 2]:
            session.add(
                MatchResult(
                    matcher_job_id=1,
                    ocr_result_id=10,
                    voter_id=voter.id,
                    rank=rank,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        matches = session.exec(
            __import__("sqlmodel", fromlist=["select"]).select(MatchResult)
        ).all()
        result = build_predictions(session, matches)

        assert [p.rank for p in result[10]] == [1, 2, 3]


class TestEnrichWithCropScan:
    """Feature: Crop/scan enrichment.

    As both query services
    I want shared crop/scan lookup and enrichment
    So that OCR results get the same thumbnail/coordinate/scan data.
    """

    def test_enriches_ocr_results_with_crop_and_scan(self, session: Session):
        """Scenario: OCR results linked to crops and scans get enrichment data."""
        from app.services.results_shared import enrich_ocr_lookup

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = OcrResult(
            crop_id=crop.id,
            ocr_job_id=1,
            extracted_text={"name": "Test"},
        )
        session.add(ocr)
        session.flush()

        result = enrich_ocr_lookup(session, [ocr.id])

        assert ocr.id in result
        info = result[ocr.id]
        assert info.crop_id == crop.id
        assert info.thumbnail_url == f"/api/crops/{crop.id}/image"
        assert info.page_number == 1
        assert info.document_name == "test.pdf"

    def test_enriches_with_orphan_crop_id(self, session: Session):
        """Scenario: OCR result with crop_id=0 (no matching crop) gets defaults."""
        from app.services.results_shared import enrich_ocr_lookup

        _seed_region(session)
        ocr = OcrResult(
            crop_id=0,
            ocr_job_id=1,
            extracted_text={"name": "Orphan"},
        )
        session.add(ocr)
        session.flush()

        result = enrich_ocr_lookup(session, [ocr.id])

        info = result[ocr.id]
        assert info.crop_id == 0
        assert info.thumbnail_url == ""
        assert info.document_name == ""


class TestComputeNextCursor:
    """Feature: Next cursor computation.

    As both query services
    I want a shared function to determine if next_cursor should be set
    So that pagination termination is consistent across endpoints.
    """

    def test_returns_none_when_fewer_than_page_size(self):
        """Scenario: 3 results with page_size=5 yields no next cursor."""
        from app.services.results_shared import compute_next_cursor

        result = compute_next_cursor(
            paginated_ids=[1, 2, 3], page_size=5, count_after=0
        )
        assert result is None

    def test_returns_last_id_when_more_results_exist(self):
        """Scenario: 5 results with page_size=5 and more remaining yields cursor."""
        from app.services.results_shared import compute_next_cursor

        result = compute_next_cursor(
            paginated_ids=[10, 20, 30, 40, 50], page_size=5, count_after=3
        )
        assert result == 50

    def test_returns_none_when_no_more_results(self):
        """Scenario: 5 results with page_size=5 but nothing after yields None."""
        from app.services.results_shared import compute_next_cursor

        result = compute_next_cursor(
            paginated_ids=[10, 20, 30, 40, 50], page_size=5, count_after=0
        )
        assert result is None
