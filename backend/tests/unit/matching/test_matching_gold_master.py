"""Approval tests for the OLD matching algorithm (fuzzy_match_helper.py).

Locks the baseline truth for the algorithm at commit 11b9617:
  - Name: First_Name + " " + Last_Name (2 fields)
  - Address: Street_Number + Street_Name + Street_Type + Street_Dir_Suffix (4 fields)
  - Scoring: harmonic_mean(name_score, address_score) where each = fuzz.ratio / 100
  - Thresholds: HIGH >= 0.85, MEDIUM >= 0.60, LOW < 0.60

These approval tests serve as the GOLD MASTER baseline. Any future matching
implementation must prove parity against these locked snapshots.

Run with: uv run pytest tests/unit/matching/ -v --tb=short
"""

from pathlib import Path

import pytest
from rapidfuzz import fuzz

from tests.unit.matching.matching_databuilder import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    assign_confidence,
    load_ocr_results,
    load_voters_from_csv,
    run_old_algorithm_batch,
)

APPROVAL_DIR = Path(__file__).parent

pytestmark = pytest.mark.slow


def _approve_or_compare(approval_path: Path, actual: str) -> None:
    if approval_path.exists():
        expected = approval_path.read_text()
        assert actual == expected, (
            f"Snapshot mismatch. Delete {approval_path.name} to re-approve.\n"
            f"First diff at line: ..."
        )
    else:
        approval_path.write_text(actual)
        pytest.fail(
            f"Created initial approval file: {approval_path.name}. Re-run to verify."
        )


class TestOldAlgorithmSanity:
    """Sanity checks that the pure-function reproducer matches fuzz.ratio."""

    def test_identical_strings_score_1(self):
        assert fuzz.ratio("John Smith", "John Smith") / 100.0 == 1.0

    def test_harmonic_mean_identical_inputs(self):
        name = fuzz.ratio("John Smith", "John Smith") / 100.0
        addr = fuzz.ratio("123 Main St", "123 Main St") / 100.0
        harmonic = (2 * name * addr) / (name + addr)
        assert harmonic == 1.0

    def test_harmonic_mean_balanced(self):
        name = 0.9
        addr = 0.9
        harmonic = (2 * name * addr) / (name + addr)
        assert abs(harmonic - 0.9) < 1e-10

    def test_harmonic_mean_imbalanced(self):
        name = 1.0
        addr = 0.5
        harmonic = (2 * name * addr) / (name + addr)
        assert abs(harmonic - 2 / 3) < 1e-10

    def test_harmonic_mean_zero_division(self):
        name = 0.0
        addr = 0.0
        if name + addr == 0:
            harmonic = 0.0
        else:
            harmonic = (2 * name * addr) / (name + addr)
        assert harmonic == 0.0

    def test_confidence_thresholds(self):
        assert assign_confidence(1.0) == "HIGH"
        assert assign_confidence(0.85) == "HIGH"
        assert assign_confidence(0.84) == "MEDIUM"
        assert assign_confidence(0.60) == "MEDIUM"
        assert assign_confidence(0.59) == "LOW"
        assert assign_confidence(0.0) == "LOW"


class TestOldAlgorithmApproval:
    """Approval test: 50 OCR results × 100K voters via OLD algorithm.

    This locks the baseline truth. The approval file contains the top-1
    match for each OCR result, with name_score, address_score, combined_score,
    and confidence level.
    """

    @pytest.fixture(scope="class")
    def voters(self):
        return load_voters_from_csv()

    @pytest.fixture(scope="class")
    def ocr_results(self):
        return load_ocr_results()

    def test_voter_count(self, voters):
        assert len(voters) == 100000

    def test_ocr_count(self, ocr_results):
        assert len(ocr_results) == 50

    def test_old_algorithm_approval(self, voters, ocr_results, request):
        results = run_old_algorithm_batch(ocr_results, voters)

        lines = []
        lines.append("OLD ALGORITHM BASELINE (commit 11b9617)")
        lines.append(f"Voters: {len(voters)}, OCR results: {len(ocr_results)}")
        lines.append("Scoring: harmonic_mean(fuzz.ratio(name), fuzz.ratio(address))")
        lines.append(
            f"Thresholds: HIGH>={CONFIDENCE_HIGH}, MEDIUM>={CONFIDENCE_MEDIUM}, LOW<{CONFIDENCE_MEDIUM}"
        )
        lines.append("")
        lines.append(
            f"{'OCR#':>4} {'OCR Name':<25} {'Matched Name':<25} {'Name':>6} {'Addr':>6} {'Comb':>7} {'Conf':>6}"
        )
        lines.append("-" * 90)

        for r in results:
            top = r["top_match"]
            lines.append(
                f"{r['ocr_id']:>4} "
                f"{r['ocr_name']:<25} "
                f"{top['voter_name']:<25} "
                f"{top['name_score']:>6.3f} "
                f"{top['address_score']:>6.3f} "
                f"{top['combined_score']:>7.4f} "
                f"{top['confidence']:>6}"
            )

        high = sum(1 for r in results if r["top_match"]["confidence"] == "HIGH")
        med = sum(1 for r in results if r["top_match"]["confidence"] == "MEDIUM")
        low = sum(1 for r in results if r["top_match"]["confidence"] == "LOW")
        total = len(results)
        lines.append("")
        lines.append(
            f"Confidence: HIGH={high} ({high / total:.0%}) MEDIUM={med} ({med / total:.0%}) LOW={low} ({low / total:.0%})"
        )
        exact = sum(1 for r in results if r["top_match"]["name_score"] == 1.0)
        lines.append(f"Exact name matches (1.0): {exact}/{total} ({exact / total:.0%})")
        avg_combined = sum(r["top_match"]["combined_score"] for r in results) / total
        avg_name = sum(r["top_match"]["name_score"] for r in results) / total
        avg_addr = sum(r["top_match"]["address_score"] for r in results) / total
        lines.append(
            f"Averages: name={avg_name:.4f} addr={avg_addr:.4f} combined={avg_combined:.4f}"
        )
        min_combined = min(r["top_match"]["combined_score"] for r in results)
        max_combined = max(r["top_match"]["combined_score"] for r in results)
        lines.append(f"Range: combined min={min_combined:.4f} max={max_combined:.4f}")

        actual = "\n".join(lines) + "\n"

        approval_path = APPROVAL_DIR / f"{request.node.name}.approved.txt"
        _approve_or_compare(approval_path, actual)
