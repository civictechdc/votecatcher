"""Unit tests for MatchingService.

Tests follow BDD scenarios from SPEC.md §3.4:
- Name + address extraction from OCR results
- RapidFuzz fuzzy matching with weighted scoring
- Confidence level assignment
- Spec-driven matching with dynamic field weights and render_template
"""

from unittest.mock import MagicMock
from uuid import uuid4

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)
from app.domain.voter import RegisteredVoter
from app.matching.matching_service import MatchingService


def _dc_spec() -> RegionFieldSpecConfig:
    return RegionFieldSpecConfig(
        region_name="District of Columbia",
        country_code="US",
        ballot_fields=[
            BallotField(
                id="name",
                label="Full Name",
                field_type="text",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="address",
                label="Address",
                field_type="address",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="ward",
                label="Ward",
                field_type="integer",
                required_for_matching=False,
                match_weight=0.3,
            ),
        ],
        voter_reg_fields=[
            VoterRegField(
                id="last_name",
                csv_column_name="Last_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="first_name",
                csv_column_name="First_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="middle_name",
                csv_column_name="Middle_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="street_number",
                csv_column_name="Street_Number",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_name",
                csv_column_name="Street_Name",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_type",
                csv_column_name="Street_Type",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_dir_suffix",
                csv_column_name="Street_Dir_Suffix",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="zip_code",
                csv_column_name="Zip_Code",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="ward",
                csv_column_name="WARD",
                data_type="integer",
                category="geography",
            ),
        ],
        field_mappings=[
            FieldMapping(
                ballot_field_id="name",
                template="{first_name} {middle_name} {last_name}",
            ),
            FieldMapping(
                ballot_field_id="address",
                template="{street_number} {street_name} {street_type} {street_dir_suffix}",
            ),
            FieldMapping(ballot_field_id="ward", template="{ward}"),
        ],
        hash_fields=[
            "last_name",
            "first_name",
            "street_number",
            "street_name",
            "zip_code",
        ],
        crop_config=CropConfig(top_crop=0.385, bottom_crop=0.725, base_threshold=85),
    )


def _make_voter(
    name_data: dict | None = None,
    address_data: dict | None = None,
    other_field_data: dict | None = None,
) -> RegisteredVoter:
    return RegisteredVoter(
        id=1,
        region_id=uuid4(),
        name_data=name_data or {},
        address_data=address_data or {},
        other_field_data=other_field_data or {},
    )


class TestMatchingServiceExtraction:
    """Tests for extracting name and address from OCR results."""

    def test_extract_from_ocr_result_simple(self):
        """Should extract name and address from simple OCR text."""
        service = MatchingService(session=MagicMock())
        ocr_text = {
            "name": "John Smith",
            "address": "123 Main St",
        }

        name, address = service.extract_name_and_address(ocr_text)

        assert name == "John Smith"
        assert address == "123 Main St"

    def test_extract_from_ocr_result_missing_fields(self):
        """Should handle missing fields gracefully."""
        service = MatchingService(session=MagicMock())
        ocr_text = {"name": "John Smith"}

        name, address = service.extract_name_and_address(ocr_text)

        assert name == "John Smith"
        assert address == ""

    def test_extract_from_ocr_result_empty(self):
        """Should handle empty OCR text."""
        service = MatchingService(session=MagicMock())
        ocr_text = {}

        name, address = service.extract_name_and_address(ocr_text)

        assert name == ""
        assert address == ""


class TestMatchingServiceSimilarity:
    """Tests for fuzzy matching similarity calculation."""

    def test_calculate_similarity_exact_match(self):
        """Should return high score for exact match."""
        service = MatchingService(session=MagicMock())
        score = service.calculate_similarity(
            ocr_name="John Smith",
            ocr_address="123 Main St",
            voter_name="John Smith",
            voter_address="123 Main St",
        )

        assert score >= 0.95

    def test_calculate_similarity_partial_match(self):
        """Should return medium score for partial match."""
        service = MatchingService(session=MagicMock())
        score = service.calculate_similarity(
            ocr_name="John Smith",
            ocr_address="123 Main St",
            voter_name="John Smyth",
            voter_address="123 Main Street",
        )

        assert 0.60 <= score < 0.95

    def test_calculate_similarity_no_match(self):
        """Should return low score for no match."""
        service = MatchingService(session=MagicMock())
        score = service.calculate_similarity(
            ocr_name="John Smith",
            ocr_address="123 Main St",
            voter_name="Jane Doe",
            voter_address="456 Oak Ave",
        )

        assert score < 0.60

    def test_calculate_similarity_empty_ocr(self):
        """Should return 0 for empty OCR input."""
        service = MatchingService(session=MagicMock())
        score = service.calculate_similarity(
            ocr_name="",
            ocr_address="",
            voter_name="John Smith",
            voter_address="123 Main St",
        )

        assert score == 0.0


class TestMatchingServiceConfidence:
    """Tests for confidence level assignment."""

    def test_assign_confidence_high(self):
        """Should assign HIGH for score >= 0.85."""
        from app.data.database.model.match_result import ConfidenceLevel

        service = MatchingService(session=MagicMock())
        confidence = service.assign_confidence(0.90)

        assert confidence == ConfidenceLevel.HIGH

    def test_assign_confidence_medium(self):
        """Should assign MEDIUM for 0.60 <= score < 0.85."""
        from app.data.database.model.match_result import ConfidenceLevel

        service = MatchingService(session=MagicMock())
        confidence = service.assign_confidence(0.70)

        assert confidence == ConfidenceLevel.MEDIUM

    def test_assign_confidence_low(self):
        """Should assign LOW for score < 0.60."""
        from app.data.database.model.match_result import ConfidenceLevel

        service = MatchingService(session=MagicMock())
        confidence = service.assign_confidence(0.40)

        assert confidence == ConfidenceLevel.LOW

    def test_assign_confidence_boundary_high(self):
        """Should assign HIGH at exact 0.85 threshold."""
        from app.data.database.model.match_result import ConfidenceLevel

        service = MatchingService(session=MagicMock())
        confidence = service.assign_confidence(0.85)

        assert confidence == ConfidenceLevel.HIGH

    def test_assign_confidence_boundary_medium(self):
        """Should assign MEDIUM at exact 0.60 threshold."""
        from app.data.database.model.match_result import ConfidenceLevel

        service = MatchingService(session=MagicMock())
        confidence = service.assign_confidence(0.60)

        assert confidence == ConfidenceLevel.MEDIUM


class TestMatchingServiceInitialization:
    """Tests for MatchingService initialization."""

    def test_matching_service_initializes_with_session(self):
        """MatchingService should initialize with database session."""
        mock_session = MagicMock()
        service = MatchingService(session=mock_session)
        assert service.session == mock_session

    def test_matching_service_has_default_thresholds(self):
        """MatchingService should have default confidence thresholds."""
        service = MatchingService(session=MagicMock())
        assert service.high_threshold == 0.85
        assert service.medium_threshold == 0.60

    def test_matching_service_allows_custom_thresholds(self):
        """MatchingService should allow custom thresholds."""
        service = MatchingService(
            session=MagicMock(),
            high_threshold=0.90,
            medium_threshold=0.70,
        )
        assert service.high_threshold == 0.90
        assert service.medium_threshold == 0.70


class TestSpecDrivenSimilarity:
    def test_spec_driven_similarity_uses_spec_weights(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(
            name_data={"first_name": "John", "last_name": "Smith"},
            address_data={
                "street_number": "123",
                "street_name": "Main",
                "street_type": "St",
            },
            other_field_data={"ward": "3"},
        )
        ocr_text = {"name": "John Smith", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert "field_scores" in result
        assert "name" in result["field_scores"]
        assert "address" in result["field_scores"]

    def test_spec_driven_similarity_builds_voter_name_from_spec(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(
            name_data={"first_name": "Jane", "middle_name": "A", "last_name": "Doe"},
        )
        ocr_text = {"name": "Jane A Doe", "address": ""}

        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert result["field_scores"]["name"] >= 0.95

    def test_spec_driven_similarity_builds_voter_address_from_spec(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(
            address_data={
                "street_number": "456",
                "street_name": "Oak",
                "street_type": "Ave",
                "street_dir_suffix": "NE",
            },
        )
        ocr_text = {"name": "", "address": "456 Oak Ave NE"}

        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert result["field_scores"]["address"] >= 0.80

    def test_spec_driven_ward_has_reduced_weight(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(other_field_data={"ward": "3"})
        ocr_text = {"name": "", "address": "", "ward": "3"}

        service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        name_matchable = any(
            f.id == "name" and f.match_weight == 1.0 for f in spec.matchable_fields()
        )
        ward_field = next(f for f in spec.ballot_fields if f.id == "ward")
        assert ward_field.match_weight == 0.3
        assert name_matchable

    def test_spec_driven_field_scores_keyed_by_ballot_field_id(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(
            name_data={"first_name": "John", "last_name": "Smith"},
            address_data={"street_number": "123", "street_name": "Main"},
            other_field_data={"ward": "3"},
        )
        ocr_text = {"name": "John Smith", "address": "123 Main", "ward": "3"}

        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        matchable_ids = {f.id for f in spec.matchable_fields()}
        for field_id in matchable_ids:
            assert field_id in result["field_scores"]

    def test_spec_driven_overall_score_is_weighted(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _make_voter(
            name_data={"first_name": "John", "last_name": "Smith"},
            address_data={"street_number": "123", "street_name": "Main"},
        )
        ocr_text = {"name": "John Smith", "address": "123 Main"}

        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        total_weight = spec.total_match_weight()
        assert total_weight > 0
        assert 0.0 <= result["similarity_score"] <= 1.0
