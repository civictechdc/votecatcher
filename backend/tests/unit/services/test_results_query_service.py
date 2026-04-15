"""Unit tests for ResultsQueryService."""

import uuid

from sqlmodel import Session

from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.registered_voter import RegisteredVoter


class TestResultsQueryService:
    """Tests for ResultsQueryService."""

    def test_build_predictions_from_match_results_empty(self, session: Session):
        """Test building predictions with no match results."""
        from app.services.results_query_service import ResultsQueryService

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results([])

        assert predictions == {}

    def test_build_predictions_from_match_results_with_voter(self, session: Session):
        """Test building predictions with voter data."""
        from app.services.results_query_service import ResultsQueryService

        voter = RegisteredVoter(
            id=1,
            region_id=uuid.uuid4(),
            name_data={"first_name": "John", "last_name": "Doe"},
            address_data={
                "street": "123 Main St",
                "city": "DC",
                "state": "DC",
                "zip": "20001",
            },
            data_hash="hash1",
        )
        session.add(voter)

        match_result = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=1,
            rank=1,
            similarity_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        session.add(match_result)
        session.commit()

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results([match_result])

        assert 10 in predictions
        assert len(predictions[10]) == 1
        pred = predictions[10][0]
        assert pred.rank == 1
        assert pred.voter_name == "John Doe"
        assert pred.voter_address == "123 Main St, DC, DC, 20001"
        assert pred.similarity_score == 0.95
        assert pred.confidence == "HIGH"

    def test_build_predictions_from_match_results_no_voter(self, session: Session):
        """Test building predictions without voter data."""
        from app.services.results_query_service import ResultsQueryService

        match_result = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=None,
            rank=1,
            similarity_score=0.75,
            confidence_level=ConfidenceLevel.MEDIUM,
        )
        session.add(match_result)
        session.commit()

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results([match_result])

        assert 10 in predictions
        assert len(predictions[10]) == 1
        pred = predictions[10][0]
        assert pred.rank == 1
        assert pred.voter_name == ""
        assert pred.voter_address == ""
        assert pred.similarity_score == 0.75
        assert pred.confidence == "MEDIUM"

    def test_build_predictions_sorts_by_rank(self, session: Session):
        """Test that predictions are sorted by rank."""
        from app.services.results_query_service import ResultsQueryService

        voter = RegisteredVoter(
            id=1,
            region_id=uuid.uuid4(),
            name_data={"first_name": "Jane", "last_name": "Smith"},
            address_data={},
            data_hash="hash1",
        )
        session.add(voter)

        match_result1 = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=1,
            rank=3,
            similarity_score=0.85,
            confidence_level=ConfidenceLevel.MEDIUM,
        )
        match_result2 = MatchResult(
            id=2,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=1,
            rank=1,
            similarity_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        match_result3 = MatchResult(
            id=3,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=1,
            rank=2,
            similarity_score=0.90,
            confidence_level=ConfidenceLevel.HIGH,
        )
        session.add_all([match_result1, match_result2, match_result3])
        session.commit()

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results(
            [match_result1, match_result2, match_result3]
        )

        assert 10 in predictions
        assert len(predictions[10]) == 3
        assert predictions[10][0].rank == 1
        assert predictions[10][1].rank == 2
        assert predictions[10][2].rank == 3

    def test_build_predictions_groups_by_ocr_result(self, session: Session):
        """Test that predictions are grouped by OCR result ID."""
        from app.services.results_query_service import ResultsQueryService

        voter1 = RegisteredVoter(
            id=1,
            region_id=uuid.uuid4(),
            name_data={"first_name": "John", "last_name": "Doe"},
            address_data={},
            data_hash="hash1",
        )
        voter2 = RegisteredVoter(
            id=2,
            region_id=uuid.uuid4(),
            name_data={"first_name": "Jane", "last_name": "Smith"},
            address_data={},
            data_hash="hash2",
        )
        session.add_all([voter1, voter2])

        match_result1 = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=1,
            rank=1,
            similarity_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        match_result2 = MatchResult(
            id=2,
            matcher_job_id=1,
            ocr_result_id=20,
            voter_id=2,
            rank=1,
            similarity_score=0.92,
            confidence_level=ConfidenceLevel.HIGH,
        )
        session.add_all([match_result1, match_result2])
        session.commit()

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results(
            [match_result1, match_result2]
        )

        assert 10 in predictions
        assert 20 in predictions
        assert len(predictions[10]) == 1
        assert len(predictions[20]) == 1
        assert predictions[10][0].voter_name == "John Doe"
        assert predictions[20][0].voter_name == "Jane Smith"

    def test_build_predictions_handles_low_confidence_default(self, session: Session):
        """Test that LOW confidence level is handled correctly."""
        from app.services.results_query_service import ResultsQueryService

        match_result = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=10,
            voter_id=None,
            rank=1,
            similarity_score=0.50,
            confidence_level=ConfidenceLevel.LOW,
        )
        session.add(match_result)
        session.commit()

        service = ResultsQueryService(session)
        predictions = service._build_predictions_from_match_results([match_result])

        assert predictions[10][0].confidence == "LOW"

    def test_get_results_empty(self, session: Session):
        """Test getting results with no data."""
        from app.data.database.model.jobs import MatcherJob, JobStatus
        from app.services.results_query_service import ResultsQueryService

        job = MatcherJob(
            id=1,
            campaign_id=uuid.uuid4(),
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(1)

        assert result.total == 0
        assert result.results == []
        assert result.page == 1
        assert result.page_size == 50

    def test_get_results_with_data(self, session: Session):
        """Test getting results with match results."""
        from app.data.database.model.jobs import MatcherJob, JobStatus
        from app.data.database.model.match_result import ConfidenceLevel, MatchResult
        from app.data.database.model.ocr_result import OcrResult
        from app.data.database.model.petition_crop import PetitionCrop
        from app.data.database.model.petition_scan import PetitionScan
        from app.data.database.model.schema import Campaign, Region
        from app.services.results_query_service import ResultsQueryService

        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        session.add(region)

        campaign = Campaign(
            unique_name="dc-2024",
            title="DC 2024",
            year="2024",
            region_id=region.id,
        )
        session.add(campaign)

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
            id=1,
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)

        voter = RegisteredVoter(
            id=1,
            region_id=region.id,
            name_data={"first_name": "John", "last_name": "Doe"},
            address_data={
                "street": "123 Main St",
                "city": "DC",
                "state": "DC",
                "zip": "20001",
            },
            data_hash="hash1",
        )
        session.add(voter)

        ocr_result = OcrResult(
            crop_id=crop.id,
            ocr_job_id=1,
            extracted_text={"name": "John Doe", "address": "123 Main St"},
        )
        session.add(ocr_result)
        session.flush()

        match_result = MatchResult(
            id=1,
            matcher_job_id=1,
            ocr_result_id=ocr_result.id,
            voter_id=1,
            rank=1,
            similarity_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )
        session.add(match_result)
        session.commit()

        service = ResultsQueryService(session)
        result = service.get_results(1)

        assert result.total == 1
        assert len(result.results) == 1
        assert result.results[0].ocr_result_id == ocr_result.id
        assert result.results[0].crop_id == crop.id
        assert "John Doe" in result.results[0].extracted_text
        assert len(result.results[0].predictions) == 1
        assert result.results[0].predictions[0].voter_name == "John Doe"

    def test_get_results_pagination(self, session: Session):
        """Test pagination of results."""
        from app.data.database.model.jobs import MatcherJob, JobStatus
        from app.data.database.model.match_result import ConfidenceLevel, MatchResult
        from app.data.database.model.ocr_result import OcrResult
        from app.data.database.model.petition_crop import PetitionCrop
        from app.data.database.model.petition_scan import PetitionScan
        from app.data.database.model.schema import Campaign, Region
        from app.services.results_query_service import ResultsQueryService

        region = Region(
            region_key="DC",
            region_name="Washington, DC",
            country_code="US",
        )
        session.add(region)

        campaign = Campaign(
            unique_name="dc-2024",
            title="DC 2024",
            year="2024",
            region_id=region.id,
        )
        session.add(campaign)

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="test.pdf",
            stored_path="/tmp/test.pdf",
            file_hash="abc123",
            page_count=10,
        )
        session.add(scan)
        session.flush()

        crops = []
        ocr_results = []
        match_results = []

        for i in range(10):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/crop_{i}.png",
                crop_coordinates={"top": 0.0, "bottom": 0.1},
                page_number=1,
            )
            session.add(crop)
            crops.append(crop)

        session.flush()

        for i, crop in enumerate(crops):
            ocr_result = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Name {i}"},
            )
            session.add(ocr_result)
            ocr_results.append(ocr_result)

        session.flush()

        for i, ocr_result in enumerate(ocr_results):
            match_result = MatchResult(
                id=i + 1,
                matcher_job_id=1,
                ocr_result_id=ocr_result.id,
                voter_id=None,
                rank=1,
                similarity_score=0.90,
                confidence_level=ConfidenceLevel.HIGH,
            )
            session.add(match_result)
            match_results.append(match_result)

        job = MatcherJob(
            id=1,
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        session.add(job)
        session.commit()

        service = ResultsQueryService(session)

        page1 = service.get_results(1, page=1, page_size=3)
        assert page1.total == 10
        assert len(page1.results) == 3

        page2 = service.get_results(1, page=2, page_size=3)
        assert page2.total == 10
        assert len(page2.results) == 3

        page3 = service.get_results(1, page=3, page_size=3)
        assert page3.total == 10
        assert len(page3.results) == 3

        page4 = service.get_results(1, page=4, page_size=3)
        assert page4.total == 10
        assert len(page4.results) == 1
