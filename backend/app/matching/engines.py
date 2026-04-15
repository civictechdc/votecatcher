"""Score aggregation engines for matching.

Provides a Protocol-based strategy for combining per-field fuzzy scores
into a single similarity score. Engines are swappable via Settings
(`MATCHING_ENGINE` env var) or DI.

Engines:
    - HarmonicMeanAggregator: conservative, penalizes imbalanced scores.
      Matches the original fuzzy_match_helper algorithm (commit 11b9617).
    - WeightedAverageAggregator: permissive, arithmetic mean weighted by
      BallotField.match_weight. The pre-existing spec-driven default.

Use:
    from app.matching.engines import get_engine, HarmonicMeanAggregator

    engine = get_engine("harmonic")  # or "weighted"
    score = engine.aggregate({"name": 0.9, "address": 0.5}, {"name": 1.0, "address": 1.0})
"""

from typing import Protocol


class ScoreAggregator(Protocol):
    """Combine per-field scores into a single similarity score."""

    @property
    def name(self) -> str: ...

    def aggregate(
        self,
        field_scores: dict[str, float],
        weights: dict[str, float],
    ) -> float: ...


class HarmonicMeanAggregator:
    """Generalized weighted harmonic mean.

    For equal weights this reduces to the classic H = n / (1/x1 + ... + 1/xn).
    Scores of 0.0 are excluded from the calculation (they would make the
    harmonic mean zero regardless of other scores).

    This matches the original matching algorithm from fuzzy_match_helper.py.
    """

    @property
    def name(self) -> str:
        return "harmonic"

    def aggregate(
        self,
        field_scores: dict[str, float],
        weights: dict[str, float],
    ) -> float:
        weighted_pairs = [
            (s, weights.get(fid, 1.0))
            for fid, s in field_scores.items()
            if weights.get(fid, 1.0) > 0
        ]
        if not weighted_pairs:
            return 0.0
        numerator = 0.0
        denominator = 0.0
        for score, weight in weighted_pairs:
            if score <= 0.0:
                return 0.0
            numerator += weight
            denominator += weight / score
        if denominator <= 0.0 or numerator <= 0.0:
            return 0.0
        return numerator / denominator


class WeightedAverageAggregator:
    """Arithmetic weighted average of per-field scores.

    More permissive than harmonic mean when scores are imbalanced.
    Equivalent to the spec-driven algorithm before engine extraction.
    """

    @property
    def name(self) -> str:
        return "weighted"

    def aggregate(
        self,
        field_scores: dict[str, float],
        weights: dict[str, float],
    ) -> float:
        total_weight = sum(weights.get(fid, 1.0) for fid in field_scores)
        if total_weight <= 0.0:
            return 0.0
        weighted_sum = sum(s * weights.get(fid, 1.0) for fid, s in field_scores.items())
        return weighted_sum / total_weight


_ENGINES: dict[str, type[HarmonicMeanAggregator | WeightedAverageAggregator]] = {
    "harmonic": HarmonicMeanAggregator,
    "weighted": WeightedAverageAggregator,
}

DEFAULT_ENGINE = "harmonic"


def get_engine(name: str | None = None) -> ScoreAggregator:
    """Factory: return a ScoreAggregator by name.

    Args:
        name: Engine key ("harmonic", "weighted"). Falls back to DEFAULT_ENGINE.

    Returns:
        ScoreAggregator instance.

    Raises:
        ValueError: Unknown engine name.
    """
    key = (name or DEFAULT_ENGINE).lower().strip()
    cls = _ENGINES.get(key)
    if cls is None:
        raise ValueError(
            f"Unknown matching engine '{name}'. "
            f"Available: {', '.join(sorted(_ENGINES))}"
        )
    return cls()
