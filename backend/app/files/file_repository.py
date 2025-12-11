import uuid
from pathlib import Path
from typing import Protocol

from pandas import DataFrame
from pydantic import BaseModel


class RegisteredVoterRepository(Protocol):

    async def save_registered_voter_list(
        self, region_id: uuid.UUID, file_path: Path
    ) -> None: ...

    async def get_registered_voter_data(self, region_id: uuid.UUID) -> DataFrame: ...

    async def get_registered_voter_data_by_region_key(
        self, region_key: str
    ) -> DataFrame: ...


class ScannedPetition(BaseModel):
    id: str
    campaign_id: str
    file_path: str
    file_name: str
    page_count: int


class CreatePetitionScan(BaseModel):
    campaign_id: str
    file_path: str
    file_name: str
    page_count: int


class UpdatePetitionScan(BaseModel):
    id: str
    campaign_id: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    page_count: int | None = None


class ReadPetitionScan(ScannedPetition):
    pass


class CroppedAsset(BaseModel):
    petition_scan_id: str
    campaign_id: str
    file_path: str
    file_name: str
    top_crop: float
    bottom_crop: float
    page_number: int


class CreatePetitionCrop(CroppedAsset):
    pass


class ReadPetitionCrop(CroppedAsset):
    id: str
    page_number: int
    file_path: str
    file_name: str


class ScannedPetitionRepository(Protocol):

    async def save_scanned_petitions(self, files: list[CreatePetitionScan]) -> None: ...

    async def get_scanned_petitions(
        self,
        campaign_id: str,
    ) -> list[ReadPetitionScan]: ...

    async def save_cropped_assets(
        self, cropped_assets: list[CreatePetitionCrop]
    ) -> None: ...

    async def get_cropped_assets(
        self, petition_scan_id: str
    ) -> list[ReadPetitionCrop]: ...
