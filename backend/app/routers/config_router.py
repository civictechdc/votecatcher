"""Configuration router for feature flags and settings."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.settings.env_settings import AppSettings, get_settings

router = APIRouter(prefix="/config", tags=["config"])


class FeatureFlagsResponse(BaseModel):
	"""Feature flags response - camelCase for API contract."""

	simulationMode: bool  # noqa: N815
	betaFeatures: bool  # noqa: N815
	debugMode: bool  # noqa: N815
	demoMode: bool  # noqa: N815
	demoReset: bool  # noqa: N815


class SettingsResponse(BaseModel):
	"""Settings response."""

	ocr_provider: str | None
	ocr_model: str | None
	features: FeatureFlagsResponse


@router.get("/features", response_model=FeatureFlagsResponse)
def get_features(
	settings: Annotated[AppSettings, Depends(get_settings)],
) -> FeatureFlagsResponse:
	"""Get feature flags."""
	return FeatureFlagsResponse(
		simulationMode=settings.enable_simulation,
		betaFeatures=settings.enable_beta_features,
		debugMode=settings.enable_debug_mode,
		demoMode=settings.demo_mode,
		demoReset=settings.demo_reset,
	)


@router.get("/settings", response_model=SettingsResponse)
def get_settings_endpoint(
	settings: Annotated[AppSettings, Depends(get_settings)],
) -> SettingsResponse:
	"""Get application settings."""
	return SettingsResponse(
		ocr_provider=settings.ocr_provider_name,
		ocr_model=settings.ocr_model,
		features=FeatureFlagsResponse(
			simulationMode=settings.enable_simulation,
			betaFeatures=settings.enable_beta_features,
			debugMode=settings.enable_debug_mode,
			demoMode=settings.demo_mode,
			demoReset=settings.demo_reset,
		),
	)
