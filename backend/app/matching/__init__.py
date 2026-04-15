"""Matching package for fuzzy matching OCR results against voter lists."""

from app.matching.engines import (
    HarmonicMeanAggregator,
    ScoreAggregator,
    WeightedAverageAggregator,
    get_engine,
)
from app.matching.matching_service import MatchingService

__all__ = [
    "MatchingService",
    "ScoreAggregator",
    "HarmonicMeanAggregator",
    "WeightedAverageAggregator",
    "get_engine",
]
