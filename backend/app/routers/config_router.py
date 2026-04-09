"""Configuration router for feature flags and settings."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlmodel import Session

from app.api_models import ApiModel
from app.dependencies import get_session
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


@router.get("/features", response_model=FeatureFlagsResponse)
def get_features(  # nosemgrep: fastapi-unauthenticated-route
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


@router.get("/settings", response_model=SettingsResponse)
def get_settings_endpoint(  # nosemgrep: fastapi-unauthenticated-route
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


class ResetDataResponse(ApiModel):
    """Response for data reset operation."""

    deleted_counts: dict[str, int]
    message: str


@router.post("/reset-data", response_model=ResetDataResponse)
def reset_all_data(  # nosemgrep: fastapi-unauthenticated-route
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
    if settings.feature_demo or settings.feature_debug or settings.feature_simulation:
        conn = db_session.connection()
        deleted_counts = {}

        deleted_counts["match_results"] = conn.execute(
            text("DELETE FROM match_results")
        ).rowcount

        deleted_counts["ocr_results"] = conn.execute(
            text("DELETE FROM ocr_results")
        ).rowcount

        deleted_counts["ocr_jobs"] = conn.execute(text("DELETE FROM ocr_jobs")).rowcount

        deleted_counts["matcher_jobs"] = conn.execute(
            text("DELETE FROM matcher_jobs")
        ).rowcount

        deleted_counts["petition_crops"] = conn.execute(
            text("DELETE FROM petition_crops")
        ).rowcount

        deleted_counts["petition_scans"] = conn.execute(
            text("DELETE FROM petition_scans")
        ).rowcount

        deleted_counts["campaigns"] = conn.execute(
            text("DELETE FROM campaigns")
        ).rowcount

        db_session.commit()

        logger.info("All data reset complete", deleted_counts=deleted_counts)

        return ResetDataResponse(
            deleted_counts=deleted_counts,
            message="All data has been reset successfully",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Data reset is only available in non-production modes",
    )
