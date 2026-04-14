"""Approval test: live OCR data matched against legacy AND spec-format voters.

Uses the EXACT production dc.json5 spec (templates, weights, thresholds).
Asset files contain the 50 real OCR results and their top-1 matched voters
from the live DB captured 2026-04-14.

BEFORE FIX: legacy addr=0.000 for all rows (the bug).
AFTER FIX: legacy addr > 0, spec rows UNCHANGED.

Approve new baseline only if:
1. SPEC section is byte-identical to pre-fix baseline
2. LEGACY section shows addr > 0 (the fix worked)
"""

from unittest.mock import MagicMock

from approvaltests import verify

from app.matching.matching_service import MatchingService

from .matching_databuilder import (
    dc_production_spec,
    load_ocr_results,
    load_matched_voters,
    build_legacy_voter,
    build_spec_voter,
)


def _parse_street_number(street: str) -> tuple[str, str]:
    """Split '23407 Hawkins Lock' → ('23407', 'Hawkins Lock')."""
    parts = street.split(None, 1)
    if parts and parts[0].isdigit():
        return parts[0], parts[1] if len(parts) > 1 else ""
    return "", street


class TestLiveOcrMatchingApproval:
    def test_live_ocr_vs_legacy_and_spec_voters(self):
        spec = dc_production_spec()
        service = MatchingService(session=MagicMock())

        ocr_data = load_ocr_results()
        voter_data = load_matched_voters()

        lines: list[str] = []
        lines.append(f"spec: {spec.region_name}")
        lines.append(
            f"matchable: {[(f.id, f.match_weight) for f in spec.matchable_fields()]}"
        )
        lines.append(f"name_template: {spec.get_mapping_for('name').template}")
        lines.append(f"address_template: {spec.get_mapping_for('address').template}")
        lines.append(f"high_threshold: {service.high_threshold}")
        lines.append(f"medium_threshold: {service.medium_threshold}")
        lines.append(f"total_match_weight: {spec.total_match_weight()}")
        lines.append("")

        for idx in range(len(ocr_data)):
            ocr = ocr_data[idx]
            vd = voter_data[idx]

            lines.append(
                f"OCR #{idx + 1}: name={ocr['name']!r} address={ocr['address']!r}"
            )
            lines.append("-" * 80)

            num, name_rest = _parse_street_number(vd["street"])
            sv = build_spec_voter(
                vid=idx + 1,
                first_name=vd["first_name"],
                last_name=vd["last_name"],
                street_number=num,
                street_name=name_rest,
            )
            r = service.calculate_spec_driven_similarity(spec, ocr, sv)
            lines.append(
                f"  SPEC   id={sv.id:3d} "
                f"{vd['first_name']:10s} {vd['last_name']:<14s} "
                f"| sim={r['similarity_score']:.4f} conf={r['confidence_level'].value:6s} "
                f"| name={r['field_scores'].get('name', 0):.3f} "
                f"addr={r['field_scores'].get('address', 0):.3f} "
                f"ward={r['field_scores'].get('ward', 0):.3f}"
            )

            lv = build_legacy_voter(
                vid=idx + 101,
                first_name=vd["first_name"],
                last_name=vd["last_name"],
                street=vd["street"],
            )
            r = service.calculate_spec_driven_similarity(spec, ocr, lv)
            lines.append(
                f"  LEGACY id={lv.id:3d} "
                f"{vd['first_name']:10s} {vd['last_name']:<14s} "
                f"| sim={r['similarity_score']:.4f} conf={r['confidence_level'].value:6s} "
                f"| name={r['field_scores'].get('name', 0):.3f} "
                f"addr={r['field_scores'].get('address', 0):.3f} "
                f"ward={r['field_scores'].get('ward', 0):.3f}"
            )

            lines.append("")

        verify("\n".join(lines))
