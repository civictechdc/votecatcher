"""OCR configuration provider."""

from pydantic import BaseModel, Field, SecretStr


class OcrConfig(BaseModel):
    """OCR configuration provider."""

    provider_name: str = Field(default="")
    model: str | None = Field(default=None)
    api_key: SecretStr | None = Field(default=None)
