import json
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
import structlog
from sqlalchemy.engine.result import ScalarResult
from sqlmodel import Field, Session, SQLModel, select
from sqlmodel.orm.session import Session

from app.data.database.local.demo_match_task_repo import MatchingTaskEntity
from app.data.database.model.ocr_model import OcrJob
from app.data.database.model.scanned_petition_model import PetitionCropAssetEntity
from app.data.database.model.schema import Campaign
from app.ocr.ocr_manager import OcrResult, ReadOcrResult
from app.ocr.ocr_result_repo import CreateOcrResult

logger = structlog.get_logger(__name__)


class OcrResultEntity(SQLModel, table=True):
	__tablename__ = "ocr_results"
	id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	page_num: int = Field()
	row_num: int = Field()
	results_json: str = Field()
	# FK
	region_id: UUID = Field(foreign_key="regions.id")
	ocr_job_id: UUID = Field(foreign_key="ocr_jobs.id")
	campaign_id: UUID = Field(foreign_key="campaigns.id")
	document_id: UUID = Field(foreign_key="petition_scans.id")
	task_id: UUID = Field(foreign_key="matching_tasks.id")


class DemoOcrResultsRepo:
	def __init__(self, session: Session) -> None:
		self.db: Session = session

	def _create_ocr_result_entity(
		self, result_data: CreateOcrResult
	) -> OcrResultEntity:
		task: MatchingTaskEntity | None = self.db.get(
			MatchingTaskEntity, UUID(result_data.task_id)
		)
		assert task, "No task found in database"
		# TODO reduce queries with joins
		result: OcrResult = result_data.ocr_result
		campaign: Campaign | None = self.db.get(Campaign, task.campaign_id)

		ocr_job: OcrJob = self.db.exec(
			select(OcrJob).where(OcrJob.job_id == result_data.ocr_job_id)
		).one()

		logger.debug(f"Result data: {result.model_dump_json()}")
		logger.debug(f"Scan id: {ocr_job.scan_id}")

		cropped: PetitionCropAssetEntity = self.db.exec(
			select(PetitionCropAssetEntity).where(
				PetitionCropAssetEntity.petition_scan_id == ocr_job.scan_id,
				PetitionCropAssetEntity.sheet_number == result.page_num,
			)
		).one()
		return OcrResultEntity(
			campaign_id=campaign.id,
			region_id=campaign.region_id,
			task_id=task.id,
			ocr_job_id=ocr_job.id,
			document_id=cropped.petition_scan_id,
			page_num=result.page_num,
			row_num=result.row_num,
			results_json=json.dumps(result.result_parts),
		)

	async def save_ocr_result(self, result_data: CreateOcrResult) -> str:
		db_result: OcrResultEntity = self._create_ocr_result_entity(result_data)
		self.db.add(db_result)
		self.db.commit()
		return str(db_result.id)

	async def save_ocr_results(self, results: Iterable[CreateOcrResult]) -> None:
		db_entries: list[OcrResultEntity] = [
			self._create_ocr_result_entity(r) for r in results
		]
		self.db.add_all(db_entries)
		self.db.commit()

	async def fetch_ocr_results_by_task(self, task_id: str) -> Iterable[ReadOcrResult]:
		db_results: ScalarResult[OcrResultEntity] = self.db.exec(
			select(OcrResultEntity).where(OcrResultEntity.task_id == UUID(task_id))
		)

		results: list[ReadOcrResult] = [
			ReadOcrResult(
				page_num=r.page_num,
				row_num=r.row_num,
				result_parts=json.loads(r.results_json),
			)
			for r in db_results
		]

		logger.debug(f"Found {len(results)} ocr results from task")

		return results
