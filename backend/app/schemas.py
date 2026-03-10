from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.matching.response_adapter import OcrMatchResults


class Cookies(BaseModel):
	session_id: str


class WorkspaceResponse(BaseModel):
	id: str
	campaign_id: str
	campaign_name: str


class NewUser(BaseModel):
	email: EmailStr
	password: str


class Login(BaseModel):
	email: EmailStr
	password: str


class SessionTokenResponse(BaseModel):
	access_token: str
	token_type: str
	refresh_token: str
	expires_in: int
	expires_at: int | None


class AuthUser(BaseModel):
	id: str
	email: EmailStr | None


class SuccessResponse(BaseModel):
	message: str


class VoterRecordsUploadResponse(BaseModel):
	file_name: str
	message: str


class PetitionFileUploadResponse(BaseModel):
	file_name: str
	message: str


class OcrMatchResponse(BaseModel):
	results: OcrMatchResults | dict[str, str] = Field(default_factory=dict)
	stats: dict[str, Any] = Field(default_factory=dict)


class OcrProviderPayload(BaseModel):
	provider_name: str
	provider_model: str
	api_key: str


class MatchFieldsResponse(BaseModel):
	id: str
	field_names: list[str]
