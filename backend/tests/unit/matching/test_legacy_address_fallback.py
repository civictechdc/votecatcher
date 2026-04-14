"""RED tests for legacy address_data fallback in matching.

Bug: Voters imported before G10 have address_data stored as
{"street": "23407 Hawkins Lock", "city": None, "state": None, "zip": None}
instead of spec-driven structured fields like
{"street_number": "23407", "street_name": "Hawkins Lock", "street_type": "", ...}.

The matching pipeline's render_template expects structured fields from the spec,
so it renders "" for all legacy voters → address score 0.0 → all matches LOW.

Fix: flatten_voter_data must detect legacy format and synthesize structured fields.
"""

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
from app.matching.voter_data_adapter import flatten_voter_data

from unittest.mock import MagicMock


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


def _legacy_voter(
    street: str = "23407 Hawkins Lock",
    zip_val: str | None = None,
    first_name: str = "Alexis",
    last_name: str = "Walter",
) -> RegisteredVoter:
    return RegisteredVoter(
        id=1,
        region_id=uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={"street": street, "city": None, "state": None, "zip": zip_val},
        other_field_data={},
    )


def _spec_voter() -> RegisteredVoter:
    return RegisteredVoter(
        id=2,
        region_id=uuid4(),
        name_data={"first_name": "John", "last_name": "Smith"},
        address_data={
            "street_number": "123",
            "street_name": "Main",
            "street_type": "St",
            "zip_code": "20001",
        },
        other_field_data={},
    )


class TestFlattenLegacyAddressData:
    """flatten_voter_data must handle legacy address_data format."""

    def test_legacy_street_used_as_street_name_when_no_structured_fields(self):
        """Legacy voter with 'street' key: '23407 Hawkins Lock' → street_name gets full value."""
        voter = _legacy_voter(street="23407 Hawkins Lock")
        spec = _dc_spec()
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        assert flat["street_name"] == "23407 Hawkins Lock"
        assert flat["street_number"] == ""

    def test_legacy_street_with_number_prefix_splits_into_street_number(self):
        """Legacy '23407 Hawkins Lock' → street_number='23407', street_name='Hawkins Lock'."""
        voter = _legacy_voter(street="23407 Hawkins Lock")
        spec = _dc_spec()
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        assert flat["street_number"] == "23407"
        assert flat["street_name"] == "Hawkins Lock"

    def test_legacy_zip_maps_to_zip_code(self):
        """Legacy 'zip' key maps to spec field 'zip_code'."""
        voter = _legacy_voter(zip_val="20001")
        spec = _dc_spec()
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        assert flat["zip_code"] == "20001"

    def test_spec_format_not_degraded(self):
        """Spec-format data (structured fields) must remain unchanged."""
        voter = _spec_voter()
        spec = _dc_spec()
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        assert flat["street_number"] == "123"
        assert flat["street_name"] == "Main"
        assert flat["street_type"] == "St"
        assert flat["zip_code"] == "20001"

    def test_legacy_with_no_street_key_no_crash(self):
        """Legacy format missing 'street' key should not crash."""
        voter = RegisteredVoter(
            id=3,
            region_id=uuid4(),
            name_data={"first_name": "A", "last_name": "B"},
            address_data={"city": "Washington"},
            other_field_data={},
        )
        spec = _dc_spec()
        flat = flatten_voter_data(voter, spec.voter_reg_fields)
        assert flat["street_number"] == ""
        assert flat["street_name"] == ""


class TestLegacyAddressMatchingScore:
    """End-to-end: legacy voter matches OCR text with non-zero address score."""

    def test_legacy_voter_address_score_above_zero(self):
        """Legacy voter '23407 Hawkins Lock' vs OCR '23407 Hawkins Lock' → address score > 0."""
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _legacy_voter(street="23407 Hawkins Lock")

        ocr_text = {"name": "Alexis Walter", "address": "23407 Hawkins Lock"}
        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert result["field_scores"]["address"] > 0.0, (
            f"Address score should be > 0 for identical addresses, "
            f"got {result['field_scores']['address']}"
        )

    def test_legacy_voter_high_similarity_for_matching_name_and_address(self):
        """Legacy voter with matching name + address should score HIGH confidence."""
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _legacy_voter(street="23407 Hawkins Lock")

        ocr_text = {"name": "Alexis Walter", "address": "23407 Hawkins Lock"}
        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert result["similarity_score"] >= 0.60, (
            f"Expected MEDIUM+ confidence for matching name+address, "
            f"got score={result['similarity_score']}, "
            f"confidence={result['confidence_level']}"
        )

    def test_spec_voter_still_matches_correctly(self):
        """Spec-format voters must still match correctly after fallback addition."""
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())
        voter = _spec_voter()

        ocr_text = {"name": "John Smith", "address": "123 Main St"}
        result = service.calculate_spec_driven_similarity(spec, ocr_text, voter)

        assert result["field_scores"]["address"] >= 0.80
