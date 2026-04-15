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
        name_parts = []
        if voter.name_data:
            first = voter.name_data.get("first_name", "")
            last = voter.name_data.get("last_name", "")
            if first:
                name_parts.append(first)
            if last:
                name_parts.append(last)
        return " ".join(name_parts)

    @staticmethod
    def format_voter_address(voter: Any) -> str:
        addr_parts = []
        if voter.address_data:
            for key in ("street", "city", "state", "zip"):
                val = voter.address_data.get(key, "")
                if val:
                    addr_parts.append(val)
        return ", ".join(addr_parts)

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

            voter_name = ""
            voter_address = ""
            if voter:
                voter_name = PredictionBuilder.format_voter_name(voter)
                voter_address = PredictionBuilder.format_voter_address(voter)

            predictions_by_ocr[ocr_id].append(
                PredictionData(
                    rank=result.rank,
                    voter_name=voter_name,
                    voter_address=voter_address,
                    similarity_score=result.similarity_score,
                    confidence=result.confidence_level.value
                    if result.confidence_level
                    else "LOW",
                )
            )

        for ocr_id in predictions_by_ocr:
            predictions_by_ocr[ocr_id].sort(key=lambda p: p.rank)

        return predictions_by_ocr
