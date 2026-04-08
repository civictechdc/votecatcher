import uuid
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class CampaignData(BaseModel):
    id: str
    unique_name: str
    title: str
    year_active: str


class CreateCampaign(BaseModel):
    unique_name: str
    title: str
    description: str
    year_active: str
    region_key: str


class ReadCampaign(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime | None
    unique_name: str
    title: str
    description: str
    year_active: str
    region_id: str
    region_key: str


class CampaignRepository(Protocol):
    async def save_campaign(self, new_campaign: CreateCampaign) -> uuid.UUID: ...

    async def fetch_campaign(self, unique_name: str) -> ReadCampaign: ...
