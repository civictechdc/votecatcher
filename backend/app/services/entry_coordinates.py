"""Compute per-entry highlight coordinates from crop coordinates and OCR index.

Calibrated for DC petition forms (demo data, 4723x2078 crop images).
Constants derived from pixel measurements: header=245px, stride=320px, box=370px (50px overlap).
See .agent-workspace/preview-entry-division/ for validation images.
See GitHub #61 for edge-detection research to handle scan/form variance.
"""

_HEADER_FRAC = 245 / 2078
_STRIDE_FRAC = 320 / 2078
_BOX_FRAC = 370 / 2078


def compute_entry_coordinates(
    crop_coordinates: dict[str, float],
    ocr_index: int,
) -> dict[str, float] | None:
    if (
        not crop_coordinates
        or "top" not in crop_coordinates
        or "bottom" not in crop_coordinates
    ):
        return None

    crop_top = crop_coordinates["top"]
    crop_height = crop_coordinates["bottom"] - crop_top
    if crop_height <= 0:
        return None

    entry_top = crop_top + (_HEADER_FRAC + ocr_index * _STRIDE_FRAC) * crop_height
    entry_bottom = entry_top + _BOX_FRAC * crop_height

    if entry_top < 0 or entry_bottom > 1.0:
        return None

    return {"top": round(entry_top, 4), "bottom": round(entry_bottom, 4)}
