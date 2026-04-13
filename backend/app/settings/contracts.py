"""Configuration provider contracts using Protocol classes."""

from typing import Protocol

from pydantic import SecretStr

from app.settings.providers.features import AllFeatures


class ProvidesDatabaseConfig(Protocol):
    @property
    def url(self) -> str: ...

    @property
    def type(self) -> str: ...


class ProvidesSupabaseConfig(Protocol):
    @property
    def url(self) -> str: ...

    @property
    def service_key(self) -> SecretStr: ...

    @property
    def is_connected(self) -> bool: ...

    @property
    def database_url(self) -> str: ...


class ProvidesOcrConfig(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def model(self) -> str | None: ...

    @property
    def api_key(self) -> SecretStr | None: ...


class ProvidesFeatureConfig(Protocol):
    @property
    def features(self) -> AllFeatures: ...
