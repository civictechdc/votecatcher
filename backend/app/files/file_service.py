"""File service for handling petition PDFs and voter lists."""

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from pdf2image import convert_from_path
from pydantic import BaseModel

from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan

if TYPE_CHECKING:
	from fastapi import UploadFile


class FileValidationError(Exception):
	"""Raised when file validation fails."""

	pass


class VoterListUploadResult(BaseModel):
	"""Result of voter list upload."""

	region_id: int
	stored_path: str
	original_filename: str


class FileService:
	"""Service for file upload, storage, and PDF cropping."""

	DC_CROP_REGIONS: list[dict[str, float]] = [
		{"top": 0.0, "bottom": 0.5},
		{"top": 0.5, "bottom": 1.0},
	]

	def __init__(self, storage_base: Path) -> None:
		self.storage_base = storage_base

	async def upload_petition(
		self, file: "UploadFile", campaign_id: UUID, user_id: int
	) -> PetitionScan:
		"""
		Upload and validate a petition PDF file.

		Args:
		    file: UploadFile object from FastAPI
		    campaign_id: UUID of the campaign
		    user_id: ID of the user uploading

		Returns:
		    PetitionScan model with file metadata

		Raises:
		    FileValidationError: If file validation fails
		"""
		if not file.filename or not file.filename.lower().endswith(".pdf"):
			raise FileValidationError("Invalid file type. Only PDF files are allowed.")

		if not file.content_type or file.content_type != "application/pdf":
			raise FileValidationError("Invalid content type. Expected application/pdf.")

		petition_dir = self.storage_base / "campaigns" / str(campaign_id) / "petitions"
		petition_dir.mkdir(parents=True, exist_ok=True)

		stored_path = petition_dir / file.filename
		content = await file.read()
		_ = stored_path.write_bytes(content)
		_ = await file.seek(0)

		file_hash = hashlib.sha256(content).hexdigest()

		page_count = 0
		try:
			images = convert_from_path(str(stored_path))
			page_count = len(images)
		except Exception:  # nosec B110 # Page count detection is optional, non-critical
			pass

		return PetitionScan(
			campaign_id=campaign_id,
			original_filename=file.filename,
			stored_path=str(stored_path),
			file_hash=file_hash,
			page_count=page_count,
			uploaded_by=user_id,
		)

	def crop_petition(
		self,
		pdf_path: Path,
		petition_scan_id: int,
		campaign_id: int,
		region: str = "dc",
	) -> list[PetitionCrop]:
		"""
		Crop petition PDF into individual signature entries.

		Args:
		    pdf_path: Path to the PDF file
		    petition_scan_id: ID of the PetitionScan record
		    campaign_id: ID of the campaign
		    region: Region code for crop coordinates (default: dc)

		Returns:
		    List of PetitionCrop models
		"""
		images = convert_from_path(str(pdf_path))
		crops = []
		crop_dir = self.storage_base / "campaigns" / str(campaign_id) / "crops"
		crop_dir.mkdir(parents=True, exist_ok=True)

		crop_regions = self.DC_CROP_REGIONS if region == "dc" else self.DC_CROP_REGIONS

		crop_index = 0
		for page_num, image in enumerate(images, start=1):
			width, height = image.size

			for region_spec in crop_regions:
				crop_index += 1
				top = int(height * region_spec["top"])
				bottom = int(height * region_spec["bottom"])

				cropped = image.crop((0, top, width, bottom))

				crop_filename = (
					f"{petition_scan_id}_page{page_num}_crop{crop_index}.png"
				)
				crop_path = crop_dir / crop_filename
				cropped.save(crop_path, "PNG")

				crop = PetitionCrop(
					scan_id=petition_scan_id,
					crop_index=crop_index,
					stored_path=str(crop_path),
					crop_coordinates={
						"top": region_spec["top"],
						"bottom": region_spec["bottom"],
					},
					page_number=page_num,
				)
				crops.append(crop)

		return crops

	async def upload_voter_list(
		self, file: "UploadFile", region_id: int
	) -> VoterListUploadResult:
		"""
		Upload and validate a voter list CSV file.

		Args:
		    file: UploadFile object from FastAPI
		    region_id: ID of the region

		Returns:
		    VoterListUploadResult with file metadata

		Raises:
		    FileValidationError: If file validation fails
		"""
		if not file.filename or not file.filename.lower().endswith(".csv"):
			raise FileValidationError("Invalid file type. Only CSV files are allowed.")

		content = await file.read()

		required_columns = ["First_Name", "Last_Name", "Street_Number", "Street_Name"]
		content_str = content.decode("utf-8")
		first_line = content_str.split("\n")[0]
		headers = [col.strip() for col in first_line.split(",")]

		missing = [col for col in required_columns if col not in headers]
		if missing:
			raise FileValidationError(f"Missing required columns: {', '.join(missing)}")

		voter_dir = self.storage_base / "regions" / str(region_id) / "voter-lists"
		voter_dir.mkdir(parents=True, exist_ok=True)

		file_path = voter_dir / file.filename
		_ = file_path.write_bytes(content)
		_ = await file.seek(0)

		return VoterListUploadResult(
			region_id=region_id,
			stored_path=str(file_path),
			original_filename=file.filename,
		)
