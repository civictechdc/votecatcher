"""Prediction builder for constructing voter predictions from match results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.data.database.model.match_result import MatchResult
    from app.data.database.model.registered_voter import RegisteredVoter


@dataclass(frozen=True)
class PredictionData:
    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: str


class PredictionBuilder:
    """Builds voter predictions from match results.

    Pure once voters_by_id is provided. Voter DB lookup is the caller's
    responsibility (effectful shell).
    """

    @staticmethod
    def format_voter_name(voter: Any) -> str:
        if not voter.name_data:
            return ""
        return " ".join(
            filter(
                None,
                [
                    voter.name_data.get("first_name", ""),
                    voter.name_data.get("last_name", ""),
                ],
            )
        )

    @staticmethod
    def format_voter_address(voter: Any) -> str:
        if not voter.address_data:
            return ""
        return ", ".join(
            filter(
                None,
                [
                    voter.address_data.get(k, "")
                    for k in ("street", "city", "state", "zip")
                ],
            )
        )

    @staticmethod
    def build(
        match_results: list[MatchResult],
        voters_by_id: dict[int, RegisteredVoter],
    ) -> dict[int, list[PredictionData]]:
        predictions_by_ocr: dict[int, list[PredictionData]] = {}

        for result in match_results:
            ocr_id = result.ocr_result_id
            if ocr_id not in predictions_by_ocr:
                predictions_by_ocr[ocr_id] = []

            voter = voters_by_id.get(result.voter_id) if result.voter_id else None

            predictions_by_ocr[ocr_id].append(
                PredictionData(
                    rank=result.rank,
                    voter_name=PredictionBuilder.format_voter_name(voter)
                    if voter
                    else "",
                    voter_address=PredictionBuilder.format_voter_address(voter)
                    if voter
                    else "",
                    similarity_score=result.similarity_score,
                    confidence=result.confidence_level.value
                    if result.confidence_level
                    else "LOW",
                )
            )

        for ocr_id in predictions_by_ocr:
            predictions_by_ocr[ocr_id].sort(key=lambda p: p.rank)

        return predictions_by_ocr
