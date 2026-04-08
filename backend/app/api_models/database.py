"""API models for database operations."""

from pydantic import BaseModel, Field, SecretStr, field_validator


class DatabaseStatus(BaseModel):
    """Current database configuration status."""

    configured: bool
    type: str = Field(description="sqlite, postgres, or supabase")
    connected: bool
    message: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("sqlite", "postgres", "supabase"):
            raise ValueError("type must be sqlite, postgres, or supabase")
        return v


class SupabaseCredentials(BaseModel):
    """Supabase connection credentials."""

    project_url: str = Field(
        ...,
        description="Supabase project URL or custom domain",
        pattern=r"^https://[a-z0-9][a-z0-9.-]+\.[a-z]{2,}",
    )
    service_key: SecretStr = Field(
        ...,
        min_length=50,
        description="Service role key",
    )
    db_password: SecretStr = Field(
        ...,
        min_length=1,
        description="Database password",
    )


class ConnectionTestResult(BaseModel):
    """Result of connection test."""

    success: bool
    message: str
    project_ref: str | None = None


class ProvisionResult(BaseModel):
    """Result of Supabase provisioning."""

    success: bool
    message: str
    tables_created: list[str] | None = None
