"""Smart prediction truncation — pure function.

Replaces the hard [:5] slice with adaptive score-based filtering.
Three filters applied in order: max cap → absolute floor → relative
threshold → gap detection.  Always keeps at least 1 prediction.

Purity boundary: no I/O, no DB, no side effects.
"""

from __future__ import annotations

from typing import Protocol


class Scored(Protocol):
    similarity_score: float


def truncate_predictions(
    predictions: list[Scored],
    *,
    max_predictions: int = 5,
    relative_threshold: float = 0.5,
    absolute_floor: float = 0.1,
    gap_ratio: float = 2.0,
) -> list[Scored]:
    if not predictions:
        return []

    sorted_preds = sorted(predictions, key=lambda p: p.similarity_score, reverse=True)
    capped = sorted_preds[:max_predictions]

    above_floor = [p for p in capped if p.similarity_score >= absolute_floor]
    if not above_floor:
        return [sorted_preds[0]]

    top_score = above_floor[0].similarity_score
    min_score = top_score * relative_threshold
    above_relative = [p for p in above_floor if p.similarity_score >= min_score]
    if not above_relative:
        return [above_floor[0]]

    cut = len(above_relative)
    for i in range(1, len(above_relative)):
        prev = above_relative[i - 1].similarity_score
        curr = above_relative[i].similarity_score
        if curr > 0 and prev / curr > gap_ratio:
            cut = i
            break

    return above_relative[:cut]
