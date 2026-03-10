import asyncio
import random
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
import structlog
from faker import Faker
from fastapi import APIRouter, Depends, HTTPException, status
from pandas import DataFrame
from pandas.core.frame import DataFrame
from sse_starlette.sse import EventSourceResponse
from starlette.status import HTTP_404_NOT_FOUND

from app.campaign.campaign_repository import CampaignRepository
from app.data.memory_db import get_memory_db
from app.dependencies import (
	demo_petition_path,  # get_ocr_job_repository,
	get_campaign_repository,
	get_file_repository,
	get_matching_results_repository,
	get_matching_task_monitor,
	get_matching_task_repository,
	get_ocr_handler,
	get_ocr_results_repository,
	get_scanned_documents_repository,
)
from app.events.matching_task_events import MatchingTaskMonitor
from app.files.file_repository import (
	ReadPetitionScan,
	RegisteredVoterRepository,
	ScannedPetitionRepository,
)
from app.matching.fuzzy_match_helper import (
	create_ocr_matched_df,
	create_select_voter_records,
	perform_fuzzy_matching,
)
from app.matching.match_repository import (
	CreateMatchingTask,
	EntryMatchRepository,
	MatchingStatus,
	MatchingTask,
	MatchTaskRepository,
	UpdateMatchingTask,
)
from app.matching.response_adapter import (
	OcrMatchColumnSpec,
	OcrMatchResults,
	OcrMatchRow,
	OcrMatchValueItem,
	create_ocr_match_result_response,
)
from app.ocr.batching.batch_handler import (
	get_ocr_provider_config,
)
from app.ocr.batching.batch_ocr_client import BatchJobStatus
from app.ocr.ocr_helper import (
	create_batched_ocr_job,
	create_ocr_results,
	emit_matching_job_status,
)
from app.ocr.ocr_manager import OcrHandler
from app.ocr.ocr_result_repo import OcrResultRepository
from app.ocr.response_types import MatchingJobStatusProgress
from app.schemas import OcrMatchResponse, OcrProviderPayload
from app.settings.env_settings import AppSettings, get_settings
from app.voter.voter_processor import RegisteredVotersData

logger = structlog.get_logger(__name__)

router: APIRouter = APIRouter(tags=["Workspace"], prefix="/workspace")


@router.get("/ocr/simulate/{task_id}", response_model=OcrMatchResponse)
async def simulate_ocr_results(task_id: str):
	"""
	Generate simulated OCR match results for testing.

	No database or OCR operations are performed.
	Returns realistic mock data following the OcrMatchResults schema.
	"""
	fake = Faker()
	random.seed(hash(task_id))

	columns = [
		OcrMatchColumnSpec(name="ocr_name", position_idx=0, data_type="string"),
		OcrMatchColumnSpec(name="ocr_address", position_idx=1, data_type="string"),
		OcrMatchColumnSpec(name="matched_name", position_idx=2, data_type="string"),
		OcrMatchColumnSpec(name="matched_address", position_idx=3, data_type="string"),
		OcrMatchColumnSpec(name="match_score", position_idx=4, data_type="float"),
		OcrMatchColumnSpec(name="ocr_date", position_idx=5, data_type="string"),
		OcrMatchColumnSpec(name="ocr_ward", position_idx=6, data_type="int"),
	]

	row_count = random.randint(50, 200)
	rows = []

	for i in range(row_count):
		ocr_name = fake.name()
		ocr_address = fake.address().replace("\n", ", ")
		match_score = round(random.uniform(0.5, 1.0), 3)

		if random.random() > 0.3:
			matched_name = ocr_name
			matched_address = ocr_address
		else:
			matched_name = fake.name()
			matched_address = fake.address().replace("\n", ", ")

		values = [
			OcrMatchValueItem(value=ocr_name, column_idx=0, data_type="string"),
			OcrMatchValueItem(value=ocr_address, column_idx=1, data_type="string"),
			OcrMatchValueItem(value=matched_name, column_idx=2, data_type="string"),
			OcrMatchValueItem(value=matched_address, column_idx=3, data_type="string"),
			OcrMatchValueItem(value=str(match_score), column_idx=4, data_type="float"),
			OcrMatchValueItem(value=fake.date(), column_idx=5, data_type="string"),
			OcrMatchValueItem(
				value=str(random.randint(1, 8)), column_idx=6, data_type="int"
			),
		]
		rows.append(OcrMatchRow(row_idx=i, values=values))

	result = OcrMatchResults(column_data=columns, result_data=rows)

	return OcrMatchResponse(
		results=result,
		stats={
			"total_rows": row_count,
			"simulated": True,
			"task_id": task_id,
		},
	)


@router.post(path="/ocr/demo", tags=["OCR", "Demo"], response_model=OcrMatchResponse)
async def ocr_demo(
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
	ocr_provider: OcrProviderPayload | None = None,
):
	logger.debug(f"demo petition path ${demo_petition_path.exists()}")
	DEMO_VOTER_RECORD_STATE: Any | None = db.get("voter_list")

	if not demo_petition_path.exists():
		raise HTTPException(
			status.HTTP_412_PRECONDITION_FAILED,
			detail="No petition scans found to perform matching. Please upload and try again.",
		)

	if not DEMO_VOTER_RECORD_STATE:
		raise HTTPException(
			status.HTTP_412_PRECONDITION_FAILED,
			detail="No voter records found to match against. Please upload and try again.",
		)

	# Temporary shortcut to set the OCR provider without config
	if ocr_provider:
		try:
			get_ocr_provider_config(
				provider_name=ocr_provider.provider_name,
				api_key=ocr_provider.api_key,
				model_name=ocr_provider.provider_model,
			)
		except Exception as e:
			raise HTTPException(
				status.HTTP_406_NOT_ACCEPTABLE,
				detail=f"{e}",
			)

	df_list: list[DataFrame] = []

	"""
    for file in demo_petition_path.iterdir():
        if file.is_file():
            ocr_df: DataFrame = await create_ocr_df(
                filedir=file.parent.name, filename=file.name
            )
            df_list.append(ocr_df)

    ocr_df = pd.concat(df_list)
    """

	files: list[Path] = list(demo_petition_path.iterdir())
	df_list: list[DataFrame] = await create_ocr_results(files)
	ocr_df: DataFrame = pd.concat(df_list)

	selected_voters: DataFrame = create_select_voter_records(
		voter_records=DEMO_VOTER_RECORD_STATE.voters_df
	)
	ocr_matched_df: DataFrame = create_ocr_matched_df(
		ocr_df,
		select_voter_records=selected_voters,
	)

	logger.debug(f"Column types: {ocr_matched_df.dtypes}")

	# Convert to proper response format using response adapter
	match_response = create_ocr_match_result_response(ocr_matched_df)
	return {"results": match_response, "stats": {}}


@router.post("/ocr/batch", tags=["OCR"])
async def start_batch_ocr(
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
	ocr_provider: OcrProviderPayload,
) -> BatchJobStatus:
	raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/ocr/demo_batch", tags=["OCR", "Demo"])
async def start_demo_batch_ocr(
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
	settings: Annotated[AppSettings, Depends(get_settings)],
	campaign_repo: Annotated[CampaignRepository, Depends(get_campaign_repository)],
	file_repo: Annotated[
		ScannedPetitionRepository, Depends(get_scanned_documents_repository)
	],
	voter_repo: Annotated[RegisteredVoterRepository, Depends(get_file_repository)],
	matching_task_repo: Annotated[
		MatchTaskRepository, Depends(get_matching_task_repository)
	],
	matching_task_monitor: Annotated[
		MatchingTaskMonitor, Depends(get_matching_task_repository)
	],
	ocr_handler: Annotated[OcrHandler, Depends(get_ocr_handler)],
	ocr_provider: OcrProviderPayload,
) -> MatchingJobStatusProgress:
	logger.debug(f"demo petition path ${demo_petition_path.exists()}")
	DEMO_VOTER_RECORD_STATE: Any | None = db.get("voter_list")

	demo_campaign, voter_data = await asyncio.gather(
		campaign_repo.fetch_campaign("demo"),
		voter_repo.get_registered_voter_data_by_region_key("demo"),
	)

	file_scans: list[ReadPetitionScan] = await file_repo.get_scanned_petitions(
		demo_campaign.unique_name
	)

	if not demo_petition_path.exists():
		raise HTTPException(
			status.HTTP_412_PRECONDITION_FAILED,
			detail="No petition scans found to perform matching. Please upload and try again.",
		)

	if not DEMO_VOTER_RECORD_STATE:
		raise HTTPException(
			status.HTTP_412_PRECONDITION_FAILED,
			detail="No voter records found to match against. Please upload and try again.",
		)

	if ocr_provider:
		try:
			provider_config = get_ocr_provider_config(
				provider_name=ocr_provider.provider_name,
				api_key=ocr_provider.api_key,
				model_name=ocr_provider.provider_model,
			)
		except Exception as e:
			raise HTTPException(
				status.HTTP_406_NOT_ACCEPTABLE,
				detail=f"{e}",
			)

	task: MatchingTask = await matching_task_repo.register_matching_task(
		CreateMatchingTask(campaign_id=demo_campaign.unique_name)
	)

	cropped_img_dest: Path = settings.local_campaign_base_dir().joinpath(
		settings.crop_dir
	)

	ocr_status: MatchingJobStatusProgress = await create_batched_ocr_job(
		campaign_data=demo_campaign,
		scans=file_scans,
		scan_repo=file_repo,
		crop_dir=cropped_img_dest,
		task_id=task.id,
		ocr_handler=ocr_handler,
		ocr_provider_id=provider_config.name,
	)

	# db[ocr_status.ocr_job_id] = ocr_status
	return ocr_status


@router.get("/ocr/batch/{task_id}/status", tags=["OCR"])
async def get_batch_status(
	task_id: str,
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
	matching_task_monitor: MatchingTaskMonitor = Depends(get_matching_task_monitor),
) -> EventSourceResponse:
	"""Stream batch job status updates"""
	if not task_id:
		raise HTTPException(
			status_code=HTTP_404_NOT_FOUND,
			detail=f"Could not find job id for value {task_id}",
		)

	# return EventSourceResponse(content=matching_task_monitor.monitor_job(task_id=job_id))
	return EventSourceResponse(
		content=emit_matching_job_status(
			task_id=task_id, matching_task_monitor=matching_task_monitor
		)
	)


@router.get(path="/ocr/batch/{task_id}/snapshot", tags=["OCR", "API"])
async def get_batch_status_json(
	job_id: str,
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
) -> MatchingJobStatusProgress:
	"""Return current job snapshot as JSON (not SSE)."""
	snapshot = db.get(job_id)
	if snapshot is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
		)
	return snapshot


@router.get(path="/ocr/results/demo/{task_id}", tags=["OCR, Demo"])
async def get_batch_result(
	match_task_repo: Annotated[
		MatchTaskRepository, Depends(get_matching_task_repository)
	],
	match_task_monitor: Annotated[
		MatchingTaskMonitor, Depends(get_matching_task_monitor)
	],
	match_result_repo: Annotated[
		EntryMatchRepository, Depends(get_matching_results_repository)
	],
	ocr_result_repo: Annotated[
		OcrResultRepository, Depends(get_ocr_results_repository)
	],
	registered_voter_repo: Annotated[
		RegisteredVoterRepository, Depends(get_file_repository)
	],
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
	task_id: str,
) -> OcrMatchResponse:
	DEMO_VOTER_RECORD_STATE: RegisteredVotersData | None = db.get("voter_list")

	if not DEMO_VOTER_RECORD_STATE:
		raise HTTPException(
			status.HTTP_412_PRECONDITION_FAILED,
			detail="No voter records found to match against. Please upload and try again.",
		)

	task: MatchingTask = await match_task_repo.get_matching_task(task_id)

	try:
		voters_df, results, columns = await asyncio.gather(
			registered_voter_repo.get_registered_voter_data_by_region_key("demo"),
			ocr_result_repo.fetch_ocr_results_by_task(task_id),
			match_result_repo.fetch_column_spec("demo"),
		)

		# ocr_results: Iterable[OcrResultItem] = await get_ocr_results(
		# IN_MEMORY_DEMO_CAMPAIGN_ID
		# )

		DEMO_VOTER_RECORD_STATE.voters_df.info()
		logger.debug(f"DEMO VOTER DATA: {DEMO_VOTER_RECORD_STATE.voters_df.head()}")

		_ = await match_task_monitor.publish_updated_task_status(
			UpdateMatchingTask(
				task_id=task.id,
				status=MatchingStatus.MATCHING,
				status_message="Performing fuzzy matching on OCR results",
			)
		)

		fuzzy_match_df: DataFrame = await perform_fuzzy_matching(
			ocr_results=results, voter_records=voters_df
		)

		logger.debug(f"Fuzzy match results created: {len(fuzzy_match_df)}")
		fuzzy_match_df.info()

		response: OcrMatchResults = create_ocr_match_result_response(fuzzy_match_df)
		_ = await match_task_monitor.publish_updated_task_status(
			UpdateMatchingTask(
				task_id=task.id,
				status=MatchingStatus.COMPLETED,
				status_message=f"Matching completed successfully for {len(fuzzy_match_df)} records",
			)
		)
		return OcrMatchResponse(results=response)

	except Exception as e:
		logger.error(f"Error with: {e}")
		_ = await match_task_monitor.publish_updated_task_status(
			UpdateMatchingTask(
				task_id=task.id,
				status=MatchingStatus.MATCHING_FAILED,
				status_message=f"Matching failed with error: {e}",
			)
		)
		raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/ocr/batch/{job_id}/result", tags=["OCR"])
async def get_batch_result(
	job_id: str,
	db: Annotated[dict[str, Any], Depends(get_memory_db)],
) -> OcrMatchResponse:
	raise HTTPException(
		status_code=status.HTTP_501_NOT_IMPLEMENTED,
	)


"""
@router.post(path="/ocr", tags=["OCR"])
async def ocr(
    response: Response, token: Annotated[OAuth2PasswordBearer, Depends(oauth2_scheme)]
):

    # Triggers the OCR process on the uploaded petition signatures PDF file.


    if not os.path.exists("temp/ballot.pdf"):
        logger.error("No PDF file found for petition signatures")
        response.status_code = 400
        return {"error": "No PDF file found for petition signatures"}
    if app.state.voter_records_df is None:
        logger.error("No voter records file found")
        response.status_code = 400
        return {"error": "No voter records file found"}
    logger.info("Starting OCR processing...")
    # Process files if in processing state
    logger.info("Converting PDF to images...")

    ocr_df: DataFrame = create_ocr_df(filedir="temp", filename="ballot.pdf")

    logger.info("Compiling Voter Record Data...")

    select_voter_records = create_select_voter_records(app.state.voter_records_df)

    logger.info("Matching petition signatures to voter records...")

    ocr_matched_df = create_ocr_matched_df(
        ocr_df, select_voter_records, threshold=config["BASE_THRESHOLD"]
    )
    response.headers["Content-Type"] = "application/json"
    return {"data": ocr_matched_df.to_dict(orient="records"), "stats": {}}
"""
