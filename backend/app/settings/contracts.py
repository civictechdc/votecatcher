"""Configuration provider contracts using Protocol classes."""

from typing import Protocol

from pydantic import SecretStr


class ProvidesDatabaseConfig(Protocol):
	"""Any source that provides database configuration."""

	@property
	def url(self) -> str: ...

	@property
	def type(self) -> str: ...


class ProvidesSupabaseConfig(Protocol):
	"""Supabase-specific configuration."""

	@property
	def url(self) -> str: ...

	@property
	def service_key(self) -> SecretStr: ...

	@property
	def is_connected(self) -> bool: ...

	@property
	def database_url(self) -> str: ...


class ProvidesOcrConfig(Protocol):
	"""OCR provider configuration."""

	@property
	def provider_name(self) -> str: ...

	@property
	def model(self) -> str | None: ...

	@property
	def api_key(self) -> SecretStr | None: ...


class ProvidesFeatureConfig(Protocol):
	"""Feature flag configuration."""

	@property
	def simulation(self) -> bool: ...

	@property
	def beta_features(self) -> bool: ...

	@property
	def debug_mode(self) -> bool: ...

	@property
	def demo_mode(self) -> bool: ...
