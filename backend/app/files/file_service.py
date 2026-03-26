"""File service for handling petition PDFs and voter lists."""

import contextlib
import hashlib
import io
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pandas as pd
from pdf2image import convert_from_path
from pydantic import BaseModel

from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter

if TYPE_CHECKING:
	from fastapi import UploadFile
	from sqlmodel import Session


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

	DC_CROP_REGION = {"top": 0.385, "bottom": 0.725}
	storage_base: Path

	def __init__(
		self, session: "Session | Any" = None, storage_base: Path | None = None
	) -> None:
		self.session = session
		self.storage_base = storage_base or Path(os.getenv("UPLOAD_DIR", "./uploads"))

	async def upload_petition(
		self, file: "UploadFile", campaign_id: UUID, user_id: int
	) -> PetitionScan:
		"""Upload and validate a petition PDF file."""
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
		file_size = len(content)

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
			file_size=file_size,
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
		"""Crop petition PDF into individual signature entries."""
		images = convert_from_path(str(pdf_path))
		crops = []
		crop_dir = self.storage_base / "campaigns" / str(campaign_id) / "crops"
		crop_dir.mkdir(parents=True, exist_ok=True)

		crop_region = self.DC_CROP_REGION

		for page_num, image in enumerate(images, start=1):
			width, height = image.size

			top = int(height * crop_region["top"])
			bottom = int(height * crop_region["bottom"])

			cropped = image.crop((0, top, width, bottom))

			crop_filename = f"{petition_scan_id}_page{page_num}_crop{page_num}.png"
			crop_path = crop_dir / crop_filename
			cropped.save(crop_path, "PNG")

			crop = PetitionCrop(
				scan_id=petition_scan_id,
				crop_index=page_num,
				stored_path=str(crop_path),
				crop_coordinates={
					"top": crop_region["top"],
					"bottom": crop_region["bottom"],
				},
				page_number=page_num,
			)
			crops.append(crop)

		return crops

	async def upload_voter_list(
		self, file: "UploadFile", region_id: int
	) -> VoterListUploadResult:
		"""Upload and validate a voter list CSV file."""
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

	async def save_voter_list_file(self, file: "UploadFile") -> tuple[str, int]:
		"""Save voter list file and return path and row count."""
		if not file.filename:
			raise FileValidationError("No filename provided")

		valid_extensions = (".csv", ".xlsx", ".xls")
		if not file.filename.lower().endswith(valid_extensions):
			raise FileValidationError(
				f"Invalid file type. Supported formats: {', '.join(valid_extensions)}"
			)

		content = await file.read()

		voter_dir = self.storage_base / "voter-lists"
		voter_dir.mkdir(parents=True, exist_ok=True)

		file_path = voter_dir / file.filename
		file_path.write_bytes(content)
		_ = await file.seek(0)

		row_count = 0
		if file.filename.lower().endswith(".csv"):
			content_str = content.decode("utf-8")
			row_count = (
				len([line for line in content_str.strip().split("\n") if line]) - 1
			)
		elif file.filename.lower().endswith((".xlsx", ".xls")):
			import io

			df = pd.read_excel(io.BytesIO(content))
			row_count = len(df)

		return (str(file_path), max(0, row_count))

	async def import_voter_list(
		self, file: "UploadFile", region_id: UUID
	) -> tuple[str, int]:
		"""Import voter list CSV into registered_voters table.

		Args:
			file: Uploaded CSV file
			region_id: Region UUID to associate voters with

		Returns:
			Tuple of (file_path, imported_count)

		Raises:
			FileValidationError: If file is invalid
		"""
		if not file.filename or not file.filename.lower().endswith(".csv"):
			raise FileValidationError("Invalid file type. Only CSV files are allowed.")

		content = await file.read()
		await file.seek(0)

		df = pd.read_csv(io.BytesIO(content))
		df.columns = [col.strip() for col in df.columns]

		required_columns = ["First_Name", "Last_Name"]
		missing = [col for col in required_columns if col not in df.columns]
		if missing:
			raise FileValidationError(f"Missing required columns: {', '.join(missing)}")

		voter_dir = self.storage_base / "voter-lists"
		voter_dir.mkdir(parents=True, exist_ok=True)
		file_path = voter_dir / file.filename
		file_path.write_bytes(content)

		from sqlmodel import col, select

		result = self.session.exec(
			select(RegisteredVoter.id).order_by(col(RegisteredVoter.id).desc()).limit(1)
		)
		max_id = result.first() or 0

		voters_to_insert = []
		for _idx, row in df.iterrows():
			name_data = {
				"first_name": str(row.get("First_Name", "")).strip(),
				"last_name": str(row.get("Last_Name", "")).strip(),
				"middle_name": str(row.get("Middle_Name", "")).strip()
				if pd.notna(row.get("Middle_Name"))
				else None,
			}

			street_parts = [
				str(row.get("Street_Number", "")).strip()
				if pd.notna(row.get("Street_Number"))
				else "",
				str(row.get("Street_Name", "")).strip()
				if pd.notna(row.get("Street_Name"))
				else "",
				str(row.get("Street_Type", "")).strip()
				if pd.notna(row.get("Street_Type"))
				else "",
				str(row.get("Street_Dir_Suffix", "")).strip()
				if pd.notna(row.get("Street_Dir_Suffix"))
				else "",
			]
			street = " ".join(p for p in street_parts if p)

			address_data = {
				"street": street,
				"city": str(row.get("City", "")).strip()
				if pd.notna(row.get("City"))
				else None,
				"state": str(row.get("State", "")).strip()
				if pd.notna(row.get("State"))
				else None,
				"zip": str(row.get("Zip", "")).strip()
				if pd.notna(row.get("Zip"))
				else None,
			}

			other_data = {
				"party": str(row.get("Party", "")).strip()
				if pd.notna(row.get("Party"))
				else None,
				"registration_date": str(row.get("Registration_Date", "")).strip()
				if pd.notna(row.get("Registration_Date"))
				else None,
			}

			max_id += 1
			voter = RegisteredVoter(
				id=max_id,
				region_id=region_id,
				name_data=name_data,
				address_data=address_data,
				other_field_data=other_data,
			)
			voters_to_insert.append(voter)

		for voter in voters_to_insert:
			self.session.add(voter)

		from app.data.database.model.voter_list_upload import (
			UploadStatus,
			VoterListUpload,
		)

		upload = VoterListUpload(
			region_id=region_id,
			original_filename=file.filename,
			file_size=len(content),
			row_count=len(voters_to_insert),
			status=UploadStatus.ACTIVE,
		)
		self.session.add(upload)
		self.session.flush()

		from app.services.voter_list_service import VoterListService

		voter_list_service = VoterListService(self.session)
		voter_list_service.supersede_previous_uploads(region_id, upload)

		self.session.commit()

		return (str(file_path), len(voters_to_insert))

	async def process_petition_upload(
		self, file: "UploadFile", campaign_id: str, region: str = "DC"
	) -> tuple[int, int]:
		"""Upload petition PDF, save it, and create crops.

		Args:
			file: Uploaded PDF file
			campaign_id: Campaign ID to associate with
			region: Region for crop coordinates (default: DC)

		Returns:
			Tuple of (scan_id, crop_count)

		Raises:
			FileValidationError: If file is invalid
		"""
		if not file.filename or not file.filename.lower().endswith(".pdf"):
			raise FileValidationError("Invalid file type. Only PDF files are allowed.")

		# Normalize campaign_id (remove hyphens if present)
		campaign_id_clean = campaign_id.replace("-", "")

		petition_dir = self.storage_base / "campaigns" / campaign_id_clean / "petitions"
		petition_dir.mkdir(parents=True, exist_ok=True)

		file_path = petition_dir / file.filename
		content = await file.read()
		file_path.write_bytes(content)
		_ = await file.seek(0)

		file_hash = hashlib.sha256(content).hexdigest()

		images: list[Any] = []
		with contextlib.suppress(Exception):
			images = convert_from_path(str(file_path))

		# Create PetitionScan record
		scan = PetitionScan(
			campaign_id=UUID(campaign_id_clean),
			original_filename=file.filename,
			stored_path=str(file_path),
			file_hash=file_hash,
			page_count=len(images),
		)
		self.session.add(scan)
		self.session.commit()
		self.session.refresh(scan)
		scan_id = scan.id

		crop_dir = self.storage_base / "campaigns" / campaign_id_clean / "crops"
		crop_dir.mkdir(parents=True, exist_ok=True)

		crop_count = 0

		for page_num, image in enumerate(images, start=1):
			width, height = image.size

			top = int(height * self.DC_CROP_REGION["top"])
			bottom = int(height * self.DC_CROP_REGION["bottom"])

			cropped = image.crop((0, top, width, bottom))

			crop_filename = f"{scan_id}_page{page_num}_crop{page_num}.png"
			crop_path = crop_dir / crop_filename
			cropped.save(crop_path, "PNG")

			# Create PetitionCrop record
			crop = PetitionCrop(
				scan_id=scan_id,
				crop_index=page_num,
				stored_path=str(crop_path),
				crop_coordinates={
					"top": self.DC_CROP_REGION["top"],
					"bottom": self.DC_CROP_REGION["bottom"],
				},
				page_number=page_num,
			)
			self.session.add(crop)
			crop_count += 1

		if crop_count > 0:
			self.session.commit()

		return (scan_id, crop_count)
