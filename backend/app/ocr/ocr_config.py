from typing import NamedTuple


class CropConfig(NamedTuple):
    BASE_THRESHOLD: int | float
    TOP_CROP: int | float
    BOTTOM_CROP: int | float


def get_current_crop_config() -> CropConfig:
    # TODO load current value from configuration or setting toggle via
    # front end interaction
    return CropConfig(BASE_THRESHOLD=85, TOP_CROP=0.385, BOTTOM_CROP=0.725)
