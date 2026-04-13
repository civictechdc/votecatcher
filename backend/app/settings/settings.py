"""Aggregated application settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import override

from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.settings.providers.database_config import DatabaseConfig
from app.settings.providers.features import AllFeatures
from app.settings.providers.features._base import FeatureFlag
from app.settings.providers.ocr_config import OcrConfig
from app.settings.providers.supabase_config import SupabaseConfig
from app.settings.sources.environment import EnvironmentSource

BACKEND_DIR = Path(__file__).parent.parent.parent


def _resolve_env_path() -> Path:
    """Resolve the env file path based on priority.

    Checks SETTINGS_ENV_FILE first for test override, then falls
    back to ENV_FILE, .env.local, or NODE_ENV-based path.

    Called lazily at Settings instantiation time (not module level)
    so tests can override via SETTINGS_ENV_FILE env var or by
    setting Settings.model_config['env_file'] before importing.
    """
    override = os.environ.get("SETTINGS_ENV_FILE")
    if override:
        return Path(override)

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
        env_file_encoding="utf-8",
    )

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        env_path = _resolve_env_path()
        dotenv = DotEnvSettingsSource(
            settings_cls,
            env_file=env_path,
            env_file_encoding="utf-8",
        )
        return (init_settings, env_settings, dotenv, file_secret_settings)

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

    app_name: str = Field(default="Votecatcher Backend", alias="APP_NAME")
    version: str = Field(default="", alias="APP_VERSION")

    feature_simulation: bool = Field(default=False, alias="FEATURE_ENABLE_SIMULATION")
    feature_beta: bool = Field(default=False, alias="FEATURE_ENABLE_BETA_FEATURES")
    feature_debug: bool = Field(default=False, alias="FEATURE_ENABLE_DEBUG_MODE")
    feature_demo: bool = Field(default=False, alias="FEATURE_DEMO_MODE")
    demo_reset: bool = Field(default=False, alias="FEATURE_DEMO_RESET")
    always_batch_ocr: bool = Field(default=True, alias="FEATURE_ALWAYS_BATCH_OCR")

    fieldspec_persistence: bool = Field(
        default=False, alias="FEATURE_FIELDSPEC_PERSISTENCE"
    )
    fieldspec_service: bool = Field(default=False, alias="FEATURE_FIELDSPEC_SERVICE")
    fieldspec_matching: bool = Field(default=False, alias="FEATURE_FIELDSPEC_MATCHING")
    fieldspec_voter_list: bool = Field(
        default=False, alias="FEATURE_FIELDSPEC_VOTER_LIST"
    )
    fieldspec_api: bool = Field(default=False, alias="FEATURE_FIELDSPEC_API")

    clear_runtime_on_launch: bool = Field(
        default=False, alias="DEV_CLEAR_RUNTIME_ON_LAUNCH"
    )

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
    def features(self) -> AllFeatures:
        from app.settings.providers.features.fieldspec import FieldSpecFlags
        from app.settings.providers.features.runtime import RuntimeFlags

        return AllFeatures(
            runtime=RuntimeFlags(
                simulation=FeatureFlag(
                    enabled=self.feature_simulation,
                    meta=RuntimeFlags.model_fields["simulation"].default.meta,
                ),
                beta_features=FeatureFlag(
                    enabled=self.feature_beta,
                    meta=RuntimeFlags.model_fields["beta_features"].default.meta,
                ),
                debug_mode=FeatureFlag(
                    enabled=self.feature_debug,
                    meta=RuntimeFlags.model_fields["debug_mode"].default.meta,
                ),
                demo_mode=FeatureFlag(
                    enabled=self.feature_demo,
                    meta=RuntimeFlags.model_fields["demo_mode"].default.meta,
                ),
                demo_reset=FeatureFlag(
                    enabled=self.demo_reset,
                    meta=RuntimeFlags.model_fields["demo_reset"].default.meta,
                ),
                always_batch_ocr=FeatureFlag(
                    enabled=self.always_batch_ocr,
                    meta=RuntimeFlags.model_fields["always_batch_ocr"].default.meta,
                ),
            ),
            fieldspec=FieldSpecFlags(
                persistence=FeatureFlag(
                    enabled=self.fieldspec_persistence,
                    meta=FieldSpecFlags.model_fields["persistence"].default.meta,
                ),
                service=FeatureFlag(
                    enabled=self.fieldspec_service,
                    meta=FieldSpecFlags.model_fields["service"].default.meta,
                ),
                matching=FeatureFlag(
                    enabled=self.fieldspec_matching,
                    meta=FieldSpecFlags.model_fields["matching"].default.meta,
                ),
                voter_list=FeatureFlag(
                    enabled=self.fieldspec_voter_list,
                    meta=FieldSpecFlags.model_fields["voter_list"].default.meta,
                ),
                api=FeatureFlag(
                    enabled=self.fieldspec_api,
                    meta=FieldSpecFlags.model_fields["api"].default.meta,
                ),
            ),
        )

    def local_campaign_base_dir(self) -> Path:
        if self.runtime_dir is None or self.campaigns_dir is None:
            raise ValueError("runtime_dir and campaigns_dir must be set")
        return self.runtime_dir.joinpath(self.campaigns_dir)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
