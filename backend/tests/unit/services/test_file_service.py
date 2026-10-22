"""Unit tests for FileService."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile

from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
)

from app.files.file_service import FileService, FileValidationError


class _FakeSession:
    """Minimal session double capturing add/commit behavior."""

    def __init__(self, scan_id_on_flush: int = 7):
        self.added: list = []
        self.commits = 0
        self.scan_id_on_flush = scan_id_on_flush

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        obj = self.added[-1]
        if not getattr(obj, "id", None):
            obj.id = self.scan_id_on_flush

    def refresh(self, obj):
        pass

    def commit(self):
        self.commits += 1


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


class _FakeImage:
    """Stand-in for a PIL image produced by convert_from_path.

    Successful saves actually write the target file so cleanup tests can
    verify unlink behavior.
    """

    def __init__(self, size: tuple[int, int] = (1000, 1500), fail_save=False):
        self.size = size
        self._fail_save = fail_save

    def crop(self, box):
        return self

    def save(self, path, fmt):
        if self._fail_save:
            raise OSError("disk write failed")
        Path(path).write_bytes(b"fake-image")


def _petition_upload_file(
    filename: str = "test_petition.pdf",
    content_type: str | None = "application/pdf",
    content: bytes = b"%PDF-1.4\n%fake pdf\n%%EOF",
):
    from unittest.mock import MagicMock

    from fastapi import UploadFile

    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type

    async def mock_read():
        return content

    file.read = mock_read
    file.seek = AsyncMock()
    return file


class TestFileServiceProcessPetitionUpload:
    """Tests for the active petition upload path."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def fake_session(self):
        return _FakeSession()

    @pytest.fixture
    def file_service(self, temp_storage, fake_session):
        return FileService(session=fake_session, storage_base=temp_storage)

    def _mock_convert(self, images):
        return patch("app.files.file_service.convert_from_path", return_value=images)

    @pytest.mark.asyncio
    async def test_garbage_bytes_named_pdf_rejected(self, file_service):
        """PDF-named garbage bytes must raise, not silently 201."""
        file = _petition_upload_file(content=b"not a pdf at all")
        with pytest.raises(FileValidationError):
            await file_service.process_petition_upload(
                file=file, campaign_id=str(uuid4())
            )

    @pytest.mark.asyncio
    async def test_wrong_content_type_rejected(self, file_service):
        """Content type must be application/pdf, even with a .pdf filename."""
        file = _petition_upload_file(content_type="text/plain")
        with pytest.raises(FileValidationError, match="Invalid content type"):
            await file_service.process_petition_upload(
                file=file, campaign_id=str(uuid4())
            )

    @pytest.mark.asyncio
    async def test_missing_pdf_magic_bytes_rejected(self, file_service):
        """Valid content type but no %PDF- magic must be rejected."""
        file = _petition_upload_file(content=b"%%EOF but no header")
        with pytest.raises(FileValidationError, match="not a valid PDF"):
            await file_service.process_petition_upload(
                file=file, campaign_id=str(uuid4())
            )

    @pytest.mark.asyncio
    async def test_page_count_error_maps_to_validation_error(self, file_service):
        """PDFPageCountError is a client-side corrupt file: 4xx."""
        with self._mock_convert(None) as convert:
            convert.side_effect = PDFPageCountError("no page count")
            file = _petition_upload_file()
            with pytest.raises(FileValidationError, match="corrupt or unsupported"):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

    @pytest.mark.asyncio
    async def test_poppler_timeout_maps_to_validation_error(self, file_service):
        """Timeout is surfaced as a 4xx validation error (timeout-only rule)."""
        service = FileService(
            session=file_service.session,
            storage_base=file_service.storage_base,
            pdf_conversion_timeout=12,
        )
        with self._mock_convert(None) as convert:
            convert.side_effect = PDFPopplerTimeoutError("timed out")
            file = _petition_upload_file()
            with pytest.raises(FileValidationError, match="timed out"):
                await service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )
            # Timeout is threaded from settings into convert_from_path.
            assert convert.call_args.kwargs.get("timeout") == 12

    @pytest.mark.asyncio
    async def test_conversion_failure_removes_stored_file(self, file_service):
        """A failed conversion must not leave the uploaded file on disk."""
        with self._mock_convert(None) as convert:
            convert.side_effect = PDFPageCountError("no page count")
            file = _petition_upload_file()
            with pytest.raises(FileValidationError):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

        assert not list(file_service.storage_base.rglob("*.pdf"))

    @pytest.mark.asyncio
    async def test_non_uuid_campaign_id_rejected_without_creating_directories(
        self, file_service, temp_storage
    ):
        """A malformed campaign ID must fail before touching the filesystem."""
        file = _petition_upload_file()
        with pytest.raises(FileValidationError, match="Invalid campaign ID"):
            await file_service.process_petition_upload(
                file=file, campaign_id="not-a-campaign-id"
            )

        assert temp_storage.exists() is False or list(temp_storage.iterdir()) == []

    @pytest.mark.asyncio
    async def test_filename_with_path_separator_rejected(self, file_service):
        """Client filenames never reach a path; separators are rejected."""
        for bad_name in (
            "../evil.pdf",
            "/etc/passwd.pdf",
            "sub\\dir.pdf",
            "n\x00ul.pdf",
        ):
            file = _petition_upload_file(filename=bad_name)
            with pytest.raises(FileValidationError, match="Invalid filename"):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

    @pytest.mark.asyncio
    async def test_same_filename_reuploads_use_distinct_stored_paths(
        self, file_service
    ):
        """Same-name re-uploads must not overwrite each other on disk."""
        images = [_FakeImage()]
        stored_paths = []
        with patch("app.files.file_service.convert_from_path", return_value=images):
            for _ in range(2):
                file = _petition_upload_file(filename="petitions.pdf")
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )
                scans = [
                    obj
                    for obj in file_service.session.added
                    if type(obj).__name__ == "PetitionScan"
                ]
                stored_paths.append(scans[-1].stored_path)

        assert stored_paths[0] != stored_paths[1]

    @pytest.mark.asyncio
    async def test_poppler_not_installed_raises_runtime_error(self, file_service):
        """Missing poppler is infra failure: RuntimeError, never 4xx."""
        with self._mock_convert(None) as convert:
            convert.side_effect = PDFInfoNotInstalledError("no poppler")
            file = _petition_upload_file()
            with pytest.raises(RuntimeError, match="poppler not installed"):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

    @pytest.mark.asyncio
    async def test_zero_page_pdf_rejected(self, file_service):
        """Valid PDF with zero pages must be rejected at the boundary."""
        with self._mock_convert([]):
            file = _petition_upload_file()
            with pytest.raises(FileValidationError, match="no pages"):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

    @pytest.mark.asyncio
    async def test_happy_path_returns_scan_id_and_crop_count(
        self, file_service, fake_session
    ):
        """N pages cropped yields (scan_id, N) with one commit."""
        images = [_FakeImage(), _FakeImage(), _FakeImage()]
        with self._mock_convert(images):
            file = _petition_upload_file()
            scan_id, crop_count = await file_service.process_petition_upload(
                file=file, campaign_id=str(uuid4())
            )

        assert crop_count == 3
        assert scan_id == fake_session.scan_id_on_flush
        assert fake_session.commits == 1
        added_types = [type(obj).__name__ for obj in fake_session.added]
        assert added_types.count("PetitionScan") == 1
        assert added_types.count("PetitionCrop") == 3

    @pytest.mark.asyncio
    async def test_mid_crop_failure_persists_nothing(self, file_service, fake_session):
        """A failing crop write must leave the scan uncommitted."""
        images = [_FakeImage(), _FakeImage(fail_save=True)]
        with self._mock_convert(images):
            file = _petition_upload_file()
            with pytest.raises(OSError):
                await file_service.process_petition_upload(
                    file=file, campaign_id=str(uuid4())
                )

        assert fake_session.commits == 0
        # Cleanup removed the stored PDF and every written crop PNG.
        assert list(file_service.storage_base.rglob("*.png")) == []
        assert list(file_service.storage_base.rglob("*.pdf")) == []
