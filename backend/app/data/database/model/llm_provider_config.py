"""LLM Provider configuration model for storing API keys and model preferences."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class LlmProviderConfig(SQLModel, table=True):
    """LLM provider configuration stored in database."""

    __tablename__ = "llm_provider_config"

    id: int | None = Field(default=None, primary_key=True)
    provider: str = Field(unique=True, index=True)
    api_key: str | None = Field(default=None)
    model: str = Field()
    is_configured: bool = Field(default=False)
    last_validated: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(default=None)


class LlmProviderConfigCreate(SQLModel):
    """Schema for creating/updating provider config."""

    api_key: str
    model: str


class LlmProviderConfigRead(SQLModel):
    """Schema for reading provider config (no API key)."""

    provider: str
    model: str
    is_configured: bool
    last_validated: datetime | None


class LlmProviderTestResult(SQLModel):
    """Schema for provider test result."""

    valid: bool
    models: list[str] = []
    error: str | None = None
