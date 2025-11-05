import pandas as pd
from app.dependencies import demo_petition_path, oauth2_scheme
from app.fuzzy_match_helper import create_ocr_matched_df, create_select_voter_records
from app.ocr.ocr_helper import OCR_COLUMNS, create_ocr_df
from app.schemas import OcrMatchResponse, OcrProviderPayload
from app.settings.settings_repo import (
    GeminiAiConfig,
    MistralAiConfig,
    OpenAiConfig,
    override_settings,
)
from app.voter.voter_processor import DEMO_VOTER_RECORD_STATE
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pandas import DataFrame

router: APIRouter = APIRouter(tags=["Workspace"], prefix="/workspace")


@router.post(path="/ocr/demo", tags=["OCR", "Demo"], response_model=OcrMatchResponse)
async def ocr_demo(ocr_provider: OcrProviderPayload | None = None):
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
        config: OpenAiConfig | GeminiAiConfig | MistralAiConfig
        match ocr_provider.provider_name:
            case "open_ai":
                config = OpenAiConfig(
                    api_key=ocr_provider.api_key, model=ocr_provider.provider_model
                )
            case "mistral_ai":
                config = MistralAiConfig(
                    api_key=ocr_provider.api_key, model=ocr_provider.provider_model
                )
            case "gemini_ai":
                config = GeminiAiConfig(
                    api_key=ocr_provider.api_key, model=ocr_provider.provider_model
                )
            case _:
                raise HTTPException(
                    status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"Provider name {ocr_provider.provider_name} is invalid. Please use an authorised OCR provider.",
                )

        override_settings(config)

    df_list: list[DataFrame] = []

    for file in demo_petition_path.iterdir():
        if file.is_file():
            df_list.append(create_ocr_df(filedir=file.parent.name, filename=file.name))

    ocr_df = pd.concat(df_list)

    selected_voters = create_select_voter_records(DEMO_VOTER_RECORD_STATE.voters_df)
    ocr_matched_df = create_ocr_matched_df(
        ocr_df,
        select_voter_records=selected_voters,
    )
    return {"results": ocr_matched_df.to_dict("records"), "stats": {}}


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
