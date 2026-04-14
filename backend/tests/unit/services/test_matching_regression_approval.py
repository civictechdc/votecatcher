"""Characterization test — captures spec-driven MatchingService behavior.

This approval test establishes a baseline for the spec-driven matching.
If scores change unexpectedly, investigate. If intentional (better scoring),
approve new baseline.
"""

from unittest.mock import MagicMock

from approvaltests import verify

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)
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
        hash_fields=["last_name", "first_name", "street_number", "street_name"],
        crop_config=CropConfig(top_crop=0.385, bottom_crop=0.725, base_threshold=85),
    )


_voter_counter = 0


def _build_mock_voter(
    name_data: dict, address_data: dict, other_field_data: dict | None = None
) -> MagicMock:
    global _voter_counter
    _voter_counter += 1
    voter = MagicMock()
    voter.name_data = name_data
    voter.address_data = address_data
    voter.other_field_data = other_field_data or {}
    voter.id = _voter_counter
    return voter


class TestDcMatchingScoreMatrix:
    def test_dc_matching_score_matrix(self):
        ocr_inputs = [
            {"name": "John Smith", "address": "123 Main St NW", "ward": ""},
            {"name": "Jane A Doe", "address": "456 Oak Ave NE", "ward": ""},
            {"name": "Robert Johnson", "address": "789 Pine St SW", "ward": ""},
            {"name": "", "address": "321 Elm Blvd SE", "ward": ""},
            {"name": "Mary Wilson", "address": "", "ward": ""},
        ]

        voters = [
            _build_mock_voter(
                {"first_name": "John", "middle_name": "", "last_name": "Smith"},
                {
                    "street_number": "123",
                    "street_name": "Main",
                    "street_type": "St",
                    "street_dir_suffix": "NW",
                },
            ),
            _build_mock_voter(
                {"first_name": "Jane", "middle_name": "A", "last_name": "Doe"},
                {
                    "street_number": "456",
                    "street_name": "Oak",
                    "street_type": "Ave",
                    "street_dir_suffix": "NE",
                },
            ),
            _build_mock_voter(
                {"first_name": "Robert", "middle_name": "", "last_name": "Johnson"},
                {
                    "street_number": "789",
                    "street_name": "Pine",
                    "street_type": "St",
                    "street_dir_suffix": "SW",
                },
            ),
            _build_mock_voter(
                {"first_name": "Mary", "middle_name": "", "last_name": "Wilson"},
                {
                    "street_number": "654",
                    "street_name": "Cedar",
                    "street_type": "Ln",
                    "street_dir_suffix": "NW",
                },
            ),
        ]

        spec = _dc_spec()
        service = MatchingService(session=MagicMock())

        lines: list[str] = []
        for ocr in ocr_inputs:
            lines.append(
                f"OCR: name={ocr.get('name', '')!r} address={ocr.get('address', '')!r}"
            )
            lines.append("-" * 60)

            for voter in voters:
                result = service.calculate_spec_driven_similarity(spec, ocr, voter)
                lines.append(
                    f"  vs id={voter.id:4d} "
                    f"| sim={result['similarity_score']:.4f} conf={result['confidence_level'].value:6s} "
                    f"| scores={result['field_scores']}"
                )
            lines.append("")

        verify("\n".join(lines))
