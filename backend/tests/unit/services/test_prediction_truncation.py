"""Unit tests for prediction truncation.

BDD-style tests for the smart truncation algorithm that replaces the
hard [:5] slice with adaptive score-based filtering.

VSDD Phase 2 — Red Gate. All tests MUST fail until truncation is implemented.
"""

from dataclasses import dataclass

import pytest

from app.services.prediction_truncation import truncate_predictions


@dataclass(frozen=True)
class FakePrediction:
    rank: int
    similarity_score: float
    confidence: str = "HIGH"


def _preds(*scores: float) -> list[FakePrediction]:
    return [
        FakePrediction(rank=i + 1, similarity_score=s) for i, s in enumerate(scores)
    ]


class TestTruncatePredictionsEmptyAndSingle:
    """Feature: Edge cases with 0-1 predictions."""

    def test_empty_list_returns_empty(self):
        assert truncate_predictions([]) == []

    def test_single_prediction_always_kept(self):
        preds = _preds(0.05)
        result = truncate_predictions(preds)
        assert len(result) == 1
        assert result[0].similarity_score == pytest.approx(0.05)

    def test_single_prediction_kept_regardless_of_floor(self):
        preds = _preds(0.001)
        result = truncate_predictions(preds)
        assert len(result) == 1


class TestTruncatePredictionsMaxCap:
    """Feature: Hard ceiling on prediction count."""

    def test_caps_at_max_predictions_default_5(self):
        preds = _preds(0.95, 0.93, 0.91, 0.89, 0.87, 0.85, 0.83)
        result = truncate_predictions(preds)
        assert len(result) == 5

    def test_caps_at_custom_max_predictions(self):
        preds = _preds(0.95, 0.93, 0.91, 0.89)
        result = truncate_predictions(preds, max_predictions=3)
        assert len(result) == 3

    def test_does_not_pad_if_fewer_than_max(self):
        preds = _preds(0.95, 0.93)
        result = truncate_predictions(preds, max_predictions=5)
        assert len(result) == 2


class TestTruncatePredictionsAbsoluteFloor:
    """Feature: Absolute minimum confidence threshold."""

    def test_drops_predictions_below_absolute_floor(self):
        preds = _preds(0.8, 0.05, 0.03)
        result = truncate_predictions(preds, absolute_floor=0.1)
        assert len(result) == 1
        assert result[0].similarity_score == pytest.approx(0.8)

    def test_keeps_predictions_at_or_above_floor(self):
        preds = _preds(0.8, 0.5, 0.15)
        result = truncate_predictions(
            preds, absolute_floor=0.1, relative_threshold=0.0, gap_ratio=float("inf")
        )
        assert len(result) == 3


class TestTruncatePredictionsRelativeThreshold:
    """Feature: Drop predictions below X% of top score."""

    def test_drops_below_half_of_top_score(self):
        preds = _preds(0.97, 0.12, 0.08)
        result = truncate_predictions(preds, relative_threshold=0.5)
        assert len(result) == 1
        assert result[0].similarity_score == pytest.approx(0.97)

    def test_keeps_predictions_within_relative_threshold(self):
        preds = _preds(0.50, 0.45, 0.30)
        result = truncate_predictions(preds, relative_threshold=0.5)
        scores = [p.similarity_score for p in result]
        assert 0.50 in scores
        assert 0.45 in scores
        assert len(result) >= 2

    def test_relative_threshold_calculated_from_first_prediction(self):
        preds = _preds(0.50, 0.45, 0.10)
        result = truncate_predictions(preds, relative_threshold=0.5)
        assert len(result) == 2


class TestTruncatePredictionsGapDetection:
    """Feature: Detect significant score drop-offs between adjacent predictions."""

    def test_truncates_at_large_gap(self):
        preds = _preds(0.80, 0.75, 0.30, 0.25)
        result = truncate_predictions(preds, gap_ratio=2.0)
        assert len(result) == 2
        assert [p.similarity_score for p in result] == pytest.approx([0.80, 0.75])

    def test_no_truncation_when_scores_gradual(self):
        preds = _preds(0.80, 0.75, 0.70, 0.65, 0.60)
        result = truncate_predictions(preds, gap_ratio=2.0)
        assert len(result) == 5

    def test_gap_detection_preserves_top_even_if_gap_at_rank_1_to_2(self):
        preds = _preds(0.80, 0.30, 0.25)
        result = truncate_predictions(preds, gap_ratio=2.0)
        assert len(result) == 1

    def test_custom_gap_ratio(self):
        preds = _preds(0.80, 0.60, 0.20)
        result = truncate_predictions(preds, gap_ratio=3.0)
        assert len(result) == 2


class TestTruncatePredictionsCombined:
    """Feature: All three filters applied together."""

    def test_dominant_top_match_drops_everyone_else(self):
        preds = _preds(0.97, 0.12, 0.08, 0.05, 0.03)
        result = truncate_predictions(preds)
        assert len(result) == 1

    def test_close_cluster_kept_then_gap_drops_tail(self):
        preds = _preds(0.30, 0.28, 0.27, 0.05, 0.03)
        result = truncate_predictions(preds)
        assert len(result) == 3

    def test_all_similar_kept_up_to_max(self):
        preds = _preds(0.50, 0.49, 0.48, 0.47, 0.46, 0.45)
        result = truncate_predictions(preds)
        assert len(result) == 5

    def test_floor_and_gap_both_apply(self):
        preds = _preds(0.80, 0.75, 0.30, 0.08)
        result = truncate_predictions(preds, absolute_floor=0.1, gap_ratio=2.0)
        assert len(result) == 2
        assert [p.similarity_score for p in result] == pytest.approx([0.80, 0.75])

    def test_minimum_one_prediction_guaranteed(self):
        preds = _preds(0.001)
        result = truncate_predictions(preds, absolute_floor=0.5, relative_threshold=0.9)
        assert len(result) == 1

    def test_preserves_rank_order(self):
        preds = _preds(0.90, 0.85, 0.80)
        result = truncate_predictions(preds)
        assert [p.rank for p in result] == [1, 2, 3]

    def test_handles_unsorted_input(self):
        preds = _preds(0.50, 0.90, 0.70)
        result = truncate_predictions(preds)
        assert result[0].similarity_score == pytest.approx(0.90)
        assert len(result) >= 1


class TestTruncatePredictionsDisabledFilters:
    """Feature: Individual filters can be effectively disabled."""

    def test_disable_relative_threshold(self):
        preds = _preds(0.97, 0.12)
        result = truncate_predictions(
            preds, relative_threshold=0.0, gap_ratio=float("inf")
        )
        assert len(result) == 2

    def test_disable_gap_detection(self):
        preds = _preds(0.80, 0.75, 0.40)
        result = truncate_predictions(preds, gap_ratio=float("inf"))
        assert len(result) == 3

    def test_disable_absolute_floor(self):
        preds = _preds(0.80, 0.05)
        result = truncate_predictions(
            preds,
            absolute_floor=0.0,
            relative_threshold=0.0,
            gap_ratio=float("inf"),
        )
        assert len(result) == 2
