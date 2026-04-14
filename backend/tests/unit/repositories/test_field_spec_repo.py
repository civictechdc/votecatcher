"""Unit tests for FieldSpecRepository.

Tests cover CRUD operations for field spec persistence following TDD approach.
Uses real SqliteEngine for integration-style unit tests.
"""

from pathlib import Path
from uuid import UUID

import pytest

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)


def _make_spec() -> RegionFieldSpecConfig:
    return RegionFieldSpecConfig(
        region_name="Test Region",
        country_code="US",
        ballot_fields=[
            BallotField(
                id="name",
                label="Full Name",
                field_type="text",
                required_for_matching=True,
                match_weight=1.0,
            ),
        ],
        voter_reg_fields=[
            VoterRegField(
                id="last_name",
                csv_column_name="Last_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="first_name",
                csv_column_name="First_Name",
                data_type="text",
                category="name",
            ),
        ],
        field_mappings=[
            FieldMapping(
                ballot_field_id="name",
                template="{first_name} {last_name}",
            ),
        ],
        hash_fields=["last_name", "first_name"],
        crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=85),
    )


class TestFieldSpecRepository:
    @pytest.fixture
    def engine(self, tmp_path: Path):
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        engine.initialize()
        return engine

    @pytest.fixture
    def region_id(self, engine):
        from app.data.database.model.schema import Region

        with engine.create_session() as session:
            region = Region(
                region_key="TEST",
                region_name="Test Region",
                country_code="US",
            )
            session.add(region)
            session.commit()
            session.refresh(region)
            return region.id

    @pytest.fixture
    def repo(self, engine):
        from app.repositories.field_spec_repo import FieldSpecRepositoryImpl

        return FieldSpecRepositoryImpl(engine)

    def test_save_and_find_by_region(self, repo, region_id):
        spec = _make_spec()
        repo.save(spec, region_id)
        found = repo.find_by_region(region_id)
        assert found is not None
        assert found.region_name == "Test Region"
        assert len(found.ballot_fields) == 1
        assert found.ballot_fields[0].id == "name"

    def test_find_returns_none_for_unknown_region(self, repo):
        result = repo.find_by_region(UUID("00000000-0000-0000-0000-000000000999"))
        assert result is None

    def test_save_updates_existing(self, repo, region_id):
        spec_v1 = _make_spec()
        repo.save(spec_v1, region_id)

        spec_v2 = RegionFieldSpecConfig(
            region_name="Test Region V2",
            country_code="US",
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Full Name",
                    field_type="text",
                    required_for_matching=True,
                    match_weight=1.0,
                ),
                BallotField(
                    id="address",
                    label="Address",
                    field_type="address",
                    required_for_matching=True,
                    match_weight=1.0,
                ),
            ],
            voter_reg_fields=[
                VoterRegField(
                    id="last_name",
                    csv_column_name="Last_Name",
                    data_type="text",
                    category="name",
                ),
                VoterRegField(
                    id="first_name",
                    csv_column_name="First_Name",
                    data_type="text",
                    category="name",
                ),
                VoterRegField(
                    id="street_number",
                    csv_column_name="Street_Number",
                    data_type="text",
                    category="address",
                ),
            ],
            field_mappings=[
                FieldMapping(
                    ballot_field_id="name",
                    template="{first_name} {last_name}",
                ),
                FieldMapping(
                    ballot_field_id="address",
                    template="{street_number}",
                ),
            ],
            hash_fields=["last_name", "first_name", "street_number"],
            crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=85),
        )
        repo.save(spec_v2, region_id)

        found = repo.find_by_region(region_id)
        assert found is not None
        assert found.region_name == "Test Region V2"
        assert len(found.ballot_fields) == 2

    def test_delete_removes_spec(self, repo, region_id):
        spec = _make_spec()
        repo.save(spec, region_id)
        assert repo.delete(region_id) is True
        assert repo.find_by_region(region_id) is None

    def test_delete_returns_false_for_missing(self, repo):
        result = repo.delete(UUID("00000000-0000-0000-0000-000000000999"))
        assert result is False

    def test_round_trip_preserves_all_fields(self, repo, region_id):
        spec = _make_spec()
        repo.save(spec, region_id)
        found = repo.find_by_region(region_id)

        assert found is not None
        assert found.country_code == "US"
        assert len(found.voter_reg_fields) == 2
        assert found.voter_reg_fields[0].csv_column_name == "Last_Name"
        assert len(found.field_mappings) == 1
        assert found.field_mappings[0].template == "{first_name} {last_name}"
        assert found.hash_fields == ["last_name", "first_name"]
        assert found.crop_config.top_crop == 0.1
        assert found.crop_config.bottom_crop == 0.9
        assert found.crop_config.base_threshold == 85
        assert found.validate_integrity() == []


class TestFieldSpecRepositoryUpsert:
    @pytest.fixture
    def engine(self, tmp_path: Path):
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        engine.initialize()
        return engine

    @pytest.fixture
    def repo(self, engine):
        from app.repositories.field_spec_repo import FieldSpecRepositoryImpl

        return FieldSpecRepositoryImpl(engine)

    def test_upsert_creates_new(self, repo, engine):
        spec = _make_spec()
        repo.upsert("TEST", spec, region_name="Test Region", country_code="US")

        with engine.create_session() as session:
            from app.data.database.model.schema import Region

            region = session.exec(
                __import__("sqlmodel").select(Region).where(Region.region_key == "TEST")
            ).first()
            assert region is not None
            assert region.region_name == "Test Region"

        found = repo.find_by_region_key("TEST")
        assert found is not None
        assert found.region_name == "Test Region"

    def test_upsert_updates_existing(self, repo, engine):
        spec_v1 = _make_spec()
        repo.upsert("TEST", spec_v1, region_name="Test Region", country_code="US")

        spec_v2 = RegionFieldSpecConfig(
            region_name="Updated Region",
            country_code="US",
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Full Name",
                    field_type="text",
                    required_for_matching=True,
                    match_weight=1.0,
                ),
            ],
            voter_reg_fields=[
                VoterRegField(
                    id="last_name",
                    csv_column_name="Last_Name",
                    data_type="text",
                    category="name",
                ),
            ],
            field_mappings=[
                FieldMapping(
                    ballot_field_id="name",
                    template="{last_name}",
                ),
            ],
            hash_fields=["last_name"],
            crop_config=CropConfig(top_crop=0.2, bottom_crop=0.8, base_threshold=90),
        )
        repo.upsert("TEST", spec_v2, region_name="Updated Region", country_code="US")

        found = repo.find_by_region_key("TEST")
        assert found is not None
        assert found.region_name == "Updated Region"

    def test_find_by_region_key_normalizes_case(self, repo, engine):
        spec = _make_spec()
        repo.upsert("TEST", spec, region_name="Test Region", country_code="US")

        found = repo.find_by_region_key("test")
        assert found is not None
        assert found.region_name == "Test Region"

    def test_list_regions_empty(self, repo):
        regions = repo.list_regions()
        assert regions == []

    def test_list_regions_returns_loaded_specs(self, repo):
        spec = _make_spec()
        repo.upsert("TEST", spec, region_name="Test Region", country_code="US")

        regions = repo.list_regions()
        assert len(regions) == 1
        key, name, rid = regions[0]
        assert key == "TEST"
        assert name == "Test Region"
        assert isinstance(rid, UUID)
