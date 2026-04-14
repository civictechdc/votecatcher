from typing import NamedTuple

from app.domain.field_spec import CropConfig as DomainCropConfig


class CropConfig(NamedTuple):
    BASE_THRESHOLD: int | float
    TOP_CROP: int | float
    BOTTOM_CROP: int | float


def get_current_crop_config() -> CropConfig:
    """Load crop config from the DC spec (or fallback defaults).

    After G10, crop config is spec-driven. This returns DC defaults
    which match the production petition template layout.
    """
    config = _load_spec_crop_config()
    if config is not None:
        return CropConfig(
            BASE_THRESHOLD=config.base_threshold,
            TOP_CROP=config.top_crop,
            BOTTOM_CROP=config.bottom_crop,
        )
    return CropConfig(BASE_THRESHOLD=85, TOP_CROP=0.385, BOTTOM_CROP=0.725)


def _load_spec_crop_config() -> DomainCropConfig | None:
    try:
        from app.dependencies import get_field_spec_service

        spec_service = next(get_field_spec_service())
        spec = spec_service.get_spec_by_key("DC")
        return spec.crop_config
    except Exception:
        return None
