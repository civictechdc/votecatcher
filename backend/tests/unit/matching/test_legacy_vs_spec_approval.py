"""Approval test: matching scores for spec-format AND legacy-format voters.

Captures both voter formats side-by-side so we can verify:
1. Spec-format scores are UNCHANGED by the legacy fallback
2. Legacy-format scores improve from 0.0 after the fix

Run BEFORE fix to capture baseline (legacy address = 0.0).
Run AFTER fix — approve new baseline only if spec scores are identical.
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
from app.domain.voter import RegisteredVoter
from app.matching.matching_service import MatchingService
from uuid import uuid4


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


def _spec_voter(
    vid: int,
    first_name: str,
    last_name: str,
    street_number: str,
    street_name: str,
    street_type: str = "",
    zip_code: str = "",
) -> RegisteredVoter:
    return RegisteredVoter(
        id=vid,
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
    vid: int,
    first_name: str,
    last_name: str,
    street: str,
    zip_val: str | None = None,
) -> RegisteredVoter:
    return RegisteredVoter(
        id=vid,
        region_id=uuid4(),
        name_data={"first_name": first_name, "last_name": last_name},
        address_data={"street": street, "city": None, "state": None, "zip": zip_val},
        other_field_data={},
    )


class TestLegacyVsSpecMatchingApproval:
    def test_spec_and_legacy_format_score_matrix(self):
        spec = _dc_spec()
        service = MatchingService(session=MagicMock())

        spec_voters = [
            _spec_voter(1, "John", "Smith", "123", "Main", "St"),
            _spec_voter(2, "Jane", "Doe", "456", "Oak", "Ave"),
            _spec_voter(3, "Alexis", "Walter", "23407", "Hawkins Lock", ""),
        ]

        legacy_voters = [
            _legacy_voter(101, "John", "Smith", "123 Main St"),
            _legacy_voter(102, "Jane", "Doe", "456 Oak Ave"),
            _legacy_voter(103, "Alexis", "Walter", "23407 Hawkins Lock"),
        ]

        ocr_inputs = [
            {"name": "John Smith", "address": "123 Main St"},
            {"name": "Jane Doe", "address": "456 Oak Ave"},
            {"name": "Alexis Walter", "address": "23407 Hawkins Lock"},
            {"name": "Unknown Person", "address": "999 Nowhere Blvd"},
        ]

        lines: list[str] = []

        for ocr in ocr_inputs:
            lines.append(f"OCR: name={ocr['name']!r} address={ocr['address']!r}")
            lines.append("=" * 70)

            lines.append("SPEC-FORMAT VOTERS:")
            for v in spec_voters:
                r = service.calculate_spec_driven_similarity(spec, ocr, v)
                lines.append(
                    f"  id={v.id:3d} {v.name_data['first_name']:6s} {v.name_data['last_name']:<10s} "
                    f"| sim={r['similarity_score']:.4f} conf={r['confidence_level'].value:6s} "
                    f"| name={r['field_scores'].get('name', 0):.3f} addr={r['field_scores'].get('address', 0):.3f}"
                )

            lines.append("LEGACY-FORMAT VOTERS:")
            for v in legacy_voters:
                r = service.calculate_spec_driven_similarity(spec, ocr, v)
                lines.append(
                    f"  id={v.id:3d} {v.name_data['first_name']:6s} {v.name_data['last_name']:<10s} "
                    f"| sim={r['similarity_score']:.4f} conf={r['confidence_level'].value:6s} "
                    f"| name={r['field_scores'].get('name', 0):.3f} addr={r['field_scores'].get('address', 0):.3f}"
                )

            lines.append("")

        verify("\n".join(lines))
