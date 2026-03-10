from functools import lru_cache
from pathlib import Path

import structlog
from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = structlog.get_logger(__name__)


class AppSettings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=find_dotenv(), extra="ignore", env_file_encoding="utf-8"
	)

	app_name: str = "Votecatcher Backend"
	version: str = ""
	runtime_dir: Path | None = Field(alias="DEV_LOCAL_RUNTIME_DIR", default=None)
	local_db: Path | None = Field(alias="DEV_LOCAL_RUNTIME_DB_DIR", default=None)
	crop_dir: Path | None = Field(alias="DEV_LOCAL_BALLOT_CROP_DIR", default=None)
	petition_dir: Path | None = Field(alias="DEV_LOCAL_PETITION_SCAN_DIR", default=None)
	campaigns_dir: Path | None = Field(alias="DEV_LOCAL_CAMPAIGNS_DIR", default=None)
	registration_dir: Path | None = Field(
		alias="DEV_LOCAL_VOTER_REGISTRATION_DIR", default=None
	)
	ocr_dir: Path | None = Field(alias="DEV_LOCAL_OCR_DIR", default=None)

	clear_runtime_on_launch: bool = Field(
		alias="DEV_CLEAR_RUNTIME_ON_LAUNCH", default=False
	)

	ocr_provider_name: str | None = Field(alias="OCR_PROVIDER_NAME", default=None)
	ocr_model: str | None = Field(alias="OCR_PROVIDER_MODEL", default=None)
	ocr_api_key: str | None = Field(alias="OCR_PROVIDER_API_KEY", default=None)

	enable_simulation: bool = Field(alias="FEATURE_ENABLE_SIMULATION", default=False)
	enable_beta_features: bool = Field(
		alias="FEATURE_ENABLE_BETA_FEATURES", default=False
	)
	enable_debug_mode: bool = Field(alias="FEATURE_ENABLE_DEBUG_MODE", default=False)
	demo_mode: bool = Field(alias="FEATURE_DEMO_MODE", default=False)
	demo_reset: bool = Field(alias="FEATURE_DEMO_RESET", default=False)

	def local_campaign_base_dir(self) -> Path:
		if self.runtime_dir is None or self.campaigns_dir is None:
			raise ValueError("runtime_dir and campaigns_dir must be set")
		return self.runtime_dir.joinpath(self.campaigns_dir)


@lru_cache
def get_settings() -> AppSettings:
	logger.debug(f"Env file path: {find_dotenv()}")
	return AppSettings()
