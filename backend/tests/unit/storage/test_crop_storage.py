"""Unit tests for CropStorageAdapter and LocalFileAdapter.

BDD-style tests for the crop image storage abstraction.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _seed_crop(session: Session, stored_path: str = "/tmp/crop_001.png") -> int:
    region = Region(region_key="DC", region_name="DC", country_code="US")
    session.add(region)
    session.flush()
    campaign = Campaign(
        unique_name="dc-test", title="DC Test", year="2024", region_id=region.id
    )
    session.add(campaign)
    session.flush()
    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc",
        page_count=1,
    )
    session.add(scan)
    session.flush()
    crop = PetitionCrop(
        scan_id=scan.id,
        crop_index=0,
        stored_path=stored_path,
        crop_coordinates={"top": 0.0, "bottom": 0.1},
        page_number=1,
    )
    session.add(crop)
    session.flush()
    session.commit()
    return crop.id


class TestCropStorageAdapterProtocol:
    """Feature: CropStorageAdapter abstracts image URL generation and path resolution.

    As a consumer of crop images
    I want a protocol that generates URLs and resolves file paths
    So that storage backend can be swapped without changing callers.
    """

    def test_local_file_adapter_get_image_url(self, session: Session):
        """Scenario: Generate URL for a valid crop ID."""
        from app.storage.crop_storage import LocalFileAdapter

        adapter = LocalFileAdapter(session)
        url = adapter.get_image_url(42)

        assert url == "/api/crops/42/image"

    def test_url_injective_different_crop_ids(self, session: Session):
        """Scenario: Different crop IDs produce different URLs."""
        from app.storage.crop_storage import LocalFileAdapter

        adapter = LocalFileAdapter(session)
        url_a = adapter.get_image_url(1)
        url_b = adapter.get_image_url(2)

        assert url_a != url_b

    def test_url_injective_same_crop_id_idempotent(self, session: Session):
        """Scenario: Same crop ID always produces same URL."""
        from app.storage.crop_storage import LocalFileAdapter

        adapter = LocalFileAdapter(session)
        assert adapter.get_image_url(99) == adapter.get_image_url(99)

    def test_get_image_path_returns_path_for_existing_crop(
        self, session: Session, tmp_path
    ):
        """Scenario: Crop exists in DB with a valid stored_path."""
        from app.storage.crop_storage import LocalFileAdapter

        png_file = tmp_path / "crop_001.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        crop_id = _seed_crop(session, stored_path=str(png_file))

        adapter = LocalFileAdapter(session, storage_base=tmp_path)
        result = adapter.get_image_path(crop_id)

        assert result is not None
        assert result == png_file

    def test_get_image_path_returns_none_for_missing_crop(
        self, session: Session, tmp_path
    ):
        """Scenario: Crop ID not in database."""
        from app.storage.crop_storage import LocalFileAdapter

        adapter = LocalFileAdapter(session, storage_base=tmp_path)
        assert adapter.get_image_path(999999) is None

    def test_get_image_path_returns_none_when_file_missing(
        self, session: Session, tmp_path
    ):
        """Scenario: Crop exists in DB but file deleted from disk."""
        from app.storage.crop_storage import LocalFileAdapter

        crop_id = _seed_crop(session, stored_path="/nonexistent/path/crop.png")

        adapter = LocalFileAdapter(session, storage_base=tmp_path)
        assert adapter.get_image_path(crop_id) is None

    def test_rejects_path_traversal_attack(self, session: Session, tmp_path):
        """Scenario: stored_path with ../ escapes storage base — must return None."""
        from app.storage.crop_storage import LocalFileAdapter

        storage_dir = tmp_path / "uploads"
        storage_dir.mkdir()
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("sensitive data")

        traversal = str((storage_dir / ".." / "secret.txt").resolve())
        crop_id = _seed_crop(session, stored_path=traversal)

        adapter = LocalFileAdapter(session, storage_base=storage_dir)
        assert adapter.get_image_path(crop_id) is None


class TestCropStorageAdapterProtocolConformance:
    """Feature: LocalFileAdapter satisfies the CropStorageAdapter protocol."""

    def test_local_file_adapter_is_crop_storage_adapter(self):
        """Scenario: LocalFileAdapter implements the protocol."""
        from app.storage.crop_storage import CropStorageAdapter, LocalFileAdapter

        assert issubclass(LocalFileAdapter, CropStorageAdapter)
