"""File service for handling petition PDFs and voter lists."""

import asyncio
import contextlib
import hashlib
import io
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.domain.field_spec import RegionFieldSpecConfig

import pandas as pd
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PopplerNotInstalledError,
)
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

    storage_base: Path

    DC_CROP_REGION = {"top": 0.385, "bottom": 0.725}

    def __init__(
        self,
        session: "Session | Any" = None,
        storage_base: Path | None = None,
        pdf_conversion_timeout: float | None = None,
    ) -> None:
        self.session = session
        self.storage_base = storage_base or Path(os.getenv("UPLOAD_DIR", "./uploads"))
        self._pdf_conversion_timeout = pdf_conversion_timeout

    async def upload_voter_list(
        self, file: "UploadFile", region_id: int
    ) -> VoterListUploadResult:
        """Upload and validate a voter list CSV file."""
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise FileValidationError("Invalid file type. Only CSV files are allowed.")
        if any(ch in file.filename for ch in ("/", "\\", "\x00")):
            raise FileValidationError("Invalid filename")

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

        file_path = voter_dir / f"{uuid4().hex}.csv"
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
        matched_suffix = next(
            (ext for ext in valid_extensions if file.filename.lower().endswith(ext)),
            None,
        )
        if matched_suffix is None:
            raise FileValidationError(
                f"Invalid file type. Supported formats: {', '.join(valid_extensions)}"
            )
        if any(ch in file.filename for ch in ("/", "\\", "\x00")):
            raise FileValidationError("Invalid filename")

        content = await file.read()

        voter_dir = self.storage_base / "voter-lists"
        voter_dir.mkdir(parents=True, exist_ok=True)

        # Use the matched allowlisted extension, not Path(...).suffix: a bare
        # ".csv" has an empty Path suffix and would be stored extensionless.
        file_path = voter_dir / f"{uuid4().hex}{matched_suffix}"
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
        self,
        file: "UploadFile",
        region_id: UUID,
        spec: "RegionFieldSpecConfig | None" = None,
    ) -> tuple[str, int]:
        """Import voter list CSV into registered_voters table.

        Uses the region's field spec to parse CSV columns into structured
        name_data, address_data, and other_field_data blobs. If no spec
        is provided and none can be loaded for the region, falls back to
        basic column mapping.

        Args:
                file: Uploaded CSV file
                region_id: Region UUID to associate voters with
                spec: Optional pre-loaded spec. If None, loads from DB.

        Returns:
                Tuple of (file_path, imported_count)

        Raises:
                FileValidationError: If file is invalid
        """
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise FileValidationError("Invalid file type. Only CSV files are allowed.")
        if any(ch in file.filename for ch in ("/", "\\", "\x00")):
            raise FileValidationError("Invalid filename")

        content = await file.read()
        await file.seek(0)

        if len(content) == 0:
            raise FileValidationError("Empty file. CSV must have content.")

        csv_content = content.decode("utf-8")

        voter_dir = self.storage_base / "voter-lists"
        voter_dir.mkdir(parents=True, exist_ok=True)
        # Server-generated name: the client-controlled filename never reaches a
        # path, and every upload lands in a distinct file (no overwrite).
        file_path = voter_dir / f"{uuid4().hex}.csv"
        file_path.write_bytes(content)

        from app.services.voter_list_service import VoterListService

        if spec is None:
            try:
                from app.repositories.field_spec_repo import FieldSpecRepositoryImpl
                from app.services.field_spec_service import FieldSpecService

                from app.persistence.session import get_engine

                repo = FieldSpecRepositoryImpl(get_engine())
                spec_service = FieldSpecService(repo)
                spec = spec_service.get_spec(region_id)
            except Exception:
                spec = None

        voter_list_service = VoterListService(self.session)

        if spec is not None:
            rows = voter_list_service.parse_csv_with_spec(csv_content, spec)
            voters_to_insert = []
            for row in rows:
                name_data, address_data, other_data = (
                    voter_list_service.group_by_category(row, spec.voter_reg_fields)
                )
                voter = RegisteredVoter(
                    region_id=region_id,
                    name_data=name_data,
                    address_data=address_data,
                    other_field_data=other_data,
                )
                voters_to_insert.append(voter)
        else:
            df = pd.read_csv(io.BytesIO(content))
            df.columns = [col.strip() for col in df.columns]
            voters_to_insert = []
            for _idx, row in df.iterrows():
                name_data = {
                    "first_name": str(row.get("First_Name", "")).strip(),
                    "last_name": str(row.get("Last_Name", "")).strip(),
                    "middle_name": str(row.get("Middle_Name", "")).strip()
                    if pd.notna(row.get("Middle_Name"))
                    else None,
                }
                address_data = {
                    "street": str(row.get("Street", "")).strip()
                    if pd.notna(row.get("Street"))
                    else None,
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
                voter = RegisteredVoter(
                    region_id=region_id,
                    name_data=name_data,
                    address_data=address_data,
                    other_field_data={},
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

        voter_list_service.supersede_previous_uploads(region_id, upload)

        self.session.commit()

        return (str(file_path), len(voters_to_insert))

    async def process_petition_upload(
        self, file: "UploadFile", campaign_id: str
    ) -> tuple[int, int]:
        """Upload petition PDF, save it, and create crops.

        Args:
                file: Uploaded PDF file
                campaign_id: Campaign ID to associate with

        Returns:
                Tuple of (scan_id, crop_count)

        Raises:
                FileValidationError: If file is invalid
        """
        try:
            campaign_uuid = UUID(campaign_id.replace("-", ""))
        except ValueError as e:
            raise FileValidationError("Invalid campaign ID") from e

        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise FileValidationError("Invalid file type. Only PDF files are allowed.")

        if any(ch in file.filename for ch in ("/", "\\", "\x00")):
            raise FileValidationError("Invalid filename")

        if file.content_type != "application/pdf":
            raise FileValidationError("Invalid content type. Expected application/pdf.")

        content = await file.read()

        if len(content) == 0:
            raise FileValidationError("Empty file. PDF must have content.")

        if not content.startswith(b"%PDF-"):
            raise FileValidationError("Invalid file content. File is not a valid PDF.")

        campaign_dir = self.storage_base / "campaigns" / campaign_uuid.hex
        petition_dir = campaign_dir / "petitions"
        petition_dir.mkdir(parents=True, exist_ok=True)

        # Server-generated name: the client-controlled original filename never
        # touches a path, so traversal, absolute paths, pre-planted names, and
        # same-name overwrites are all impossible.
        file_path = petition_dir / f"{uuid4().hex}.pdf"

        # The client-facing original name is kept only as metadata.
        original_filename = file.filename

        file_hash = hashlib.sha256(content).hexdigest()

        crop_paths: list[Path] = []
        try:
            # A settings failure or a truncated write must trigger cleanup,
            # not orphan the stored file.
            file_path.write_bytes(content)

            timeout = self._pdf_conversion_timeout
            if timeout is None:
                from app.settings.settings import get_settings

                timeout = get_settings().pdf_conversion_timeout
            # Settings ge=1 rejects sub-second values, but an injected float
            # (e.g. 0.5) would truncate to 0 and disable the timeout entirely.
            timeout = max(1, int(timeout))
            # Poppler install issues are infra failures (loud 500), not the
            # client's fault; corrupt/oversized PDFs are client failures (4xx).
            # pdf2image renders leniently by design: recoverable corrupt PDFs
            # still upload, unrecoverable ones raise PDFPageCountError.
            try:
                # Known residual: pdf2image's internal pdfinfo_from_path call
                # does not forward the timeout, so the metadata stage stays
                # unbounded.
                # pdf2image types timeout as int; fractional seconds unsupported.
                images: list[Any] = await asyncio.to_thread(
                    convert_from_path, str(file_path), timeout=timeout
                )
            except (PDFInfoNotInstalledError, PopplerNotInstalledError) as e:
                raise RuntimeError(
                    "PDF conversion unavailable: poppler not installed"
                ) from e
            except PDFPageCountError as e:
                raise FileValidationError(
                    f"PDF could not be read — corrupt or unsupported "
                    f"({type(e).__name__})"
                ) from e
            except PDFPopplerTimeoutError as e:
                raise FileValidationError(
                    "PDF conversion timed out — file too large or too complex"
                ) from e

            if not images:
                raise FileValidationError("PDF contains no pages")

            crop_dir = campaign_dir / "crops"
            crop_dir.mkdir(parents=True, exist_ok=True)

            scan = PetitionScan(
                campaign_id=campaign_uuid,
                original_filename=original_filename,
                stored_path=str(file_path),
                file_hash=file_hash,
                page_count=len(images),
            )
            self.session.add(scan)
            # Flush generates scan.id so crop filenames can reference it without
            # committing; a single commit at the end makes scan + crops atomic.
            self.session.flush()
            scan_id = scan.id

            crop_count = 0
            for page_num, image in enumerate(images, start=1):
                width, height = image.size

                top = int(height * self.DC_CROP_REGION["top"])
                bottom = int(height * self.DC_CROP_REGION["bottom"])

                cropped = image.crop((0, top, width, bottom))

                crop_filename = f"{scan_id}_page{page_num}_crop{page_num}.png"
                crop_path = crop_dir / crop_filename
                # Track the path before saving so a write that fails mid-way
                # is still cleaned up.
                crop_paths.append(crop_path)
                cropped.save(crop_path, "PNG")

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

            self.session.commit()
        except BaseException:
            # Never leave disk residue from a rejected/cancelled upload.
            # BaseException (not Exception) covers asyncio.CancelledError from
            # client disconnects.
            with contextlib.suppress(OSError):
                file_path.unlink(missing_ok=True)
            for crop_path in crop_paths:
                # Guard each unlink so one failure cannot mask the original
                # exception or abort the remaining cleanup (a failing unlink
                # must not mask the original error or abort the loop).
                with contextlib.suppress(OSError):
                    crop_path.unlink(missing_ok=True)
            raise

        return (scan_id, crop_count)
