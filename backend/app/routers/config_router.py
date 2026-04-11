"""Configuration router for feature flags and settings."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
from app.services.config_service import ConfigService
from app.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


class FeatureFlagsResponse(ApiModel):
    """Feature flags response."""

    simulation_mode: bool
    beta_features: bool
    debug_mode: bool
    demo_mode: bool
    demo_reset: bool
    always_batch_ocr: bool


class SettingsResponse(ApiModel):
    """Settings response."""

    ocr_provider: str | None
    ocr_model: str | None
    features: FeatureFlagsResponse


@router.get(  # nosemgrep: fastapi-unauthenticated-route
    "/features", response_model=FeatureFlagsResponse
)
def get_features(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FeatureFlagsResponse:
    """Get feature flags."""
    return FeatureFlagsResponse(
        simulation_mode=settings.feature_simulation,
        beta_features=settings.feature_beta,
        debug_mode=settings.feature_debug,
        demo_mode=settings.feature_demo,
        demo_reset=settings.demo_reset,
        always_batch_ocr=settings.always_batch_ocr,
    )


@router.get(  # nosemgrep: fastapi-unauthenticated-route
    "/settings", response_model=SettingsResponse
)
def get_settings_endpoint(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsResponse:
    """Get application settings."""
    return SettingsResponse(
        ocr_provider=settings.ocr_provider_name,
        ocr_model=settings.ocr_model,
        features=FeatureFlagsResponse(
            simulation_mode=settings.feature_simulation,
            beta_features=settings.feature_beta,
            debug_mode=settings.feature_debug,
            demo_mode=settings.feature_demo,
            demo_reset=settings.demo_reset,
            always_batch_ocr=settings.always_batch_ocr,
        ),
    )


class DeletedTableCounts(ApiModel):
    """Typed sub-model for table deletion counts."""

    match_results: int = 0
    ocr_results: int = 0
    ocr_jobs: int = 0
    matcher_jobs: int = 0
    petition_crops: int = 0
    petition_scans: int = 0
    campaigns: int = 0


class ResetDataResponse(ApiModel):
    """Response for data reset operation."""

    deleted_counts: DeletedTableCounts
    message: str


@router.post(  # nosemgrep: fastapi-unauthenticated-route
    "/reset-data", response_model=ResetDataResponse
)
def reset_all_data(
    db_session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResetDataResponse:
    """Reset all application data.

    This endpoint deletes ALL data from the database including:
    - All match results
    - All OCR results
    - All OCR jobs
    - All matcher jobs
    - All petition crops
    - All petition scans
    - All campaigns

    This is a destructive operation and should only be enabled in
    non-production environments.
    """
    if not (
        settings.feature_demo or settings.feature_debug or settings.feature_simulation
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data reset is only available in non-production modes",
        )

    service = ConfigService(db_session)
    deleted_counts = service.reset_all_data()

    return ResetDataResponse(
        deleted_counts=DeletedTableCounts(
            match_results=deleted_counts.get("match_results", 0),
            ocr_results=deleted_counts.get("ocr_results", 0),
            ocr_jobs=deleted_counts.get("ocr_jobs", 0),
            matcher_jobs=deleted_counts.get("matcher_jobs", 0),
            petition_crops=deleted_counts.get("petition_crops", 0),
            petition_scans=deleted_counts.get("petition_scans", 0),
            campaigns=deleted_counts.get("campaigns", 0),
        ),
        message="All data has been reset successfully",
    )
