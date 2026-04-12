"""Tests for OCR multi-entry storage (BUG-14 fix).

Each petition crop may contain up to 5 signatures. The OCR result
should store all 5 entries with an ocr_index (0-4) to identify each.

Previously, a UNIQUE constraint on crop_id prevented storing multiple
entries per crop. This test suite verifies the fix.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region
from app.data.database.model.user import User


class TestOcrMultiEntryStorage:
    """Tests for storing multiple OCR entries per crop."""

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
        """Create a single petition crop."""
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
            current_status=JobStatus.NOT_STARTED,
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
            status=JobStatus.OCR_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_ocr_result_has_ocr_index_column(
        self, session, sample_crop, sample_ocr_job
    ):
        """OcrResult should have ocr_index column for multi-entry support."""
        result = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            ocr_index=0,
            extracted_text={"name": "John Doe", "address": "123 Main St"},
            confidence_score=0.95,
        )
        session.add(result)
        session.commit()
        session.refresh(result)

        assert result.ocr_index == 0

    def test_can_store_multiple_ocr_entries_per_crop(
        self, session, sample_crop, sample_ocr_job
    ):
        """Should store multiple OCR results for same crop with different indices."""
        entries = [
            {"name": "John Doe", "address": "123 Main St"},
            {"name": "Jane Smith", "address": "456 Oak Ave"},
            {"name": "Bob Wilson", "address": "789 Pine Rd"},
            {"name": "Alice Brown", "address": "321 Elm St"},
            {"name": "Charlie Davis", "address": "654 Maple Dr"},
        ]

        for idx, entry in enumerate(entries):
            result = OcrResult(
                crop_id=sample_crop.id,
                ocr_job_id=sample_ocr_job.id,
                ocr_index=idx,
                extracted_text=entry,
                confidence_score=0.85,
            )
            session.add(result)

        session.commit()

        stored_results = session.exec(
            select(OcrResult)
            .where(OcrResult.crop_id == sample_crop.id)
            .order_by(OcrResult.ocr_index)
        ).all()

        assert len(stored_results) == 5
        for idx, result in enumerate(stored_results):
            assert result.ocr_index == idx
            assert result.extracted_text["name"] == entries[idx]["name"]

    def test_unique_constraint_removed_from_crop_id(
        self, session, sample_crop, sample_ocr_job
    ):
        """crop_id should no longer have a UNIQUE constraint."""
        result1 = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            ocr_index=0,
            extracted_text={"name": "First Entry"},
        )
        result2 = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            ocr_index=1,
            extracted_text={"name": "Second Entry"},
        )
        session.add(result1)
        session.add(result2)

        session.commit()

        assert result1.id is not None
        assert result2.id is not None
        assert result1.id != result2.id

    def test_ocr_results_ordered_by_index(self, session, sample_crop, sample_ocr_job):
        """OCR results should be queryable in index order."""
        for idx in [2, 0, 4, 1, 3]:
            result = OcrResult(
                crop_id=sample_crop.id,
                ocr_job_id=sample_ocr_job.id,
                ocr_index=idx,
                extracted_text={"name": f"Entry {idx}"},
            )
            session.add(result)
        session.commit()

        results = session.exec(
            select(OcrResult)
            .where(OcrResult.crop_id == sample_crop.id)
            .order_by(OcrResult.ocr_index)
        ).all()

        assert [r.ocr_index for r in results] == [0, 1, 2, 3, 4]

    def test_ocr_index_defaults_to_zero(self, session, sample_crop, sample_ocr_job):
        """ocr_index should default to 0 for backward compatibility."""
        result = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            extracted_text={"name": "Default Index"},
        )
        session.add(result)
        session.commit()
        session.refresh(result)

        assert result.ocr_index == 0


class TestOcrResultBackwardCompatibility:
    """Tests for backward compatibility after schema change."""

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
        user = User(email="test@example.com", name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def sample_campaign(self, session, sample_region):
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
    def sample_crop(self, session, sample_petition_scan):
        crop = PetitionCrop(
            scan_id=sample_petition_scan.id,
            crop_index=0,
            stored_path="/tmp/crop_0.png",
            crop_coordinates={"top": 0.0, "bottom": 0.5},
            page_number=1,
        )
        session.add(crop)
        session.commit()
        session.refresh(crop)
        return crop

    @pytest.fixture
    def sample_matcher_job(self, session, sample_campaign):
        job = MatcherJob(
            campaign_id=sample_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @pytest.fixture
    def sample_ocr_job(self, session, sample_matcher_job):
        job = OcrJob(
            matcher_job_id=sample_matcher_job.id,
            status=JobStatus.OCR_COMPLETED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    def test_existing_code_without_ocr_index_still_works(
        self, session, sample_crop, sample_ocr_job
    ):
        """Code that doesn't specify ocr_index should still work."""
        result = OcrResult(
            crop_id=sample_crop.id,
            ocr_job_id=sample_ocr_job.id,
            extracted_text={"name": "Legacy Entry"},
        )
        session.add(result)
        session.commit()

        assert result.id is not None
        assert result.ocr_index == 0
