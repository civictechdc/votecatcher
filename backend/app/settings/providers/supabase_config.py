"""Supabase configuration provider."""

from pydantic import BaseModel, Field, SecretStr

DEFAULT_REGION = "aws-0-us-east-1"


class SupabaseConfig(BaseModel):
    """Supabase configuration provider."""

    project_url: str = Field(default="")
    service_key: SecretStr = Field(default=SecretStr(""))
    db_password: SecretStr = Field(default=SecretStr(""))
    region: str = Field(default=DEFAULT_REGION)

    @property
    def url(self) -> str:
        return self.project_url

    @property
    def is_connected(self) -> bool:
        return bool(self.project_url and self.service_key.get_secret_value())

    @property
    def database_url(self) -> str:
        if not self.is_connected:
            return ""

        project_ref = self.project_url.replace("https://", "").replace(
            ".supabase.co", ""
        )
        password = self.db_password.get_secret_value()
        return f"postgresql://postgres.{project_ref}:{password}@{self.region}.pooler.supabase.com:6543/postgres"
