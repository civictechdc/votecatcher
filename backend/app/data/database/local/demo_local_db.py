import shutil
import uuid
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

import pandas as pd
import structlog
from pandas import DataFrame
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, select, text

from app.data.database.local.demo_match_repo import *
from app.data.database.local.demo_match_task_repo import *
from app.data.database.local.demo_ocr_results import *
from app.data.database.model.ocr_model import *
from app.data.database.model.ocr_model import OcrAiModel, OcrProvider
from app.data.database.model.registered_voter_model import (
	CreateDemoFakeRegisteredVoter,
	DemoFakeRegisteredVoter,
)
from app.data.database.model.scanned_petition_model import *
from app.data.database.model.schema import Campaign, Region
from app.settings.env_settings import AppSettings, get_settings

logger = structlog.get_logger(__name__)

db_dir: Path = (
	Path(__file__).parent.parent.parent.parent.parent / "runtime" / "database"
)

if get_settings().clear_runtime_on_launch and db_dir.parent.exists():
	logger.info("Clearing runtime database directory on launch")
	shutil.rmtree(db_dir.parent)

if db_dir.exists():
	shutil.rmtree(db_dir)
db_dir.mkdir(parents=True, exist_ok=True)


def uuid_str_factory() -> str:
	return str(uuid.uuid4())


def get_sqlite_url() -> str:
	settings: AppSettings = get_settings()
	db_file = settings.runtime_dir / "database" / "local_db.db"
	return f"sqlite:///{db_file}"


logger.debug(f"Getter file created at: {get_sqlite_url()}")
db_file: Path = db_dir / "local_db.db"
sqlite_url: str = f"sqlite:///{db_file}"
engine: Engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)


def create_db_and_tables():
	SQLModel.metadata.create_all(engine)
	with engine.connect() as connection:
		# Needed by SQLite to enable foreign key support
		connection.execute(text("PRAGMA foreign_keys=ON"))


def get_db_session() -> Generator[Session, Any]:
	with Session(engine) as session:
		yield session


def create_demo_records():
	with Session(engine) as session:
		region: Region = Region(
			region_key="demo", region_name="Demo region", country_code="xx"
		)
		session.add(region)
		session.commit()

		campaign: Campaign = Campaign(
			unique_name="demo",
			year="2025",
			title="Demo campaign",
			description="This is a demo campaign to show the features of the app",
			region_id=region.id,
		)
		session.add(campaign)
		session.commit()

		ocr_provider: OcrProvider = OcrProvider(
			unique_name="open_ai", display_name="Open AI"
		)
		session.add(ocr_provider)
		session.commit()

		ocr_model: OcrAiModel = OcrAiModel(
			display_name="GPT-4o Mini",
			unique_name="gpt-4o-mini",
			provider_id=ocr_provider.id,
		)
		session.add(ocr_model)
		session.commit()

		[
			MatchResultColumns(
				name="Name",
				data_type="str",
				position_index=0,
				is_sortable=True,
				campaign_id=campaign.id,
			)
		]


class LocalRegisteredVoterRepository:
	def __init__(self, session: Session) -> None:
		self.db: Session = session

	def _create_dataframe(self) -> DataFrame: ...

	async def save_registered_voter_list(
		self, region_id: uuid.UUID, file_path: Path
	) -> None:
		file_extension: str = file_path.suffix.casefold()

		logger.debug(f"extension: {file_extension}")
		voter_data: DataFrame | None = None
		if file_extension == ".xls" or file_extension == ".xlsx":
			voter_data = pd.read_excel(file_path, dtype=pd.StringDtype())
		elif file_extension == ".csv":
			voter_data = pd.read_csv(file_path, dtype=pd.StringDtype())
		else:
			raise ValueError(
				f"File: {file_path} is not a valid format. Please use .xlsx, .xsl or .csv files."
			)

		assert voter_data is not None, "Voter data frame is unexpectedly null"

		voter_records: list[CreateDemoFakeRegisteredVoter] = []

		for _idx, row in voter_data.iterrows():
			new_voter: CreateDemoFakeRegisteredVoter = CreateDemoFakeRegisteredVoter(
				first_name=row["First_Name"],
				last_name=row["Last_Name"],
				street_number=row["Street_Number"],
				street_name=row["Street_Name"],
				street_type=row["Street_Type"],
				street_dir_suffix=row["Street_Dir_Suffix"],
				file_name=file_path.name,
				local_path=str(file_path),
				region_id=region_id,
			)
			voter_records.append(new_voter)

		db_voters: list[DemoFakeRegisteredVoter] = [
			DemoFakeRegisteredVoter.model_validate(new_voter)
			for new_voter in voter_records
		]
		self.db.add_all(db_voters)
		self.db.commit()

	async def get_registered_voter_data(self, region_id: uuid.UUID) -> DataFrame:
		statement = select(DemoFakeRegisteredVoter).where(
			DemoFakeRegisteredVoter.region_id == region_id
		)
		registered_voters: Sequence[DemoFakeRegisteredVoter] = self.db.exec(
			statement
		).all()

		# TODO handle empty results

		voter_items: list[dict[str, str]] = []
		for voter in registered_voters:
			voter_items.append(
				{
					"First_Name": voter.first_name,
					"Last_Name": voter.last_name,
					"Street_Number": voter.street_number,
					"Street_Name": voter.street_name,
					"Street_Type": voter.street_type,
					"Street_Dir_Suffix": voter.street_dir_suffix,
				}
			)

		df: DataFrame = pd.DataFrame(data=voter_items)
		df["Full Name"] = df[["First_Name", "Last_Name"]].agg(" ".join, axis=1)
		df["Full Address"] = df[
			["Street_Number", "Street_Name", "Street_Type", "Street_Dir_Suffix"]
		].agg(" ".join, axis=1)

		return df.astype(
			dtype={
				"Full Name": pd.StringDtype(),
				"Full Address": pd.StringDtype(),
			}
		)

	async def get_registered_voter_data_by_region_key(
		self, region_key: str
	) -> DataFrame:
		statement = select(Region.id).where(Region.region_key == region_key)
		region_id: UUID = self.db.exec(statement).one()
		return await self.get_registered_voter_data(region_id)
