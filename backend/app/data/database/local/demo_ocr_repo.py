import uuid
from collections.abc import Iterable, Sequence
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session, select

from app.data.database.local.demo_local_db import get_db_session
from app.data.database.local.demo_match_task_repo import MatchingTaskEntity
from app.data.database.model.ocr_model import (
	AddOcrAiModel,
	CreateOcrJob,
	CreateOcrProvider,
	OcrAiModel,
	OcrJob,
	OcrProvider,
	OcrResult,
	ReadOcrJobStatus,
	ReadOcrModel,
	ReadOcrProvider,
	UpdateOcrJobStatus,
)
from app.data.database.model.scanned_petition_model import (
	PetitionScanEntity,
)
from app.data.database.model.schema import Campaign
from app.ocr.data.data_models import OCREntry, OcrResultItem
from app.ocr.data.ocr_repository import OcrJobRepository


class DemoOcrProviderRepo:
	def __init__(self, session: Session) -> None:
		self.db: Session = session

	async def create_ocr_provider(self, provider: CreateOcrProvider) -> str:
		ocr_db: OcrProvider = OcrProvider(
			unique_name=provider.provider_id, display_name=provider.provider_name
		)

		self.db.add(ocr_db)
		self.db.commit()
		return str(ocr_db.id)

	async def get_ocr_provider(self, unique_name: str) -> ReadOcrProvider:
		ocr_db: OcrProvider = self.db.exec(
			select(OcrProvider).where(OcrProvider.unique_name == unique_name)
		).one()

		return ReadOcrProvider(
			id=str(ocr_db.id),
			unique_name=ocr_db.unique_name,
			display_name=ocr_db.display_name,
		)

	async def create_ocr_model(self, model: AddOcrAiModel) -> str:
		provider_id: UUID = self.db.exec(
			select(OcrProvider.id).where(OcrProvider.unique_name == model.provider_id)
		).one()

		model_db: OcrAiModel = OcrAiModel(
			unique_name=model.model_name, provider_id=provider_id
		)

		self.db.add(model_db)
		self.db.commit()
		return str(model_db.id)

	async def fetch_ocr_model(self, unique_name: str) -> ReadOcrModel:
		model_db: OcrAiModel = self.db.exec(
			select(OcrAiModel).where(OcrAiModel.unique_name == unique_name)
		).one()

		return ReadOcrModel(
			unique_name=model_db.unique_name,
			model_name=(
				model_db.display_name if model_db.display_name else model_db.unique_name
			),
			provider_id=model_db.ocr_provider.unique_name,
			provider_display_name=model_db.ocr_provider.display_name,
		)


class DemoOcrJobRepository:
	def __init__(self, session: Session) -> None:
		self.db_session: Session = session

	async def save_ocr_job(self, ocr_job: CreateOcrJob) -> OcrJob:
		campaign_id: UUID = self.db_session.exec(
			select(Campaign.id).where(
				Campaign.unique_name == ocr_job.campaign_unique_name
			)
		).one()

		scan_id: UUID = self.db_session.exec(
			select(PetitionScanEntity.id).where(
				PetitionScanEntity.file_name == ocr_job.petition_scan_filename
			)
		).one()

		ocr_provider_id: UUID = self.db_session.exec(
			select(OcrProvider.id).where(
				OcrProvider.unique_name == ocr_job.provider_unique_name
			)
		).one()

		task_id: UUID = self.db_session.exec(
			select(MatchingTaskEntity.id).where(
				MatchingTaskEntity.id == UUID(ocr_job.match_task_id)
			)
		).one()

		job: OcrJob = OcrJob(
			job_id=ocr_job.job_id,
			provider_id=ocr_provider_id,
			request_payload=ocr_job.request_payload,
			campaign_id=campaign_id,
			scan_id=scan_id,
			match_task_id=task_id,
		)

		db_ocr_job: OcrJob = OcrJob.model_validate(job)
		self.db_session.add(db_ocr_job)
		self.db_session.commit()
		self.db_session.refresh(db_ocr_job)

		return db_ocr_job

	async def update_ocr_job_status(self, ocr_job: UpdateOcrJobStatus) -> OcrJob:
		db_ocr_job: OcrJob | None = self.db_session.exec(
			select(OcrJob).where(OcrJob.job_id == ocr_job.job_id)
		).one()

		if not db_ocr_job:
			raise ValueError("Update failed: OCR job not found.")

		ocr_data = ocr_job.model_dump(exclude_unset=True)

		db_ocr_job.sqlmodel_update(ocr_data)
		self.db_session.add(db_ocr_job)
		self.db_session.commit()
		self.db_session.refresh(db_ocr_job)
		return db_ocr_job

	async def get_ocr_job_status(self, job_id: str) -> ReadOcrJobStatus:
		ocr_job: OcrJob | None = self.db_session.exec(
			select(OcrJob).where(OcrJob.job_id == job_id)
		).one()
		if not ocr_job:
			raise ValueError("Query failed: Cannot find OCR job from id.")

		return ReadOcrJobStatus(
			job_id=ocr_job.job_id,
			state=ocr_job.state,
			model_version=ocr_job.model_version,
			created_at=ocr_job.created_at,
			updated_at=ocr_job.updated_at,
			completed_at=ocr_job.updated_at,
			error_message=ocr_job.error_message,
			provider_id=str(ocr_job.provider_id),
		)

	async def save_results(
		self,
		campaign_id: uuid.UUID,
		document_id: uuid.UUID,
		ocr_job_id: uuid.UUID,
		results: Iterable[OcrResultItem],
	) -> Iterable[OcrResultItem]:
		task_id: UUID = self.db_session.exec(
			select(OcrJob.match_task_id).where(OcrJob.job_id == ocr_job_id)
		).one()

		result_data: list[OcrResult] = [
			OcrResult(
				file_name=item.file_name,
				page_num=item.page_num,
				row_num=item.row_num,
				ocr_name=item.ocr_entry.Name,
				ocr_address=item.ocr_entry.Address,
				ocr_date=item.ocr_entry.Date,
				ocr_ward=item.ocr_entry.Ward,
				campaign_id=campaign_id,
				document_id=document_id,
				ocr_job_id=ocr_job_id,
				matching_task_id=task_id,
			)
			for item in results
		]

		self.db_session.add_all(result_data)
		self.db_session.commit()

		return results

	async def fetch_results(self, campaign_id: str) -> Iterable[OcrResultItem]:
		campaign_uuid: UUID = self.db_session.exec(
			select(Campaign.id).where(Campaign.unique_name == campaign_id)
		).one()

		statement = select(OcrResult).where(OcrResult.campaign_id == campaign_uuid)
		result: Sequence[OcrResult] = self.db_session.exec(statement).all()

		items: list[OcrResultItem] = [
			OcrResultItem(
				campaign_id=campaign_id,
				file_name=item.file_name,
				page_num=item.page_num,
				row_num=item.row_num,
				ocr_entry=OCREntry(
					Name=item.ocr_name,
					Address=item.ocr_address,
					Date=item.ocr_date,
					Ward=item.ocr_ward,
				),
			)
			for item in result
		]

		return items


def get_ocr_job_repository(
	session: Session = Depends(get_db_session),
) -> OcrJobRepository:
	return DemoOcrJobRepository(session)
