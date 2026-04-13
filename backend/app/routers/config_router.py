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
    simulation_mode: bool
    beta_features: bool
    debug_mode: bool
    demo_mode: bool
    demo_reset: bool
    always_batch_ocr: bool
    fieldspec_persistence: bool
    fieldspec_service: bool
    fieldspec_matching: bool
    fieldspec_voter_list: bool
    fieldspec_api: bool


def _build_features_response(settings: Settings) -> FeatureFlagsResponse:
    f = settings.features
    return FeatureFlagsResponse(
        simulation_mode=f.runtime.simulation.enabled,
        beta_features=f.runtime.beta_features.enabled,
        debug_mode=f.runtime.debug_mode.enabled,
        demo_mode=f.runtime.demo_mode.enabled,
        demo_reset=f.runtime.demo_reset.enabled,
        always_batch_ocr=f.runtime.always_batch_ocr.enabled,
        fieldspec_persistence=f.fieldspec.persistence.enabled,
        fieldspec_service=f.fieldspec.service.enabled,
        fieldspec_matching=f.fieldspec.matching.enabled,
        fieldspec_voter_list=f.fieldspec.voter_list.enabled,
        fieldspec_api=f.fieldspec.api.enabled,
    )


class SettingsResponse(ApiModel):
    """Settings response."""

    ocr_provider: str | None
    ocr_model: str | None
    features: FeatureFlagsResponse


@router.get("/features", response_model=FeatureFlagsResponse)
def get_features(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FeatureFlagsResponse:
    """Get feature flags."""
    return _build_features_response(settings)


@router.get("/settings", response_model=SettingsResponse)
def get_settings_endpoint(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsResponse:
    """Get application settings."""
    return SettingsResponse(
        ocr_provider=settings.ocr_provider_name,
        ocr_model=settings.ocr_model,
        features=_build_features_response(settings),
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


@router.post("/reset-data", response_model=ResetDataResponse)
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
