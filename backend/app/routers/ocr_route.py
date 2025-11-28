import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any, Iterable

import pandas as pd
import structlog
from app.data.demo_data import IN_MEMORY_DEMO_CAMPAIGN_ID
from app.data.memory_db import get_memory_db
from app.dependencies import demo_petition_path, oauth2_scheme
from app.logging.app_logger import AppLogger
from app.matching.fuzzy_match_helper import (
    create_ocr_match_result_response,
    create_ocr_matched_df,
    create_select_voter_records,
    perform_fuzzy_matching,
)
from app.matching.response_adapter import OcrMatchResults
from app.ocr.batching.batch_handler import (
    get_ocr_provider_config,
    get_ocr_results,
    observe_batch_job_status,
)
from app.ocr.batching.batch_ocr_client import BatchJobStatus, JobStatus
from app.ocr.data.ocr_repository import OcrResultItem
from app.ocr.ocr_helper import (
    OCR_COLUMNS,
    create_batched_ocr_job,
    create_ocr_df,
    create_ocr_results,
    emit_batch_job_status,
)
from app.ocr.response_types import MatchingJobStatusProgress
from app.schemas import OcrMatchResponse, OcrProviderPayload
from app.voter.voter_processor import DEMO_VOTER_RECORD_STATE, RegisteredVotersData
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pandas import DataFrame
from pandas.core.frame import DataFrame
from sse_starlette.sse import EventSourceResponse
from starlette.status import HTTP_404_NOT_FOUND

logger = structlog.get_logger(__name__)

router: APIRouter = APIRouter(tags=["Workspace"], prefix="/workspace")


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

    files: list[Path] = [file for file in demo_petition_path.iterdir()]
    df_list: list[DataFrame] = await create_ocr_results(files)
    ocr_df: DataFrame = pd.concat(df_list)

    selected_voters: DataFrame = create_select_voter_records(
        voter_records=DEMO_VOTER_RECORD_STATE.voters_df
    )
    ocr_matched_df: DataFrame = create_ocr_matched_df(
        ocr_df,
        select_voter_records=selected_voters,
    )

    for col in ocr_matched_df.columns:
        ocr_matched_df["data_type"] = ocr_matched_df[col].dtype

    logger.debug(f"Column types: {ocr_matched_df.dtypes}")

    return {"results": ocr_matched_df.to_dict("records"), "stats": {}}


@router.post("/ocr/batch", tags=["OCR"])
async def start_batch_ocr(
    db: Annotated[dict[str, Any], Depends(get_memory_db)],
    ocr_provider: OcrProviderPayload,
) -> BatchJobStatus:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/ocr/demo_batch", tags=["OCR", "Demo"])
async def start_demo_batch_ocr(
    db: Annotated[dict[str, Any], Depends(get_memory_db)],
    ocr_provider: OcrProviderPayload,
) -> MatchingJobStatusProgress:

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

    files: list[Path] = [file for file in demo_petition_path.iterdir()]
    ocr_status: MatchingJobStatusProgress = await create_batched_ocr_job(
        campaign_id=IN_MEMORY_DEMO_CAMPAIGN_ID, files=files
    )

    db[ocr_status.ocr_job_id] = ocr_status
    return ocr_status


@router.get("/ocr/batch/{job_id}/status", tags=["OCR"])
async def get_batch_status(
    job_id: str,
    db: Annotated[dict[str, Any], Depends(get_memory_db)],
) -> EventSourceResponse:
    """Stream batch job status updates"""
    if not job_id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Could not find job id for value {job_id}",
        )
    return EventSourceResponse(content=emit_batch_job_status(job_id=job_id))


@router.get(path="/ocr/batch/{job_id}/snapshot", tags=["OCR", "API"])
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


@router.get(path="/ocr/results/demo/{job_id}", tags=["OCR, Demo"])
async def get_batch_result(
    job_id: str,
    db: Annotated[dict[str, Any], Depends(get_memory_db)],
) -> OcrMatchResponse:

    DEMO_VOTER_RECORD_STATE: RegisteredVotersData | None = db.get("voter_list")

    if not DEMO_VOTER_RECORD_STATE:
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            detail="No voter records found to match against. Please upload and try again.",
        )

    try:
        ocr_results: Iterable[OcrResultItem] = await get_ocr_results(
            IN_MEMORY_DEMO_CAMPAIGN_ID
        )

        DEMO_VOTER_RECORD_STATE.voters_df.info()
        logger.debug(f"DEMO VOTER DATA: {DEMO_VOTER_RECORD_STATE.voters_df.head()}")

        fuzzy_match_df: DataFrame = await perform_fuzzy_matching(
            ocr_results=ocr_results, voter_records=DEMO_VOTER_RECORD_STATE.voters_df
        )

        logger.debug(f"Fuzzy match results created: {len(fuzzy_match_df)}")
        fuzzy_match_df.info()

        response: OcrMatchResults = create_ocr_match_result_response(fuzzy_match_df)
        return OcrMatchResponse(results=response)

    except Exception as e:
        logger.error(f"Error with: {e}")
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
