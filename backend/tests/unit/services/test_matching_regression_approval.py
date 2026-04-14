"""Characterization test — captures current hardcoded MatchingService behavior.

This approval test establishes a baseline BEFORE the spec-driven refactor.
After G7.3, re-run to compare. If scores changed:
- Intentional (better scoring) → approve new baseline
- Unintentional → fix regression
"""

from unittest.mock import MagicMock

from approvaltests import verify

from app.matching.matching_service import MatchingService


def _build_mock_voter(name_data: dict, address_data: dict) -> MagicMock:
    voter = MagicMock()
    voter.name_data = name_data
    voter.address_data = address_data
    voter.id = hash(str(name_data) + str(address_data)) % 10000
    return voter


class TestDcMatchingScoreMatrix:
    def test_dc_matching_score_matrix(self):
        ocr_inputs = [
            {"name": "John Smith", "address": "123 Main St NW"},
            {"name": "Jane A Doe", "address": "456 Oak Ave NE"},
            {"name": "Robert Johnson", "address": "789 Pine St SW"},
            {"name": "", "address": "321 Elm Blvd SE"},
            {"name": "Mary Wilson", "address": ""},
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

        service = MatchingService(session=MagicMock())

        lines: list[str] = []
        for ocr in ocr_inputs:
            ocr_name, ocr_address = service.extract_name_and_address(ocr)
            lines.append(f"OCR: name={ocr_name!r} address={ocr_address!r}")
            lines.append("-" * 60)

            for voter in voters:
                voter_name = service._build_voter_name(voter)
                voter_address = service._build_voter_address(voter)
                similarity = service.calculate_similarity(
                    ocr_name=ocr_name,
                    ocr_address=ocr_address,
                    voter_name=voter_name,
                    voter_address=voter_address,
                )
                confidence = service.assign_confidence(similarity)
                name_score = round(
                    __import__("rapidfuzz").fuzz.ratio(ocr_name, voter_name) / 100.0, 4
                )
                addr_score = round(
                    __import__("rapidfuzz").fuzz.ratio(ocr_address, voter_address)
                    / 100.0,
                    4,
                )
                lines.append(
                    f"  vs {voter_name:25s} | {voter_address:25s} "
                    f"| sim={similarity:.4f} conf={confidence.value:6s} "
                    f"| name={name_score:.4f} addr={addr_score:.4f}"
                )
            lines.append("")

        verify("\n".join(lines))
