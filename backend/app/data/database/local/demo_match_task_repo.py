import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
import structlog
from sqlmodel import Field, Session, SQLModel, select

from app.data.database.model.ocr_model import OcrAiModel, OcrJob
from app.data.database.model.schema import Campaign
from app.matching.match_repository import (
    CreateMatchingTask,
    MatchingStatus,
    MatchingTask,
    UpdateMatchingTask,
)

logger = structlog.get_logger(__name__)


class MatchingTaskEntity(SQLModel, table=True):
    __tablename__ = "matching_tasks"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
    ended_at: datetime | None = Field(default=None)
    status: MatchingStatus = Field(default=MatchingStatus.NOT_STARTED)
    status_message: str | None = Field(default=None)
    failure_message: str | None = Field(default=None)
    ocr_result_data: str | None = Field(default=None)
    campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")


class DemoMatchTaskRepository:

    def __init__(self, session: Session) -> None:
        self.db: Session = session

    def adapt_entity_to_matching_task(self, entity: MatchingTaskEntity) -> MatchingTask:

        return MatchingTask(
            id=str(entity.id),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            ended_at=entity.ended_at,
            status=entity.status,
            status_message=entity.status_message,
            failure_message=entity.failure_message,
            ocr_result_data=entity.ocr_result_data,
            campaign_id=str(entity.campaign_id),
        )

    async def register_matching_task(self, task: CreateMatchingTask) -> MatchingTask:

        campaign_id: UUID = self.db.exec(
            select(Campaign.id).where(Campaign.unique_name == task.campaign_id)
        ).one()

        entity: MatchingTaskEntity = MatchingTaskEntity(
            status_message=task.status_message,
            campaign_id=campaign_id,
        )

        db_entity: MatchingTaskEntity = MatchingTaskEntity.model_validate(entity)
        self.db.add(db_entity)
        self.db.commit()
        self.db.refresh(db_entity)

        return self.adapt_entity_to_matching_task(db_entity)

    async def update_matching_task_status(
        self, task: UpdateMatchingTask
    ) -> MatchingTask:

        db_entity: MatchingTaskEntity | None = self.db.get(
            MatchingTaskEntity, UUID(task.task_id)
        )

        if db_entity is None:
            raise LookupError("Unable to find matching task with associated id")

        db_entity.status = task.status
        db_entity.status_message = task.status_message
        db_entity.ended_at = task.ended_at
        db_entity.failure_message = task.failure_message
        db_entity.ocr_result_data = task.ocr_result_data
        db_entity.updated_at = task.updated_at

        self.db.add(db_entity)
        self.db.commit()
        self.db.refresh(db_entity)
        return self.adapt_entity_to_matching_task(db_entity)

    async def get_matching_task(self, task_id: str) -> MatchingTask:
        entry: MatchingTaskEntity | None = self.db.get(
            MatchingTaskEntity, UUID(task_id)
        )

        if not entry:
            raise LookupError(f"Failed to find matching task with id {task_id}")

        return self.adapt_entity_to_matching_task(entry)

    async def get_completed_task_for_campaign(
        self, campaign_id: str
    ) -> Iterable[MatchingTask]:

        statement = (
            select(MatchingTaskEntity)
            .where(MatchingTaskEntity.status == MatchingStatus.COMPLETED)
            .join(Campaign)
            .where(Campaign.unique_name == campaign_id)
        )

        tasks: Sequence[MatchingTaskEntity] = self.db.exec(statement).all()

        return [self.adapt_entity_to_matching_task(task) for task in tasks]
