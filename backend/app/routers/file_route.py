import asyncio
import os
import shutil
from _asyncio import Task
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any

import aiofiles
import fitz
import pandas as pd
from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from app.campaign.campaign_repository import CampaignRepository, ReadCampaign
from app.data.memory_db import get_memory_db
from app.dependencies import (
	get_campaign_repository,
	get_file_repository,
	get_scanned_documents_repository,
)
from app.files.file_repository import (
	CreatePetitionScan,
	RegisteredVoterRepository,
	ScannedPetitionRepository,
)
from app.schemas import (
	PetitionFileUploadResponse,
	SuccessResponse,
	VoterRecordsUploadResponse,
)
from app.settings.env_settings import AppSettings, get_settings
from app.utils import logger
from app.voter.voter_processor import (
	RegisteredVotersData,
	process_voter_data,
)

router: APIRouter = APIRouter(prefix="/upload", tags=["File Upload"])

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


async def _process_pdf_async(file: UploadFile, dest_path: Path) -> tuple[Path, int]:
	try:
		async with aiofiles.open(dest_path, "wb") as buffer:
			while content := await file.read(1024 * 1024):  # Read in 1MB chunks
				await buffer.write(content)
			logger.debug(f"Saved {dest_path.name} to {dest_path}")

		loop = asyncio.get_event_loop()
		page_count: int = await loop.run_in_executor(
			None, _get_pdf_page_count, dest_path
		)
		logger.debug(f"PDF {dest_path.name} has {page_count} pages.")

		return (dest_path, page_count)
	except FileNotFoundError as fne:
		logger.error(f"Error: Source file not found at {dest_path}")
		raise fne
	except Exception as e:
		logger.error(f"An error occurred while copying {file.filename}: {e}")
		raise e
	finally:
		await file.close()


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
	file: Annotated[UploadFile, File()],
	db_mem: Annotated[dict[str, Any], Depends(get_memory_db)],
	settings: Annotated[AppSettings, Depends(get_settings)],
	campaign_repo: Annotated[CampaignRepository, Depends(get_campaign_repository)],
	voter_list_repo: Annotated[RegisteredVoterRepository, Depends(get_file_repository)],
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

	campaign: ReadCampaign = await campaign_repo.fetch_campaign(unique_name="demo")

	voter_dir: Path = (
		settings.local_campaign_base_dir()
		.joinpath(campaign.unique_name)
		.joinpath(settings.registration_dir)
	)

	if not voter_dir.exists():
		voter_dir.mkdir(parents=True, exist_ok=True)

	voter_file: Path = voter_dir.joinpath(file.filename)
	async with aiofiles.open(voter_file, "wb") as out_file:
		content = await file.read()  # Read in 1KB chunks
		await out_file.write(content)

	# Reset upload stream so we can read it again when saving to disk
	# UploadFile.file is a file-like object (SpooledTemporaryFile) so use .seek(0)
	try:
		file.file.seek(0)
	except Exception:
		# fa: ReadCampaignllback for implementations that might expose async seek in the future
		await file.seek(0)  # type: ignore
	data: RegisteredVotersData = await process_voter_data(file)

	await voter_list_repo.save_registered_voter_list(
		region_id=campaign.region_id, file_path=voter_file
	)

	db_mem["voter_list"] = data

	logger.debug("Uploaded voter records", records=file.filename)

	return VoterRecordsUploadResponse(
		file_name=file.filename,
		message=f"{data.voters_df.size} records successfully uploaded",
	)


@router.delete("/clear-voter-records")
def clear_voter_records() -> SuccessResponse:
	return SuccessResponse(message="Voter records successfully cleared.")


def _get_pdf_page_count(pdf_path) -> int:
	# Synchronous PyMuPDF operations
	with fitz.open(pdf_path) as doc:
		return doc.page_count


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
async def create_upload_files(
	files: Annotated[list[UploadFile], File()],
	settings: Annotated[AppSettings, Depends(get_settings)],
	campaign_repo: Annotated[CampaignRepository, Depends(get_campaign_repository)],
	scan_repo: Annotated[
		ScannedPetitionRepository, Depends(get_scanned_documents_repository)
	],
) -> SuccessResponse:
	if not files or len(files) == 0:
		raise HTTPException(
			status.HTTP_417_EXPECTATION_FAILED,
			detail="No files were found in the request. Please try again.",
		)

	for idx, file in enumerate[UploadFile](files):
		if not file.filename.endswith(".pdf"):
			shutil.rmtree("temp")
			raise HTTPException(
				status.HTTP_412_PRECONDITION_FAILED,
				detail=f"File {file.filename} was not of type .pdf",
			)

	campaign: ReadCampaign = await campaign_repo.fetch_campaign("demo")
	scanned_doc_dir: Path = (
		settings.local_campaign_base_dir()
		.joinpath(campaign.unique_name)
		.joinpath(settings.petition_dir)
	)

	if not scanned_doc_dir.exists():
		scanned_doc_dir.mkdir(parents=True, exist_ok=True)

	magnitude: int = max(len(str(len(files))), 2)

	file_copy_task: list[Task[tuple[Path, int]]] = []
	for idx, file in enumerate[UploadFile](files):
		file_dest: Path = scanned_doc_dir.joinpath(
			f"{idx + 1:0{magnitude}d}-{file.filename}"
		)
		task: Task[tuple[Path, int]] = asyncio.create_task(
			_process_pdf_async(file, file_dest)
		)
		file_copy_task.append(task)
	try:
		saved_files: list[tuple[Path, int]] = await asyncio.gather(*file_copy_task)
		logger.info(f"Saved {len(saved_files)} scanned documents.")
	except Exception:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to save {len(files)} files on server.",
		)

	file_records: list[CreatePetitionScan] = [
		CreatePetitionScan(
			file_name=doc_path.name,
			file_path=str(doc_path),
			campaign_id=campaign.unique_name,
			page_count=count,
		)
		for doc_path, count in saved_files
	]

	await scan_repo.save_scanned_petitions(file_records)
	# await _save_petition_to_temp(file, file_name=f"temp_petition_{idx + 1}")

	return SuccessResponse(
		message=f"{len(saved_files)} petitions successfully uploaded."
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
