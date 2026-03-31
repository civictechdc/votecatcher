"""Database configuration provider."""

from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
	"""Database configuration provider."""

	url: str = Field(default="sqlite:///./votecatcher.db")
	type: str = Field(default="sqlite", init=False)

	@field_validator("url")
	@classmethod
	def _validate_url(cls, v: str) -> str:
		if not v:
			return v
		if " " in v:
			raise ValueError("Database URL must not contain spaces")
		scheme = urlparse(v).scheme
		if scheme and scheme not in (
			"sqlite",
			"postgresql",
			"postgres",
			"postgresql+psycopg",
			"postgresql+psycopg2",
			"postgresql+asyncpg",
		):
			raise ValueError(f"Unsupported database scheme: {scheme}")
		return v

	def model_post_init(self, __context: object) -> None:
		self.type = self._detect_type()

	def _detect_type(self) -> str:
		if "supabase.co" in self.url:
			return "supabase"
		scheme = urlparse(self.url).scheme
		if scheme in ("postgresql", "postgres") or scheme.startswith("postgresql+"):
			return "postgres"
		return "sqlite"
