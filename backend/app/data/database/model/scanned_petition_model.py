import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class PetitionScanEntity(SQLModel, table=True):
    __tablename__ = "petition_scans"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_name: str = Field(index=True)
    local_path: str = Field(unique=True)
    total_pages: int = Field()
    campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")


class PetitionCropAssetEntity(SQLModel, table=True):
    __tablename__ = "petition_crop_assets"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sheet_number: int = Field()
    file_path: str = Field()
    top_crop: float = Field()
    bottom_crop: float = Field()
    petition_scan_id: uuid.UUID = Field(foreign_key="petition_scans.id")
    campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")
