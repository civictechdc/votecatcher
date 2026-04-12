from typing import Any

from pydantic import EmailStr, Field

from app.api_models import ApiModel
from app.matching.response_adapter import OcrMatchResults


class Cookies(ApiModel):
    session_id: str


class WorkspaceResponse(ApiModel):
    id: str
    campaign_id: str
    campaign_name: str


class NewUser(ApiModel):
    email: EmailStr
    password: str


class Login(ApiModel):
    email: EmailStr
    password: str


class SessionTokenResponse(ApiModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    expires_at: int | None


class AuthUser(ApiModel):
    id: str
    email: EmailStr | None


class SuccessResponse(ApiModel):
    message: str


class VoterRecordsUploadResponse(ApiModel):
    file_name: str
    message: str


class PetitionFileUploadResponse(ApiModel):
    file_name: str
    message: str


class OcrMatchResponse(ApiModel):
    results: OcrMatchResults | dict[str, str] = Field(default_factory=dict)
    stats: dict[str, Any] = Field(default_factory=dict)


class OcrProviderPayload(ApiModel):
    provider_name: str
    provider_model: str
    api_key: str


class MatchFieldsResponse(ApiModel):
    id: str
    field_names: list[str]
