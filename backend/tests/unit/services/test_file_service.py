"""Unit tests for FileService."""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.files.file_service import FileService, FileValidationError


class TestFileServiceUploadPetition:
	"""Tests for FileService.upload_petition()."""

	@pytest.fixture
	def temp_storage(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			yield Path(tmpdir)

	@pytest.fixture
	def file_service(self, temp_storage):
		return FileService(storage_base=temp_storage)

	@pytest.fixture
	def valid_pdf_upload(self):
		pdf_content = b"%PDF-1.4\n%fake pdf content\n%%EOF"
		file = MagicMock(spec=UploadFile)
		file.filename = "test_petition.pdf"
		file.content_type = "application/pdf"

		async def mock_read():
			return pdf_content

		file.read = mock_read
		file.seek = AsyncMock()
		return file

	@pytest.fixture
	def valid_csv_upload(self):
		csv_content = (
			b"First_Name,Last_Name,Street_Number,Street_Name\nJohn,Doe,123,Main St"
		)
		file = MagicMock(spec=UploadFile)
		file.filename = "voters.csv"
		file.content_type = "text/csv"

		async def mock_read():
			return csv_content

		file.read = mock_read
		file.seek = AsyncMock()
		return file

	@pytest.mark.asyncio
	async def test_upload_petition_validates_pdf_extension(
		self, file_service, temp_storage
	):
		"""Should reject non-PDF files."""
		invalid_file = MagicMock(spec=UploadFile)
		invalid_file.filename = "test.txt"
		invalid_file.file = BytesIO(b"not a pdf")
		invalid_file.content_type = "text/plain"

		async def mock_read():
			return b"not a pdf"

		invalid_file.read = mock_read

		with pytest.raises(FileValidationError, match="Invalid file type"):
			await file_service.upload_petition(
				file=invalid_file, campaign_id=uuid4(), user_id=1
			)

	@pytest.mark.asyncio
	async def test_upload_petition_validates_pdf_content_type(
		self, file_service, temp_storage
	):
		"""Should reject files with wrong content type."""
		invalid_file = MagicMock(spec=UploadFile)
		invalid_file.filename = "test.pdf"
		invalid_file.file = BytesIO(b"not a pdf")
		invalid_file.content_type = "image/png"

		async def mock_read():
			return b"not a pdf"

		invalid_file.read = mock_read

		with pytest.raises(FileValidationError, match="Invalid content type"):
			await file_service.upload_petition(
				file=invalid_file, campaign_id=uuid4(), user_id=1
			)

	@pytest.mark.asyncio
	async def test_upload_petition_saves_to_correct_directory(
		self, file_service, temp_storage, valid_pdf_upload
	):
		"""Should save PDF in campaign petitions directory."""
		campaign_id = uuid4()
		result = await file_service.upload_petition(
			file=valid_pdf_upload, campaign_id=campaign_id, user_id=1
		)

		assert result.campaign_id == campaign_id
		assert result.original_filename == "test_petition.pdf"
		assert "campaigns" in result.stored_path
		assert "petitions" in result.stored_path

	@pytest.mark.asyncio
	async def test_upload_petition_returns_petition_scan_model(
		self, file_service, temp_storage, valid_pdf_upload
	):
		"""Should return PetitionScan model with metadata."""
		campaign_id = uuid4()
		result = await file_service.upload_petition(
			file=valid_pdf_upload, campaign_id=campaign_id, user_id=1
		)

		assert result.campaign_id == campaign_id
		assert result.original_filename == "test_petition.pdf"
		assert Path(result.stored_path).exists()
		assert result.file_hash != ""
		assert result.uploaded_by == 1


class TestFileServiceCropPetition:
	"""Tests for FileService.crop_petition()."""

	@pytest.fixture
	def temp_storage(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			yield Path(tmpdir)

	@pytest.fixture
	def file_service(self, temp_storage):
		return FileService(storage_base=temp_storage)

	@pytest.fixture
	def mock_pdf_path(self, temp_storage):
		pdf_path = temp_storage / "test.pdf"
		pdf_path.write_bytes(b"%PDF-1.4\n%fake pdf\n%%EOF")
		return pdf_path

	def test_crop_petition_converts_pdf_to_images(
		self, file_service, mock_pdf_path, temp_storage
	):
		"""Should convert PDF pages to cropped images."""
		with patch("app.files.file_service.convert_from_path") as mock_convert:
			mock_image = MagicMock()
			mock_image.size = (1000, 1500)
			mock_image.crop.return_value = mock_image
			mock_image.save = MagicMock()
			mock_convert.return_value = [mock_image]

			crops = file_service.crop_petition(
				pdf_path=mock_pdf_path, petition_scan_id=1, campaign_id=1, region="dc"
			)

			mock_convert.assert_called_once()
			assert len(crops) > 0
			assert all(hasattr(crop, "stored_path") for crop in crops)

	def test_crop_petition_uses_dc_region_preset(
		self, file_service, mock_pdf_path, temp_storage
	):
		"""Should use DC region preset crop coordinates."""
		with patch("app.files.file_service.convert_from_path") as mock_convert:
			mock_image = MagicMock()
			mock_image.size = (1000, 1500)
			mock_image.crop.return_value = mock_image
			mock_image.save = MagicMock()
			mock_convert.return_value = [mock_image]

			file_service.crop_petition(
				pdf_path=mock_pdf_path, petition_scan_id=1, campaign_id=1, region="dc"
			)

			mock_image.crop.assert_called()

	def test_crop_petition_saves_with_naming_convention(
		self, file_service, mock_pdf_path, temp_storage
	):
		"""Should save crops with convention: {scan_id}_page{num}_crop{idx}.png."""
		with patch("app.files.file_service.convert_from_path") as mock_convert:
			mock_image = MagicMock()
			mock_image.size = (1000, 1500)
			mock_image.crop.return_value = mock_image
			mock_image.save = MagicMock()
			mock_convert.return_value = [mock_image, mock_image]

			crops = file_service.crop_petition(
				pdf_path=mock_pdf_path, petition_scan_id=42, campaign_id=1, region="dc"
			)

			for crop in crops:
				assert "42_page" in crop.stored_path
				assert "_crop" in crop.stored_path
				assert crop.stored_path.endswith(".png")


class TestFileServiceUploadVoterList:
	"""Tests for FileService.upload_voter_list()."""

	@pytest.fixture
	def temp_storage(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			yield Path(tmpdir)

	@pytest.fixture
	def file_service(self, temp_storage):
		return FileService(storage_base=temp_storage)

	@pytest.fixture
	def valid_csv_upload(self):
		csv_content = (
			b"First_Name,Last_Name,Street_Number,Street_Name\nJohn,Doe,123,Main St"
		)
		file = MagicMock(spec=UploadFile)
		file.filename = "voters.csv"
		file.content_type = "text/csv"

		async def mock_read():
			return csv_content

		file.read = mock_read
		file.seek = AsyncMock()
		return file

	@pytest.mark.asyncio
	async def test_upload_voter_list_validates_csv_extension(
		self, file_service, temp_storage
	):
		"""Should reject non-CSV files."""
		invalid_file = MagicMock(spec=UploadFile)
		invalid_file.filename = "voters.xlsx"
		invalid_file.content_type = "application/vnd.ms-excel"

		async def mock_read():
			return b"not csv"

		invalid_file.read = mock_read

		with pytest.raises(FileValidationError, match="Invalid file type"):
			await file_service.upload_voter_list(file=invalid_file, region_id=1)

	@pytest.mark.asyncio
	async def test_upload_voter_list_saves_to_region_directory(
		self, file_service, temp_storage, valid_csv_upload
	):
		"""Should save voter list in region-level directory."""
		result = await file_service.upload_voter_list(
			file=valid_csv_upload, region_id=1
		)

		assert result.region_id == 1
		assert "regions/1/voter-lists" in result.stored_path
		assert result.original_filename == "voters.csv"

	@pytest.mark.asyncio
	async def test_upload_voter_list_validates_required_columns(
		self, file_service, temp_storage
	):
		"""Should validate CSV has required columns."""
		invalid_csv = MagicMock(spec=UploadFile)
		invalid_csv.filename = "invalid.csv"
		invalid_csv.content_type = "text/csv"

		async def mock_read():
			return b"Name,Address\nJohn,123 Main"

		invalid_csv.read = mock_read

		with pytest.raises(FileValidationError, match="Missing required columns"):
			await file_service.upload_voter_list(file=invalid_csv, region_id=1)
