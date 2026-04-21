"""BDD behavioral tests for ResultsQueryService.

Describes expected behaviour of match result querying, pagination,
confidence filtering, prediction building, and CSV export.

Written red-first: each scenario documents a user-facing behaviour
that the service must satisfy.
"""

from uuid import uuid4

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
        id=uuid4(), region_key="DC", region_name="Washington, DC", country_code="US"
    )
    session.add(region)
    session.flush()
    return region


def _seed_campaign(session: Session, region: Region) -> Campaign:
    campaign = Campaign(
        id=uuid4(),
        unique_name=f"test-{uuid4().hex[:8]}",
        title="Test Campaign",
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


def _seed_ocr_result(
    session: Session, crop: PetitionCrop, text: dict | None = None
) -> OcrResult:
    ocr = OcrResult(
        crop_id=crop.id,
        ocr_job_id=1,
        extracted_text=text or {"name": "John Doe"},
    )
    session.add(ocr)
    session.flush()
    return ocr


def _seed_voter(
    session: Session,
    region: Region,
    first_name: str = "John",
    last_name: str = "Doe",
    street: str = "123 Main St",
    city: str = "DC",
) -> RegisteredVoter:
    voter = RegisteredVoter(
        region_id=region.id,
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={"street": street, "city": city, "state": "DC", "zip": "20001"},
        data_hash=f"hash-{first_name}-{last_name}",
    )
    session.add(voter)
    session.flush()
    return voter


def _seed_job(session: Session, campaign: Campaign, job_id: int = 1) -> MatcherJob:
    job = MatcherJob(
        id=job_id,
        campaign_id=campaign.id,
        current_status=JobStatus.MATCHING_COMPLETED,
    )
    session.add(job)
    session.flush()
    return job


def _build_full_stack(session: Session, n_ocr_results: int = 5):
    region = _seed_region(session)
    campaign = _seed_campaign(session, region)
    scan = _seed_scan(session, campaign)
    job = _seed_job(session, campaign)

    crops = []
    ocr_results = []
    for i in range(n_ocr_results):
        crop = _seed_crop(session, scan, index=i)
        crops.append(crop)
        ocr = _seed_ocr_result(
            session, crop, text={"name": f"Signature {i}", "address": f"{i} Main St"}
        )
        ocr_results.append(ocr)

    return region, campaign, scan, job, crops, ocr_results


class TestGetResultsPagination:
    """Feature: Paginated match result retrieval.

    As an API consumer
    I want to retrieve match results for a job with pagination
    So that large result sets are delivered in manageable pages.
    """

    def test_returns_zero_results_for_job_with_no_matches(self, session):
        """Scenario: Job exists but has no match results."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        job = _seed_job(session, campaign)

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        assert result.total == 0
        assert result.results == []
        assert result.page_size == 50

    def test_returns_correct_total_as_unique_ocr_results(self, session):
        """Scenario: Multiple match results per OCR count as one total entry."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        for rank in range(1, 4):
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=rank,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        assert result.total == 1
        assert len(result.results) == 1
        assert len(result.results[0].predictions) == 3

    def test_paginates_results_across_pages(self, session):
        """Scenario: 10 OCR results with page_size=3 yields 4 pages."""
        from app.services.results_query_service import ResultsQueryService

        _region, _campaign, _scan, job, _crops, ocr_results = _build_full_stack(
            session, n_ocr_results=10
        )
        for i, ocr in enumerate(ocr_results):
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

        service = ResultsQueryService(session)

        page1 = service.get_results(job.id, page_size=3)
        page2 = service.get_results(job.id, cursor=page1.next_cursor, page_size=3)
        page4_cursor = page2.next_cursor
        page3 = service.get_results(job.id, cursor=page4_cursor, page_size=3)
        page4 = service.get_results(job.id, cursor=page3.next_cursor, page_size=3)

        assert len(page1.results) == 3
        assert len(page2.results) == 3
        assert len(page4.results) == 1
        assert page1.total == 10
        assert page4.total == 10

    def test_raises_value_error_for_missing_job(self, session):
        """Scenario: Querying a non-existent job raises ValueError."""
        from app.services.results_query_service import ResultsQueryService

        service = ResultsQueryService(session)

        with pytest.raises(ValueError, match="not found"):
            service.get_results(99999)


class TestConfidenceFiltering:
    """Feature: Confidence level filtering.

    As an API consumer
    I want to filter match results by confidence level
    So that I can focus on high-quality matches or investigate low ones.
    """

    def test_filters_to_high_confidence_only(self, session):
        """Scenario: Only HIGH confidence results returned when filtered."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr_high = _seed_ocr_result(session, crop, text={"name": "High Match"})
        crop2 = _seed_crop(session, scan, index=1)
        ocr_low = _seed_ocr_result(session, crop2, text={"name": "Low Match"})

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
        result = service.get_results(job.id, confidence=ConfidenceLevel.HIGH)

        assert result.total == 1
        assert result.results[0].predictions[0].confidence == "HIGH"

    def test_returns_all_confidences_when_no_filter(self, session):
        """Scenario: No confidence filter returns all results."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr_high = _seed_ocr_result(session, crop, text={"name": "High"})
        crop2 = _seed_crop(session, scan, index=1)
        ocr_med = _seed_ocr_result(session, crop2, text={"name": "Medium"})

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
                ocr_result_id=ocr_med.id,
                voter_id=None,
                rank=1,
                similarity_score=0.70,
                confidence_level=ConfidenceLevel.MEDIUM,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        assert result.total == 2

    def test_filter_with_zero_matching_confidence_returns_empty(self, session):
        """Scenario: Filtering for LOW when only HIGH exists yields empty."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop, text={"name": "Only High"})

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.95,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id, confidence=ConfidenceLevel.LOW)

        assert result.total == 0
        assert result.results == []


class TestPredictionBuilding:
    """Feature: Voter prediction construction.

    As the results service
    I want to build voter predictions from match results
    So that each OCR result shows ranked candidate voters.
    """

    def test_prediction_includes_voter_name_and_address(self, session):
        """Scenario: Matched voter data populates name and address."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)
        voter = _seed_voter(session, region)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=voter.id,
                rank=1,
                similarity_score=0.95,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        pred = result.results[0].predictions[0]
        assert "John" in pred.voter_name
        assert "Doe" in pred.voter_name
        assert "123 Main St" in pred.voter_address

    def test_prediction_without_voter_shows_empty_strings(self, session):
        """Scenario: Match result with no voter_id yields empty name/address."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.50,
                confidence_level=ConfidenceLevel.LOW,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        pred = result.results[0].predictions[0]
        assert pred.voter_name == ""
        assert pred.voter_address == ""

    def test_predictions_sorted_by_rank_ascending(self, session):
        """Scenario: Multiple predictions per OCR sorted rank 1 first."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)
        voter1 = _seed_voter(session, region, first_name="Alice", last_name="A")
        voter2 = _seed_voter(session, region, first_name="Bob", last_name="B")
        voter3 = _seed_voter(session, region, first_name="Carol", last_name="C")

        for rank, voter in [(3, voter1), (1, voter2), (2, voter3)]:
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=voter.id,
                    rank=rank,
                    similarity_score=0.9 - rank * 0.1,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        preds = result.results[0].predictions
        assert preds[0].rank == 1
        assert preds[1].rank == 2
        assert preds[2].rank == 3

    def test_limits_predictions_to_five_per_ocr_result(self, session):
        """Scenario: More than 5 matches for one OCR, only top 5 returned."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        for rank in range(1, 8):
            voter = _seed_voter(
                session, region, first_name=f"V{rank}", last_name=f"L{rank}"
            )
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=voter.id,
                    rank=rank,
                    similarity_score=0.9 - rank * 0.05,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        assert len(result.results[0].predictions) == 5


class TestExtractedTextRendering:
    """Feature: Extracted text display in results.

    As an API consumer
    I want OCR extracted text rendered as a readable string
    So that I can display signature text alongside predictions.
    """

    def test_dict_extracted_text_rendered_as_sorted_values(self, session):
        """Scenario: Dict text {"name": "John", "address": "1 St"} → "1 St John"."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(
            session, crop, text={"name": "John Doe", "address": "1 Main St"}
        )

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        text = result.results[0].extracted_text
        assert "John Doe" in text
        assert "1 Main St" in text

    def test_result_includes_crop_id_for_image_lookup(self, session):
        """Scenario: Each result includes the crop_id for fetching the image."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(job.id)

        assert result.results[0].crop_id == crop.id


class TestCsvExport:
    """Feature: CSV export of match results.

    As an API consumer
    I want to export match results as CSV
    So that I can analyze them in a spreadsheet.

    The service returns a (csv_row_generator, filename) tuple.
    HTTP StreamingResponse wrapping lives in the router.
    """

    @staticmethod
    def _collect_csv(generator) -> str:
        return "".join(generator)

    def test_export_returns_iterable_and_filename(self, session):
        """Scenario: Service returns an iterable of CSV lines and a filename string."""
        from collections.abc import Iterable

        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.95,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        result = service.export_results_csv(job.id)

        csv_lines, filename = result
        assert isinstance(csv_lines, Iterable)
        assert isinstance(filename, str)
        assert f"job_{job.id}_results.csv" == filename

    def test_export_produces_csv_with_correct_headers(self, session):
        """Scenario: CSV has standard column headers."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)
        voter = _seed_voter(session, region)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=voter.id,
                rank=1,
                similarity_score=0.95,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        service = ResultsQueryService(session)
        csv_lines, filename = service.export_results_csv(job.id)
        body = self._collect_csv(csv_lines)

        assert f"job_{job.id}_results.csv" == filename
        header_line = body.strip().split("\n")[0]
        for expected in ["Crop ID", "Extracted Text", "Rank", "Confidence"]:
            assert expected in header_line

    def test_export_raises_for_missing_job(self, session):
        """Scenario: Exporting CSV for non-existent job raises ValueError."""
        from app.services.results_query_service import ResultsQueryService

        service = ResultsQueryService(session)

        with pytest.raises(ValueError, match="not found"):
            service.export_results_csv(99999)

    def test_export_respects_confidence_filter(self, session):
        """Scenario: Export with confidence filter only includes matching results."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr_high = _seed_ocr_result(session, crop, text={"name": "High"})
        crop2 = _seed_crop(session, scan, index=1)
        ocr_low = _seed_ocr_result(session, crop2, text={"name": "Low"})

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
        generator, _ = service.export_results_csv(
            job.id, confidence=ConfidenceLevel.HIGH
        )
        body = self._collect_csv(generator)

        lines = [ln for ln in body.strip().split("\n") if ln]
        assert len(lines) == 2
        assert "HIGH" in lines[1]

    def test_export_materializes_match_results_and_batch_fetches_related(self, session):
        """Scenario: Export materializes match results via yield_per, then
        batch-fetches OcrResult and RegisteredVoter — no per-row lookups."""
        from unittest.mock import patch

        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        session.add(
            MatchResult(
                matcher_job_id=job.id,
                ocr_result_id=ocr.id,
                voter_id=None,
                rank=1,
                similarity_score=0.9,
                confidence_level=ConfidenceLevel.HIGH,
            )
        )
        session.commit()

        real_exec = session.exec

        batch_lookups = {"ocr": 0, "voter": 0}
        match_materializations = 0

        def tracking_exec(statement):
            nonlocal match_materializations, batch_lookups
            result = real_exec(statement)
            stmt_str = str(statement)
            if "match_result" in stmt_str.lower():
                match_materializations += 1
            elif "ocr_result" in stmt_str.lower():
                batch_lookups["ocr"] += 1
            elif "registered_voter" in stmt_str.lower():
                batch_lookups["voter"] += 1
            return result

        with patch.object(type(session), "exec", side_effect=tracking_exec):
            service = ResultsQueryService(session)
            csv_lines, _ = service.export_results_csv(job.id)
            list(csv_lines)

        assert match_materializations == 1
        assert batch_lookups["ocr"] == 1
        assert batch_lookups["voter"] == 0

    def test_export_yields_incrementally_not_as_single_blob(self, session):
        """Scenario: CSV output arrives as multiple pieces, not one monolithic string."""
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        for i in range(3):
            crop = _seed_crop(session, scan, index=i)
            ocr = _seed_ocr_result(session, crop, text={"name": f"Sig {i}"})
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=1,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        csv_lines, _ = service.export_results_csv(job.id)

        chunks = list(csv_lines)
        assert len(chunks) > 1

        body = "".join(chunks)
        lines = [ln for ln in body.strip().split("\n") if ln]
        assert lines[0].startswith("Crop ID")
        assert len(lines) == 4

    def test_export_uses_batched_ocr_lookup_not_per_row_get(self, session):
        """Scenario: CSV export batch-fetches OcrResults instead of per-row session.get.

        The export must not call session.get(OcrResult, ...) for each unique
        ocr_result_id. Instead it should bulk-fetch in batches.
        """
        from unittest.mock import patch

        from app.data.database.model.ocr_result import OcrResult
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        ocr_ids = []
        for i in range(5):
            crop = _seed_crop(session, scan, index=i)
            ocr = _seed_ocr_result(session, crop, text={"name": f"Sig {i}"})
            ocr_ids.append(ocr.id)
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=1,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)

        with patch.object(type(session), "get", wraps=session.get) as mock_get:
            generator, _ = service.export_results_csv(job.id)
            list(generator)

            ocr_get_calls = [c for c in mock_get.call_args_list if c[0][0] is OcrResult]
            assert len(ocr_get_calls) == 0, (
                f"Expected no session.get(OcrResult, ...) calls, "
                f"got {len(ocr_get_calls)}"
            )

    def test_export_uses_batched_voter_lookup_not_per_row_get(self, session):
        """Scenario: CSV export batch-fetches RegisteredVoters instead of per-row session.get.

        The export must not call session.get(RegisteredVoter, ...) for each
        unique voter_id. Instead it should bulk-fetch in batches.
        """
        from unittest.mock import patch

        from app.data.database.model.registered_voter import RegisteredVoter
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)
        crop = _seed_crop(session, scan)
        ocr = _seed_ocr_result(session, crop)

        voters = [_seed_voter(session, region, first_name=f"V{i}") for i in range(5)]
        for i, voter in enumerate(voters):
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=voter.id,
                    rank=i + 1,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)

        with patch.object(type(session), "get", wraps=session.get) as mock_get:
            generator, _ = service.export_results_csv(job.id)
            list(generator)

            voter_get_calls = [
                c for c in mock_get.call_args_list if c[0][0] is RegisteredVoter
            ]
            assert len(voter_get_calls) == 0, (
                f"Expected no session.get(RegisteredVoter, ...) calls, "
                f"got {len(voter_get_calls)}"
            )

    def test_batched_export_produces_correct_output(self, session):
        """Scenario: Batched lookup refactor preserves CSV content correctness.

        Multiple match results with different OCR results and voters must
        produce identical CSV output to the per-row version.
        """
        from app.services.results_query_service import ResultsQueryService

        region = _seed_region(session)
        campaign = _seed_campaign(session, region)
        scan = _seed_scan(session, campaign)
        job = _seed_job(session, campaign)

        for i in range(3):
            crop = _seed_crop(session, scan, index=i)
            ocr = _seed_ocr_result(session, crop, text={"name": f"Sig {i}"})
            voter = _seed_voter(session, region, first_name=f"V{i}")
            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=voter.id,
                    rank=1,
                    similarity_score=0.9,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )
        session.commit()

        service = ResultsQueryService(session)
        generator, _ = service.export_results_csv(job.id)
        body = self._collect_csv(generator)

        lines = [ln for ln in body.strip().split("\n") if ln]
        assert len(lines) == 4
        assert lines[0].startswith("Crop ID")
        for line in lines[1:]:
            assert "HIGH" in line
