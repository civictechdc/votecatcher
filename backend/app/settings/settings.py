"""Aggregated application settings."""

from functools import lru_cache
from pathlib import Path

import structlog
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.providers.database_config import DatabaseConfig
from app.settings.providers.feature_config import FeatureConfig
from app.settings.providers.ocr_config import OcrConfig
from app.settings.providers.supabase_config import SupabaseConfig
from app.settings.sources.environment import EnvironmentSource

logger = structlog.get_logger(__name__)

BACKEND_DIR = Path(__file__).parent.parent.parent


def _resolve_env_path() -> Path:
	"""Resolve the env file path based on priority."""
	env_source = EnvironmentSource()
	env_file = env_source.get("ENV_FILE")

	if env_file:
		return BACKEND_DIR / env_file

	local_path = BACKEND_DIR / ".env.local"
	if local_path.exists():
		return local_path

	node_env = env_source.get("NODE_ENV", "development")
	return BACKEND_DIR / f".env.{node_env}"


class Settings(BaseSettings):
	"""Aggregated application settings."""

	model_config = SettingsConfigDict(
		extra="ignore",
		env_file=str(_resolve_env_path()),
		env_file_encoding="utf-8",
	)

	database_url: str = Field(
		default="sqlite:///./votecatcher.db", alias="DATABASE_URL"
	)

	supabase_url: str = Field(default="", alias="SUPABASE_URL")
	supabase_service_key: SecretStr = Field(
		default=SecretStr(""), alias="SUPABASE_SERVICE_KEY"
	)
	supabase_db_password: SecretStr = Field(
		default=SecretStr(""), alias="SUPABASE_DB_PASSWORD"
	)
	supabase_region: str = Field(default="aws-0-us-east-1", alias="SUPABASE_REGION")

	ocr_provider_name: str = Field(default="", alias="OCR_PROVIDER_NAME")
	ocr_model: str | None = Field(default=None, alias="OCR_PROVIDER_MODEL")
	ocr_api_key: SecretStr | None = Field(default=None, alias="OCR_PROVIDER_API_KEY")

	feature_simulation: bool = Field(default=False, alias="FEATURE_ENABLE_SIMULATION")
	feature_beta: bool = Field(default=False, alias="FEATURE_ENABLE_BETA_FEATURES")
	feature_debug: bool = Field(default=False, alias="FEATURE_ENABLE_DEBUG_MODE")
	feature_demo: bool = Field(default=False, alias="FEATURE_DEMO_MODE")

	runtime_dir: Path | None = Field(default=None, alias="DEV_LOCAL_RUNTIME_DIR")
	local_db: Path | None = Field(default=None, alias="DEV_LOCAL_RUNTIME_DB_DIR")
	crop_dir: Path | None = Field(default=None, alias="DEV_LOCAL_BALLOT_CROP_DIR")
	petition_dir: Path | None = Field(default=None, alias="DEV_LOCAL_PETITION_SCAN_DIR")
	campaigns_dir: Path | None = Field(default=None, alias="DEV_LOCAL_CAMPAIGNS_DIR")
	registration_dir: Path | None = Field(
		default=None, alias="DEV_LOCAL_VOTER_REGISTRATION_DIR"
	)
	ocr_dir: Path | None = Field(default=None, alias="DEV_LOCAL_OCR_DIR")

	@property
	def database(self) -> DatabaseConfig:
		return DatabaseConfig(url=self.database_url)

	@property
	def supabase(self) -> SupabaseConfig:
		return SupabaseConfig(
			project_url=self.supabase_url,
			service_key=self.supabase_service_key,
			db_password=self.supabase_db_password,
			region=self.supabase_region,
		)

	@property
	def ocr(self) -> OcrConfig:
		return OcrConfig(
			provider_name=self.ocr_provider_name,
			model=self.ocr_model,
			api_key=self.ocr_api_key,
		)

	@property
	def features(self) -> FeatureConfig:
		return FeatureConfig(
			simulation=self.feature_simulation,
			beta_features=self.feature_beta,
			debug_mode=self.feature_debug,
			demo_mode=self.feature_demo,
		)


@lru_cache
def get_settings() -> Settings:
	"""Get cached settings instance."""
	env_path = _resolve_env_path()
	logger.debug("Loading settings", env_path=str(env_path))
	return Settings()
