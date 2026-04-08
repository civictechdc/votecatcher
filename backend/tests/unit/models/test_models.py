"""Unit tests for SQLModel database models."""

from datetime import datetime
from uuid import uuid4

from app.data.database.model.jobs import (
    JobStatus,
    MatcherJob,
    OcrJob,
    OcrModel,
    OcrProvider,
)
from app.data.database.model.match_result import (
    ConfidenceLevel,
    MatchResult,
)
from app.data.database.model.ocr_result import (
    OcrResult,
)
from app.data.database.model.petition_crop import (
    PetitionCrop,
    PetitionCropCreate,
)
from app.data.database.model.petition_scan import (
    PetitionScan,
    PetitionScanCreate,
    PetitionScanRead,
)
from app.data.database.model.session import (
    Session,
    SessionType,
)
from app.data.database.model.user import User


class TestUserModel:
    """Tests for User model."""

    def test_user_instantiation(self):
        """Test basic User instantiation."""
        user = User(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert isinstance(user.created_at, datetime)
        assert user.id is None


class TestPetitionScanModel:
    """Tests for PetitionScan model."""

    def test_petition_scan_instantiation(self):
        """Test basic PetitionScan instantiation."""
        campaign_id = uuid4()
        scan = PetitionScan(
            campaign_id=campaign_id,
            original_filename="petition.pdf",
            stored_path="/uploads/petitions/petition.pdf",
            file_hash="abc123",
            page_count=5,
        )
        assert scan.campaign_id == campaign_id
        assert scan.original_filename == "petition.pdf"
        assert scan.stored_path == "/uploads/petitions/petition.pdf"
        assert scan.file_hash == "abc123"
        assert scan.page_count == 5
        assert isinstance(scan.uploaded_at, datetime)
        assert scan.id is None

    def test_petition_scan_create_schema(self):
        """Test PetitionScanCreate schema."""
        campaign_id = uuid4()
        create_data = PetitionScanCreate(
            campaign_id=campaign_id,
            original_filename="petition.pdf",
            stored_path="/uploads/petitions/petition.pdf",
            file_hash="abc123",
            page_count=5,
        )
        assert create_data.campaign_id == campaign_id
        assert create_data.original_filename == "petition.pdf"

    def test_petition_scan_read_schema(self):
        """Test PetitionScanRead schema."""
        campaign_id = uuid4()
        now = datetime.now()
        read_data = PetitionScanRead(
            id=1,
            campaign_id=campaign_id,
            original_filename="petition.pdf",
            stored_path="/uploads/petitions/petition.pdf",
            file_hash="abc123",
            page_count=5,
            uploaded_at=now,
            uploaded_by=None,
        )
        assert read_data.id == 1
        assert read_data.campaign_id == campaign_id


class TestPetitionCropModel:
    """Tests for PetitionCrop model."""

    def test_petition_crop_instantiation(self):
        """Test basic PetitionCrop instantiation."""
        crop = PetitionCrop(
            scan_id=1,
            crop_index=0,
            stored_path="/uploads/crops/crop_001.jpg",
            crop_coordinates={"x": 0, "y": 0, "width": 100, "height": 50},
            page_number=1,
        )
        assert crop.scan_id == 1
        assert crop.crop_index == 0
        assert crop.stored_path == "/uploads/crops/crop_001.jpg"
        assert crop.crop_coordinates == {"x": 0, "y": 0, "width": 100, "height": 50}
        assert crop.page_number == 1
        assert isinstance(crop.created_at, datetime)
        assert crop.id is None

    def test_petition_crop_create_schema(self):
        """Test PetitionCropCreate schema."""
        create_data = PetitionCropCreate(
            scan_id=1,
            crop_index=0,
            stored_path="/uploads/crops/crop_001.jpg",
            crop_coordinates={"x": 0, "y": 0},
            page_number=1,
        )
        assert create_data.scan_id == 1
        assert create_data.crop_index == 0

    def test_petition_crop_default_coordinates(self):
        """Test default crop_coordinates."""
        crop = PetitionCrop(
            scan_id=1,
            crop_index=0,
            stored_path="/uploads/crops/crop_001.jpg",
            page_number=1,
        )
        assert crop.crop_coordinates == {}


class TestOcrResultModel:
    """Tests for OcrResult model."""

    def test_ocr_result_instantiation(self):
        """Test basic OcrResult instantiation."""
        ocr_result = OcrResult(
            crop_id=1,
            ocr_job_id=1,
            extracted_text={"name": "John Doe", "address": "123 Main St"},
            confidence_score=0.95,
            raw_response={"raw": "data"},
        )
        assert ocr_result.crop_id == 1
        assert ocr_result.ocr_job_id == 1
        assert ocr_result.extracted_text == {
            "name": "John Doe",
            "address": "123 Main St",
        }
        assert ocr_result.confidence_score == 0.95
        assert isinstance(ocr_result.created_at, datetime)
        assert ocr_result.id is None

    def test_ocr_result_optional_fields(self):
        """Test OcrResult with optional fields as None."""
        ocr_result = OcrResult(crop_id=1, ocr_job_id=1)
        assert ocr_result.extracted_text == {}
        assert ocr_result.confidence_score is None
        assert ocr_result.raw_response == {}


class TestMatchResultModel:
    """Tests for MatchResult model."""

    def test_match_result_instantiation(self):
        """Test basic MatchResult instantiation."""
        match = MatchResult(
            ocr_result_id=1,
            matcher_job_id=1,
            rank=1,
            voter_id=100,
            similarity_score=0.92,
            confidence_level=ConfidenceLevel.HIGH,
            field_scores={"name": 0.95, "address": 0.89},
        )
        assert match.ocr_result_id == 1
        assert match.matcher_job_id == 1
        assert match.rank == 1
        assert match.voter_id == 100
        assert match.similarity_score == 0.92
        assert match.confidence_level == ConfidenceLevel.HIGH
        assert isinstance(match.created_at, datetime)
        assert match.id is None

    def test_confidence_level_enum(self):
        """Test ConfidenceLevel enum values."""
        assert ConfidenceLevel.HIGH.value == "HIGH"
        assert ConfidenceLevel.MEDIUM.value == "MEDIUM"
        assert ConfidenceLevel.LOW.value == "LOW"

    def test_match_result_voter_id_optional(self):
        """Test that voter_id can be None (no match)."""
        match = MatchResult(
            ocr_result_id=1,
            matcher_job_id=1,
            rank=1,
            similarity_score=0.0,
            confidence_level=ConfidenceLevel.LOW,
        )
        assert match.voter_id is None


class TestSessionModel:
    """Tests for Session model."""

    def test_session_instantiation(self):
        """Test basic Session instantiation."""
        campaign_id = uuid4()
        session = Session(
            id=1,
            campaign_id=campaign_id,
            name="Test Session",
            session_type=SessionType.REAL,
            snapshot_data={"jobs": [1, 2, 3]},
        )
        assert session.id == 1
        assert session.campaign_id == campaign_id
        assert session.name == "Test Session"
        assert session.session_type == SessionType.REAL
        assert session.snapshot_data == {"jobs": [1, 2, 3]}
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_type_enum(self):
        """Test SessionType enum values."""
        assert SessionType.DEMO.value == "DEMO"
        assert SessionType.REAL.value == "REAL"

    def test_session_campaign_id_optional(self):
        """Test that campaign_id can be None."""
        session = Session(
            id=1,
            name="Test Session",
            session_type=SessionType.DEMO,
        )
        assert session.campaign_id is None


class TestJobsModels:
    """Tests for Job-related models."""

    def test_matcher_job_instantiation(self):
        """Test basic MatcherJob instantiation."""
        campaign_id = uuid4()
        job = MatcherJob(
            id=1,
            campaign_id=campaign_id,
            current_status=JobStatus.NOT_STARTED,
        )
        assert job.id == 1
        assert job.campaign_id == campaign_id
        assert job.current_status == JobStatus.NOT_STARTED
        assert job.started_on is None
        assert job.ended_on is None
        assert isinstance(job.created_at, datetime)

    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        assert JobStatus.NOT_STARTED.value == "NOT_STARTED"
        assert JobStatus.OCR_PENDING.value == "OCR_PENDING"
        assert JobStatus.OCR_STARTED.value == "OCR_STARTED"
        assert JobStatus.OCR_COMPLETED.value == "OCR_COMPLETED"
        assert JobStatus.OCR_FAILED.value == "OCR_FAILED"
        assert JobStatus.MATCHING_PENDING.value == "MATCHING_PENDING"
        assert JobStatus.MATCHING.value == "MATCHING"
        assert JobStatus.MATCHING_COMPLETED.value == "MATCHING_COMPLETED"

    def test_ocr_job_instantiation(self):
        """Test basic OcrJob instantiation."""
        ocr_job = OcrJob(
            id=1,
            matcher_job_id=1,
            status=JobStatus.NOT_STARTED,
        )
        assert ocr_job.id == 1
        assert ocr_job.matcher_job_id == 1
        assert ocr_job.status == JobStatus.NOT_STARTED
        assert ocr_job.provider_job_id is None
        assert ocr_job.ocr_model_id is None
        assert isinstance(ocr_job.created_at, datetime)

    def test_ocr_provider_instantiation(self):
        """Test basic OcrProvider instantiation."""
        provider = OcrProvider(
            id=1,
            unique_name="openai",
            display_name="OpenAI",
        )
        assert provider.id == 1
        assert provider.unique_name == "openai"
        assert provider.display_name == "OpenAI"
        assert isinstance(provider.created_at, datetime)

    def test_ocr_model_instantiation(self):
        """Test basic OcrModel instantiation."""
        model = OcrModel(
            id=1,
            unique_name="gpt-4o",
            display_name="GPT-4o",
            provider_id=1,
        )
        assert model.id == 1
        assert model.unique_name == "gpt-4o"
        assert model.display_name == "GPT-4o"
        assert model.provider_id == 1
        assert isinstance(model.created_at, datetime)

    def test_matcher_job_stage_timing_fields(self):
        """Test MatcherJob has stage timing fields for OCR and matching phases."""
        campaign_id = uuid4()
        job = MatcherJob(
            id=1,
            campaign_id=campaign_id,
            current_status=JobStatus.NOT_STARTED,
        )
        assert hasattr(job, "ocr_duration_seconds")
        assert hasattr(job, "matching_duration_seconds")
        assert job.ocr_duration_seconds is None
        assert job.matching_duration_seconds is None

    def test_matcher_job_stage_timing_can_be_set(self):
        """Test MatcherJob stage timing fields can be set with float values."""
        campaign_id = uuid4()
        job = MatcherJob(
            id=1,
            campaign_id=campaign_id,
            current_status=JobStatus.MATCHING_COMPLETED,
            ocr_duration_seconds=45.3,
            matching_duration_seconds=120.7,
        )
        assert job.ocr_duration_seconds == 45.3
        assert job.matching_duration_seconds == 120.7


class TestModelRelationships:
    """Tests for model relationships (foreign keys)."""

    def test_petition_scan_user_fk(self):
        """Test PetitionScan uploaded_by foreign key to User."""
        campaign_id = uuid4()
        scan = PetitionScan(
            campaign_id=campaign_id,
            original_filename="petition.pdf",
            stored_path="/uploads/petitions/petition.pdf",
            file_hash="abc123",
            uploaded_by=1,
        )
        assert scan.uploaded_by == 1

    def test_petition_crop_scan_fk(self):
        """Test PetitionCrop scan_id foreign key to PetitionScan."""
        crop = PetitionCrop(
            scan_id=1,
            crop_index=0,
            stored_path="/uploads/crops/crop_001.jpg",
            page_number=1,
        )
        assert crop.scan_id == 1

    def test_ocr_result_foreign_keys(self):
        """Test OcrResult foreign keys to crop and job."""
        ocr_result = OcrResult(crop_id=1, ocr_job_id=1)
        assert ocr_result.crop_id == 1
        assert ocr_result.ocr_job_id == 1

    def test_match_result_foreign_keys(self):
        """Test MatchResult foreign keys to ocr_result, matcher_job, and voter."""
        match = MatchResult(
            ocr_result_id=1,
            matcher_job_id=1,
            rank=1,
            voter_id=100,
            similarity_score=0.92,
            confidence_level=ConfidenceLevel.HIGH,
        )
        assert match.ocr_result_id == 1
        assert match.matcher_job_id == 1
        assert match.voter_id == 100

    def test_matcher_job_user_fk(self):
        """Test MatcherJob started_by foreign key to User."""
        campaign_id = uuid4()
        job = MatcherJob(
            id=1,
            campaign_id=campaign_id,
            current_status=JobStatus.NOT_STARTED,
            started_by=1,
        )
        assert job.started_by == 1
