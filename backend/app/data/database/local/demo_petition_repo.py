import asyncio
import uuid
from collections.abc import Sequence
from pathlib import Path

import fitz
import structlog
from sqlmodel import Session, select

from app.data.database.model.scanned_petition_model import (
	PetitionCropAssetEntity,
	PetitionScanEntity,
)
from app.data.database.model.schema import Campaign
from app.files.file_repository import (
	CreatePetitionCrop,
	CreatePetitionScan,
	ReadPetitionCrop,
	ReadPetitionScan,
)

logger = structlog.get_logger(__name__)


class DemoScannedPetitionRepository:
	def __init__(self, session: Session) -> None:
		self.db_session: Session = session

	async def _get_pdf_page_count_async(
		self, campaign_id: uuid.UUID, pdf_path: Path
	) -> PetitionScanEntity:
		def _get_page_count_sync() -> int:
			"""Synchronous function to open PDF and get page count."""
			with fitz.open(pdf_path) as pdf_document:
				num_pages = pdf_document.page_count
				return num_pages

		# Run the synchronous function in a separate thread
		page_count: int = await asyncio.to_thread(_get_page_count_sync)

		db_scan: PetitionScanEntity = PetitionScanEntity(
			file_name=pdf_path.name,
			local_path=str(pdf_path),
			total_pages=page_count,
			campaign_id=campaign_id,
		)

		return PetitionScanEntity.model_validate(db_scan)

	async def save_scanned_petitions(self, files: list[CreatePetitionScan]) -> None:
		campaign_id: uuid.UUID | None = None
		entities: list[PetitionScanEntity] = []
		# page_count_tasks: list[Task[PetitionScanEntity]] = []
		for f in files:
			if campaign_id is None:
				campaign_id = self.db_session.exec(
					select(Campaign.id).where(Campaign.unique_name == f.campaign_id)
				).one()
			"""
            task: Task[PetitionScanEntity] = asyncio.create_task(
                self._get_pdf_page_count_async(
                    campaign_id=campaign_id, pdf_path=Path(f.file_path)
                )
            )
            page_count_tasks.append(task)
            """
			entities.append(
				PetitionScanEntity(
					file_name=f.file_name,
					local_path=str(f.file_path),
					total_pages=f.page_count,
					campaign_id=campaign_id,
				)
			)

		# entities: list[PetitionScanEntity] = await asyncio.gather(*page_count_tasks)
		logger.debug(f"Updated {len(entities)} with their total page counts.")
		self.db_session.add_all(entities)
		self.db_session.commit()

	async def get_scanned_petitions(self, campaign_id: str) -> list[ReadPetitionScan]:
		campaign_db_id: uuid.UUID = self.db_session.exec(
			select(Campaign.id).where(Campaign.unique_name == campaign_id)
		).one()
		statement = select(PetitionScanEntity).where(
			PetitionScanEntity.campaign_id == campaign_db_id
		)
		petitions: Sequence[PetitionScanEntity] = self.db_session.exec(statement).all()

		results: list[ReadPetitionScan] = [
			ReadPetitionScan(
				id=str(scan.id),
				file_name=scan.file_name,
				file_path=scan.local_path,
				page_count=scan.total_pages,
				campaign_id=campaign_id,
			)
			for scan in petitions
		]

		return results

	async def save_cropped_assets(
		self, cropped_assets: list[CreatePetitionCrop]
	) -> None:
		campaign_id: uuid.UUID | None = None
		db_files: list[PetitionCropAssetEntity] = []
		for asset in cropped_assets:
			if campaign_id is None:
				campaign_id = self.db_session.exec(
					select(Campaign.id).where(Campaign.unique_name == asset.campaign_id)
				).one()

			db_files.append(
				PetitionCropAssetEntity(
					petition_scan_id=uuid.UUID(asset.petition_scan_id),
					file_path=asset.file_path,
					sheet_number=asset.page_number,
					top_crop=asset.top_crop,
					bottom_crop=asset.bottom_crop,
					campaign_id=campaign_id,
				)
			)

		self.db_session.add_all(db_files)
		self.db_session.commit()

	async def get_cropped_assets(self, petition_scan_id: str) -> list[ReadPetitionCrop]:
		statement = select(PetitionCropAssetEntity).where(
			PetitionCropAssetEntity.petition_scan_id == petition_scan_id
		)
		results: Sequence[PetitionCropAssetEntity] = self.db_session.exec(
			statement
		).all()

		crops: list[ReadPetitionCrop] = [
			ReadPetitionCrop(
				id=str(item.id),
				file_name=Path(item.file_path).name,
				page_number=item.sheet_number,
				file_path=item.file_path,
				top_crop=item.top_crop,
				bottom_crop=item.bottom_crop,
				petition_scan_id=str(item.petition_scan_id),
				campaign_id=str(item.campaign_id),
			)
			for item in results
		]

		return crops
