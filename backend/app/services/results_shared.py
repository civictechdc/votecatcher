"""Shared helpers for results query services.

Eliminates duplication between ResultsQueryService and CampaignQueryService.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlmodel import select

from app.services.prediction_builder import PredictionBuilder

if TYPE_CHECKING:
    from sqlmodel import Session

    from app.data.database.model.match_result import ConfidenceLevel, MatchResult


MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 1000


@dataclass(frozen=True)
class PredictionView:
    rank: int
    voter_name: str
    voter_address: str
    similarity_score: float
    confidence: "ConfidenceLevel"


@dataclass(frozen=True)
class OcrEnrichment:
    crop_id: int
    thumbnail_url: str
    crop_coordinates: dict[str, float] | None
    entry_coordinates: dict[str, float] | None
    page_number: int | None
    document_name: str
    scan_id: int | None
    extracted_text: str
    raw_extracted_text: dict | None = None


def validate_pagination_params(cursor: int | None, page_size: int) -> None:
    if cursor is not None and cursor < 0:
        raise ValueError("cursor must be non-negative")
    if not MIN_PAGE_SIZE <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE}"
        )


def build_predictions(
    session: "Session",
    match_results: list["MatchResult"],
) -> dict[int, list[PredictionView]]:
    from app.data.database.model.registered_voter import RegisteredVoter

    voter_ids = {r.voter_id for r in match_results if r.voter_id}
    voters_by_id: dict[int, RegisteredVoter] = {}

    if voter_ids:
        voters = session.exec(
            select(RegisteredVoter).where(RegisteredVoter.id.in_(voter_ids))
        ).all()
        voters_by_id = {v.id: v for v in voters}

    raw = PredictionBuilder.build(match_results, voters_by_id)

    predictions_by_ocr: dict[int, list[PredictionView]] = {}
    for ocr_id, preds in raw.items():
        predictions_by_ocr[ocr_id] = [
            PredictionView(
                rank=p.rank,
                voter_name=p.voter_name,
                voter_address=p.voter_address,
                similarity_score=p.similarity_score,
                confidence=p.confidence,
            )
            for p in preds
        ]

    return predictions_by_ocr


def enrich_ocr_lookup(
    session: "Session",
    ocr_ids: list[int],
) -> dict[int, OcrEnrichment]:
    from app.data.database.model.ocr_result import OcrResult
    from app.data.database.model.petition_crop import PetitionCrop
    from app.data.database.model.petition_scan import PetitionScan
    from app.services.entry_coordinates import compute_entry_coordinates
    from app.services.ocr_text_parser import OcrTextParser

    if not ocr_ids:
        return {}

    ocr_results = session.exec(select(OcrResult).where(OcrResult.id.in_(ocr_ids))).all()
    ocr_by_id = {o.id: o for o in ocr_results}

    crop_ids = {o.crop_id for o in ocr_results if o.crop_id}
    crop_by_id: dict[int, Any] = {}
    scan_by_id: dict[int, Any] = {}

    if crop_ids:
        crops = session.exec(
            select(PetitionCrop).where(PetitionCrop.id.in_(crop_ids))
        ).all()
        crop_by_id = {c.id: c for c in crops}

        scan_ids = {c.scan_id for c in crops if c.scan_id}
        if scan_ids:
            scans = session.exec(
                select(PetitionScan).where(PetitionScan.id.in_(scan_ids))
            ).all()
            scan_by_id = {s.id: s for s in scans}

    result: dict[int, OcrEnrichment] = {}
    for ocr_id in ocr_ids:
        ocr = ocr_by_id.get(ocr_id)
        extracted_text = OcrTextParser.format_text(ocr.extracted_text) if ocr else ""
        crop_id = ocr.crop_id if ocr else 0
        thumbnail_url = f"/api/crops/{crop_id}/image" if crop_id else ""

        crop = crop_by_id.get(crop_id) if crop_id else None
        scan = scan_by_id.get(crop.scan_id) if crop and crop.scan_id else None
        crop_coords = crop.crop_coordinates if crop else None

        result[ocr_id] = OcrEnrichment(
            crop_id=crop_id,
            thumbnail_url=thumbnail_url,
            crop_coordinates=crop_coords,
            entry_coordinates=(
                compute_entry_coordinates(crop_coords, ocr.ocr_index)
                if crop_coords and ocr
                else None
            ),
            page_number=crop.page_number if crop else None,
            document_name=scan.original_filename if scan else "",
            scan_id=crop.scan_id if crop else None,
            extracted_text=extracted_text,
            raw_extracted_text=ocr.extracted_text if ocr else None,
        )

    return result


def compute_next_cursor(
    paginated_ids: list[int],
    page_size: int,
    count_after: int,
) -> int | None:
    if len(paginated_ids) == page_size and count_after > 0:
        return paginated_ids[-1]
    return None
