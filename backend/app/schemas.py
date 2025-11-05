from typing import Any

from pydantic import BaseModel, EmailStr


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
    results: dict = {}
    stats: dict = {}
