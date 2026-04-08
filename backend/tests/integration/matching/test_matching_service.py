"""Integration tests for Matching service.

Tests cover matching service integration with database for voter
pre-filtering, fuzzy matching, and result storage.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.user import User
from app.matching.matching_service import MatchingService


class TestMatchingServiceIntegration:
    """Integration tests for MatchingService with database."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        yield engine
        engine.dispose()

    @pytest.fixture
    def session(self, engine):
        """Create database session for each test."""
        with Session(engine) as session:
            yield session

    @pytest.fixture
    def sample_region(self, session):
        """Create a sample region for testing."""
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
    def sample_user(self, session):
        """Create a sample user for testing."""
        user = User(
            email="test@example.com",
            name="Test User",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def sample_campaign(self, session, sample_region):
        """Create a sample campaign for testing."""
        campaign = Campaign(
            unique_name="dc-2024",
            title="DC 2024",
            description="Test campaign",
            year="2024",
            region_id=sample_region.id,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
        return campaign

    @pytest.fixture
    def sample_petition_scan(self, session, sample_campaign, sample_user):
        """Create a sample petition scan."""
        scan = PetitionScan(
            campaign_id=sample_campaign.id,
            original_filename="test_petition.pdf",
            stored_path="/tmp/test_petition.pdf",
            file_hash="abc123",
            page_count=1,
            uploaded_by=sample_user.id,
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)
        return scan

    @pytest.fixture
    def sample_crop(self, session, sample_petition_scan, temp_storage_dir):
        """Create a sample petition crop."""
        crop_path = temp_storage_dir / "crop_0.png"
        crop_path.write_bytes(b"fake_image_data")

        crop = PetitionCrop(
            scan_id=sample_petition_scan.id,
            crop_index=0,
            stored_path=str(crop_path),
            crop_coordinates={"top": 0.0, "bottom": 0.5},
            page_number=1,
        )
        session.add(crop)
        session.commit()
        session.refresh(crop)
        return crop

    @pytest.fixture
    def sample_matcher_job(self, session, sample_campaign):
        """Create a sample matcher job."""
        job = MatcherJob(
            campaign_id=sample_campaign.id,
            current_status=JobStatus.OCR_COMPLETED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @pytest.fixture
    def sample_ocr_job(self, session, sample_matcher_job):
        """Create a sample OCR job."""
        job = OcrJob(
            matcher_job_id=sample_matcher_job.id,
            provider_job_id="test-job-123",
            status=JobStatus.OCR_COMPLETED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @pytest.fixture
    def sample_ocr_result(self, session, sample_crop, sample_ocr_job):
        """Create a sample OCR result."""
        result = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            extracted_text={"name": "John Smith", "address": "123 Main St"},
            confidence_score=0.95,
        )
        session.add(result)
        session.commit()
        session.refresh(result)
        return result

    @pytest.fixture
    def sample_voters(self, session, sample_region):
        """Create sample registered voters."""
        voters = [
            RegisteredVoter(
                region_id=sample_region.id,
                name_data={
                    "first_name": "John",
                    "last_name": "Smith",
                },
                address_data={
                    "street_number": "123",
                    "street_name": "Main St",
                    "city": "Washington",
                    "state": "DC",
                    "zip": "20001",
                },
            ),
            RegisteredVoter(
                region_id=sample_region.id,
                name_data={
                    "first_name": "Jane",
                    "last_name": "Doe",
                },
                address_data={
                    "street_number": "456",
                    "street_name": "Oak Ave",
                    "city": "Washington",
                    "state": "DC",
                    "zip": "20002",
                },
            ),
            RegisteredVoter(
                region_id=sample_region.id,
                name_data={
                    "first_name": "Bob",
                    "last_name": "Johnson",
                },
                address_data={
                    "street_number": "789",
                    "street_name": "Pine Rd",
                    "city": "Washington",
                    "state": "DC",
                    "zip": "20003",
                },
            ),
        ]
        for voter in voters:
            session.add(voter)
        session.commit()
        for voter in voters:
            session.refresh(voter)
        return voters

    def test_pre_filter_voters_by_region(self, session, sample_region, sample_voters):
        """Should filter voters by region ID."""
        service = MatchingService(session=session)

        voters = service.pre_filter_voters(region_id=sample_region.id)

        assert len(voters) == 3

    def test_extract_name_and_address_from_ocr(self, session):
        """Should extract name and address from OCR text."""
        service = MatchingService(session=session)

        name, address = service.extract_name_and_address(
            {"name": "John Smith", "address": "123 Main St"}
        )

        assert name == "John Smith"
        assert address == "123 Main St"

    def test_calculate_similarity_scores(self, session):
        """Should calculate similarity scores correctly."""
        service = MatchingService(session=session)

        score = service.calculate_similarity(
            ocr_name="John Smith",
            ocr_address="123 Main St",
            voter_name="John Smith",
            voter_address="123 Main St",
        )

        assert score >= 0.95

    def test_assign_confidence_levels(self, session):
        """Should assign correct confidence levels."""
        service = MatchingService(session=session)

        assert service.assign_confidence(0.95) == ConfidenceLevel.HIGH
        assert service.assign_confidence(0.75) == ConfidenceLevel.MEDIUM
        assert service.assign_confidence(0.45) == ConfidenceLevel.LOW

    def test_match_ocr_result_returns_top_predictions(
        self, session, sample_region, sample_voters
    ):
        """Should return top predictions for OCR result."""
        service = MatchingService(session=session)

        predictions = service.match_ocr_result(
            ocr_text={"name": "John Smith", "address": "123 Main St"},
            region_id=sample_region.id,
            top_n=3,
        )

        assert len(predictions) <= 3
        if predictions:
            assert (
                predictions[0]["similarity_score"]
                >= predictions[-1]["similarity_score"]
            )

    def test_store_match_results_persists_to_db(
        self, session, sample_ocr_result, sample_matcher_job, sample_region
    ):
        """Should store match results in database."""
        service = MatchingService(session=session)

        matches = [
            {
                "voter_id": 1,
                "similarity_score": 0.95,
                "confidence_level": ConfidenceLevel.HIGH,
                "field_scores": {
                    "name": 0.98,
                    "address": 0.92,
                },
            }
        ]

        service.store_match_results(
            ocr_result_id=sample_ocr_result.id,
            matcher_job_id=sample_matcher_job.id,
            matches=matches,
        )

        db_results = session.exec(
            select(MatchResult).where(MatchResult.ocr_result_id == sample_ocr_result.id)
        ).all()
        assert len(db_results) == 1
        assert db_results[0].confidence_level == ConfidenceLevel.HIGH


class TestMatchingServiceEdgeCases:
    """Tests for matching service edge cases."""

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        yield engine
        engine.dispose()

    @pytest.fixture
    def session(self, engine):
        """Create database session for each test."""
        with Session(engine) as session:
            yield session

    def test_extract_from_empty_ocr_text(self, session):
        """Should handle empty OCR text gracefully."""
        service = MatchingService(session=session)

        name, address = service.extract_name_and_address({})

        assert name == ""
        assert address == ""

    def test_calculate_similarity_with_empty_strings(self, session):
        """Should return 0 for empty OCR input."""
        service = MatchingService(session=session)

        score = service.calculate_similarity(
            ocr_name="",
            ocr_address="",
            voter_name="John Smith",
            voter_address="123 Main St",
        )

        assert score == 0.0

    def test_match_with_no_matching_voters(self, session):
        """Should return empty list when no voters match."""
        service = MatchingService(session=session)

        predictions = service.match_ocr_result(
            ocr_text={"name": "Nonexistent Person", "address": "999 Nowhere St"},
            region_id=999,
            top_n=5,
        )

        assert predictions == []
