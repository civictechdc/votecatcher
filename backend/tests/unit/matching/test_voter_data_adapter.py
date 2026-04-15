"""Tests for voter data handling through the public matching API.

Tests MatchingService.calculate_spec_driven_similarity with various voter
data formats (spec-structured, legacy, empty, mixed) to validate that
the matching pipeline correctly handles all address_data representations.

Uses the public API (MatchingService) rather than internal adapter functions.
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
                id="zip_code",
                csv_column_name="Zip_Code",
                data_type="text",
                category="address",
            ),
        ],
        field_mappings=[
            FieldMapping(
                ballot_field_id="name",
                template="{first_name} {last_name}",
            ),
            FieldMapping(
                ballot_field_id="address",
                template="{street_number} {street_name} {street_type}",
            ),
        ],
        hash_fields=["last_name", "first_name"],
        crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=85),
        pre_filter_field_id="zip_code",
    )


def _spec_voter(
    first_name: str = "Jane",
    last_name: str = "Doe",
    street_number: str = "123",
    street_name: str = "Main",
    street_type: str = "St",
    zip_code: str = "20001",
) -> RegisteredVoter:
    return RegisteredVoter(
        id=1,
        region_id=uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={
            "street_number": street_number,
            "street_name": street_name,
            "street_type": street_type,
            "zip_code": zip_code,
        },
        other_field_data={},
    )


def _legacy_voter(
    first_name: str = "Jane",
    last_name: str = "Doe",
    street: str = "123 Main St",
) -> RegisteredVoter:
    return RegisteredVoter(
        id=2,
        region_id=uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={"street": street, "city": "", "state": "", "zip": ""},
        other_field_data={},
    )


def _empty_voter(
    first_name: str = "Jane",
    last_name: str = "Doe",
) -> RegisteredVoter:
    return RegisteredVoter(
        id=3,
        region_id=uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={},
        other_field_data={},
    )


class TestSpecFormatVoterMatching:
    """Spec-structured address_data matches correctly through the public API."""

    def test_spec_voter_high_score_for_matching_name_and_address(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _spec_voter()
        ocr = {"name": "Jane Doe", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["similarity_score"] >= 0.80
        assert result["field_scores"]["name"] > 0.9
        assert result["field_scores"]["address"] > 0.8

    def test_spec_voter_name_score_1_for_exact_match(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _spec_voter(first_name="John", last_name="Smith")
        ocr = {"name": "John Smith", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["field_scores"]["name"] == 1.0


class TestLegacyFormatVoterMatching:
    """Legacy {street, city, state, zip} address_data still produces non-zero scores."""

    def test_legacy_voter_address_score_above_zero(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _legacy_voter(street="23407 Hawkins Lock")
        ocr = {"name": "Jane Doe", "address": "23407 Hawkins Lock"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["field_scores"]["address"] > 0.0

    def test_legacy_street_number_split(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _legacy_voter(street="123 Main St")
        ocr = {"name": "Jane Doe", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["field_scores"]["address"] > 0.5

    def test_legacy_no_street_number(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _legacy_voter(street="Hawkins Lock")
        ocr = {"name": "Jane Doe", "address": "Hawkins Lock"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["field_scores"]["address"] > 0.0


class TestEmptyVoterDataMatching:
    """Empty address_data produces low but non-crashing scores."""

    def test_empty_address_no_crash(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _empty_voter()
        ocr = {"name": "Jane Doe", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert "field_scores" in result
        assert "address" in result["field_scores"]

    def test_empty_address_low_score(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _empty_voter()
        ocr = {"name": "Jane Doe", "address": "123 Main St"}

        result = service.calculate_spec_driven_similarity(spec, ocr, voter)

        assert result["field_scores"]["address"] < 0.5


class TestCrossFormatParity:
    """Spec and legacy formats with equivalent data produce similar scores."""

    def test_spec_and_legacy_similar_scores_for_same_address(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())

        spec_voter = _spec_voter(
            first_name="Alexis",
            last_name="Walter",
            street_number="23407",
            street_name="Hawkins Lock",
            street_type="",
        )
        legacy_voter = _legacy_voter(
            first_name="Alexis",
            last_name="Walter",
            street="23407 Hawkins Lock",
        )
        ocr = {"name": "Alexis Walter", "address": "23407 Hawkins Lock"}

        spec_result = service.calculate_spec_driven_similarity(spec, ocr, spec_voter)
        legacy_result = service.calculate_spec_driven_similarity(
            spec, ocr, legacy_voter
        )

        assert (
            abs(
                spec_result["field_scores"]["address"]
                - legacy_result["field_scores"]["address"]
            )
            < 0.05
        )
        assert spec_result["confidence_level"] == legacy_result["confidence_level"]
