import uuid
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, Session, SQLModel, select
from sqlmodel.orm.session import Session

from app.data.database.model.schema import Campaign
from app.matching.match_repository import (
	CreateColumnSpec,
	CreateMatchResult,
	ReadColumnSpec,
	ReadMatchResult,
)


class MatchResultColumns(SQLModel, table=True):
	__tablename__ = "match_column_specs"
	id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	name: str = Field()
	data_type: str = Field()
	position_index: int = Field()
	is_sortable: bool = Field(default=False)
	campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")


class DemoMatchResult(SQLModel, table=True):
	__tablename__ = "demo_match_results"
	id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
	registered_name: str | None = Field()
	ocr_name: str | None = Field()
	registered_address: str | None = Field()
	ocr_address: str | None = Field()
	ocr_date: str | None = Field()
	ocr_ward: int | None = Field()
	match_score: float = Field()
	fuzzy_match_threshold: float = Field()
	petition_page_number: int = Field()
	petition_row_number: int = Field()
	petition_file_name: str = Field()
	campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")
	ocr_result_id: uuid.UUID = Field(foreign_key="ocr_results.id")
	# document_id: uuid.UUID = Field(foreign_key="petition_scans.id")


class MatchResult(SQLModel, table=True):
	__tablename__ = "match_results"
	id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime | None = Field(
		default=None,
		sa_column=sa.Column(
			sa.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
		),
	)
	fuzzy_match_threshold: float = Field()
	serialised_result: str = Field()
	column_spec_id: uuid.UUID = Field(foreign_key="match_column_specs.id")
	ocr_result_id: uuid.UUID = Field(foreign_key="ocr_results.id")
	campaign_id: uuid.UUID = Field(foreign_key="campaigns.id")


class DemoEntryMatchRepository:
	def __init__(self, session: Session) -> None:
		self.db: Session = session

	async def create_column_spec(
		self, column_spec: CreateColumnSpec
	) -> str | uuid.UUID:
		campaign_id: UUID = self.db.exec(
			select(Campaign.id).where(Campaign.unique_name == column_spec.campaign_id)
		).one()

		spec: MatchResultColumns = MatchResultColumns(
			name=column_spec.name,
			data_type=column_spec.data_type,
			position_index=column_spec.position_index,
			is_sortable=column_spec.is_sortable,
			campaign_id=campaign_id,
		)
		db_spec: MatchResultColumns = MatchResultColumns.model_validate(spec)
		self.db.add(db_spec)
		self.db.commit()
		self.db.refresh(db_spec)
		return db_spec.id

	async def fetch_column_spec(self, campaign_id: str) -> Iterable[ReadColumnSpec]:
		statement = (
			select(MatchResultColumns)
			.join(Campaign)
			.where(Campaign.unique_name == campaign_id)
		)
		result: Sequence[MatchResultColumns] = self.db.exec(statement).all()
		specs: list[ReadColumnSpec] = [
			ReadColumnSpec(
				name=s.name,
				data_type=s.data_type,
				position_index=s.position_index,
				is_sortable=s.is_sortable,
				campaign_id=campaign_id,
			)
			for s in result
		]
		specs.sort(key=lambda spec: spec.position_index)
		return specs

	async def save_match_results(self, matches: Iterable[CreateMatchResult]) -> None:
		items: list[DemoMatchResult] = []

		campaign_id: UUID | None = None

		for m in matches:
			if campaign_id is None:
				campaign_id = self.db.exec(
					select(Campaign.id).where(Campaign.unique_name == m.campaign_id)
				).one()

			record: DemoMatchResult = DemoMatchResult(
				fuzzy_match_threshold=m.fuzzy_match_threshold,
				registered_name=str(m.row_values["registered_name"]),
				ocr_name=str(m.row_values["ocr_name"]),
				registered_address=str(m.row_values["registered_address"]),
				ocr_address=str(m.row_values["ocr_address"]),
				ocr_date=str(m.row_values["ocr_date"]),
				ocr_ward=(
					int(str(m.row_values["ocr_ward"]))
					if m.row_values.get("ocr_ward")
					else None
				),
				match_score=m.match_score,
				petition_page_number=m.petition_row_number,
				petition_row_number=m.petition_row_number,
				petition_file_name=m.petition_file_name,
				campaign_id=campaign_id,
				ocr_result_id=UUID(m.ocr_result_id),
			)

			db_record: DemoMatchResult = DemoMatchResult.model_validate(record)
			items.append(db_record)

		self.db.add_all(items)
		self.db.commit()

	async def fetch_match_results(self, campaign_id: str) -> Iterable[ReadMatchResult]:
		statement = (
			select(DemoMatchResult)
			.join(Campaign)
			.where(Campaign.unique_name == campaign_id)
		)
		result: Sequence[DemoMatchResult] = self.db.exec(statement).all()

		matches: list[ReadMatchResult] = []
		for r in result:
			row_values: dict[str, str | int | float | bool | None] = {
				"registered_name": r.registered_name,
				"ocr_name": r.ocr_name,
				"registered_address": r.registered_address,
				"ocr_address": r.ocr_address,
				"ocr_date": r.ocr_date,
				"ocr_ward": r.ocr_ward,
			}
			item: ReadMatchResult = ReadMatchResult(
				fuzzy_match_threshold=r.fuzzy_match_threshold,
				row_values=row_values,
				match_score=r.match_score,
				petition_page_number=r.petition_row_number,
				petition_row_number=r.petition_row_number,
				petition_file_name=r.petition_file_name,
				campaign_id=campaign_id,
				ocr_result_id=str(r.ocr_result_id),
			)
			matches.append(item)

		return matches
