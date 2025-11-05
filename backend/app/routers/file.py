import os
import shutil
from enum import Enum
from io import BytesIO

import pandas as pd
from app.schemas import (
    PetitionFileUploadResponse,
    SuccessResponse,
    VoterRecordsUploadResponse,
)
from app.utils import logger
from app.voter.voter_processor import VoterRegistrationSchema, process_voter_data
from fastapi import APIRouter, Request, Response, UploadFile, status
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/upload", tags=["File Upload"])

if not os.path.exists("temp"):
    os.makedirs("temp")
    logger.info("Created temporary directory: temp")


class UploadFileTypes(str, Enum):
    voter_records = "voter_records"
    petition_signatures = "petition_signatures"


async def _save_petition_to_temp(file: UploadFile, file_name: str):
    with open(os.path.join("temp", f"{file_name}.pdf"), "wb") as buffer:
        bytes = await file.read()
        buffer.write(bytes)
        logger.info(f"{file.filename} saved to temporary directory")


@router.delete("/clear")
def clear_all_files(request: Request):
    """
    Delete all files
    """
    request.state.voter_records_df = None
    if os.path.exists("temp/ballot.pdf"):
        os.remove("temp/ballot.pdf")
        logger.info("Deleted all files")
    else:
        logger.warning("No files to delete")
    return {"message": "All files deleted"}


@router.post("/voter-records")
async def upload_voter_records_file(
    file: UploadFile, response: Response, request: Request
) -> VoterRecordsUploadResponse:

    if not file.filename:
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            detail="No file name found. Please try again",
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Invalid file type {file.filename}. Only .csv files are allowed.",
        )

    data = await process_voter_data(file)

    return VoterRecordsUploadResponse(
        file_name=file.filename,
        message=f"{data.voters_df.size} records successfully uploaded",
    )


@router.delete("/clear-voter-records")
def clear_voter_records() -> SuccessResponse:
    DEMO_VOTER_RECORD_STATE = None
    return SuccessResponse(message="Voter records successfully cleared.")


@router.post("/petition-entry")
async def upload_petition_entry(file: UploadFile) -> PetitionFileUploadResponse:
    if not file.filename:
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            detail="No file name found. Please try again",
        )
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Invalid file type {file.filename}. Only .csv files are allowed.",
        )

    await _save_petition_to_temp(file, file_name="temp_petition")

    return PetitionFileUploadResponse(
        file_name=file.filename, message=f"{file.filename} uploaded successfully"
    )


@router.post("/petition-entries")
async def create_upload_files(petition_list: list[UploadFile]) -> SuccessResponse:

    if not petition_list or len(petition_list) == 0:
        raise HTTPException(
            status.HTTP_417_EXPECTATION_FAILED,
            detail="No files were found in the request. Please try again.",
        )

    for idx, file in enumerate[UploadFile](petition_list):
        if not file.filename.endswith(".pdf"):
            shutil.rmtree("temp")
            raise HTTPException(
                status.HTTP_412_PRECONDITION_FAILED,
                detail=f"File {file.filename} was not of type .pdf",
            )

        await _save_petition_to_temp(file, file_name=f"temp_petition_{idx + 1}")

    return SuccessResponse(
        message=f"{len(petition_list)} petitions successfully uploaded."
    )


@router.delete("/clear-petitions")
def clear_petition_files() -> SuccessResponse:
    if os.path.exists("temp/ballot.pdf"):
        os.remove("temp/ballot.pdf")
        logger.info("Deleted all files")
    else:
        logger.warning("No files to delete")
    return SuccessResponse(message="Petition files removed successfully.")


@router.post("/{filetype}")
def upload_file(
    filetype: UploadFileTypes, file: UploadFile, response: Response, request: Request
):
    """Uploads file to the server and saves it to a temporary directory.

    Args:
        filetype (UploadFileTypes): can be voter_records or petition_signatures
    """
    logger.info(f"Received file: {file.filename} of type: {filetype}")

    # Validate file type extension
    match filetype:
        case UploadFileTypes.petition_signatures:
            if not file.filename.endswith(".pdf"):
                response.status_code = 400
                return {"error": "Invalid file type. Only pdf files are allowed."}
            with open(os.path.join("temp", "ballot.pdf"), "wb") as buffer:
                buffer.write(file.file.read())
                logger.info("File saved to temporary directory: temp/ballot.pdf")
        case UploadFileTypes.voter_records:
            if not file.filename.endswith(".csv"):
                response.status_code = 400
                return {"error": "Invalid file type. Only .csv files are allowed."}
            contents = file.file.read()
            buffer = BytesIO(contents)
            df = pd.read_csv(buffer, dtype=str)

            # Create necessary columns
            df["Full Name"] = df["First_Name"] + " " + df["Last_Name"]
            df["Full Address"] = (
                df["Street_Number"]
                + " "
                + df["Street_Name"]
                + " "
                + df["Street_Type"]
                + " "
                + df["Street_Dir_Suffix"]
            )

            required_columns = [
                "First_Name",
                "Last_Name",
                "Street_Number",
                "Street_Name",
                "Street_Type",
                "Street_Dir_Suffix",
            ]
            request.app.state.voter_records_df = df

            # Verify required columns
            if not all(col in df.columns for col in required_columns):
                response.status_code = 400
                return {"error": "Missing required columns in voter records file."}

    return {"filename": file.filename}


@router.get("/{filetype}")
def get_uploaded_file(filetype: UploadFileTypes, request: Request):
    """Returns the uploaded file.

    Args:
        filetype (UploadFileTypes): can be voter_records or petition_signatures
    """
    logger.info(f"Retrieving file of type: {filetype}")

    # Validate file type
    match filetype:
        case UploadFileTypes.petition_signatures:
            if not os.path.exists("temp/ballot.pdf"):
                return {"error": "No PDF file found for petition signatures"}
            return FileResponse("temp/ballot.pdf")
        case UploadFileTypes.voter_records:
            if request.app.state.voter_records_df is None:
                return {"error": "No voter records file found"}
            return request.app.state.voter_records_df.to_csv(index=False)
