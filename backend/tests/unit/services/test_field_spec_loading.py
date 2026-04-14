"""Tests for field spec loading from JSON5 source files.

Covers: parsing, validation, upsert, error handling, and startup integration.
"""

import json
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


def _make_spec(**overrides) -> RegionFieldSpecConfig:
    defaults = dict(
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
        crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=128),
    )
    defaults.update(overrides)
    return RegionFieldSpecConfig(**defaults)


class UpsertTrackingRepo:
    def __init__(self):
        self.upserted: list[tuple[str, RegionFieldSpecConfig, str, str]] = []

    def find_by_region(self, region_id: UUID):
        return None

    def find_by_region_key(self, region_key: str):
        return None

    def save(self, spec, region_id):
        return spec

    def upsert(
        self,
        region_key: str,
        spec: RegionFieldSpecConfig,
        *,
        region_name: str,
        country_code: str = "US",
    ):
        self.upserted.append((region_key, spec, region_name, country_code))

    def delete(self, region_id: UUID):
        return False

    def list_regions(self):
        return []


class TestLoadValidSpec:
    def test_load_valid_spec_parses_and_upserts(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        spec_data = {
            "region_name": "Test Region",
            "country_code": "US",
            "ballot_fields": [
                {
                    "id": "name",
                    "label": "Full Name",
                    "field_type": "text",
                    "required_for_matching": True,
                    "match_weight": 1.0,
                },
            ],
            "voter_reg_fields": [
                {
                    "id": "last_name",
                    "csv_column_name": "Last_Name",
                    "data_type": "text",
                    "category": "name",
                },
                {
                    "id": "first_name",
                    "csv_column_name": "First_Name",
                    "data_type": "text",
                    "category": "name",
                },
            ],
            "field_mappings": [
                {"ballot_field_id": "name", "template": "{first_name} {last_name}"},
            ],
            "hash_fields": ["last_name", "first_name"],
            "crop_config": {"top_crop": 0.1, "bottom_crop": 0.9, "base_threshold": 128},
        }

        spec_file = tmp_path / "test.json5"
        spec_file.write_text(json.dumps(spec_data))

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 1
        assert errors == []
        assert len(repo.upserted) == 1
        key, spec, rname, ccode = repo.upserted[0]
        assert key == "TEST"
        assert rname == "Test Region"
        assert ccode == "US"
        assert spec.region_name == "Test Region"


class TestLoadInvalidSchema:
    def test_load_invalid_json5_reports_error(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        bad_file = tmp_path / "bad.json5"
        bad_file.write_text("{ this is not valid json5 }}}")

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 0
        assert len(errors) == 1
        assert "bad.json5" in errors[0]

    def test_load_invalid_integrity_reports_error(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        spec_data = {
            "region_name": "Bad Region",
            "country_code": "US",
            "ballot_fields": [
                {
                    "id": "name",
                    "label": "Full Name",
                    "field_type": "text",
                    "required_for_matching": True,
                    "match_weight": 1.0,
                },
            ],
            "voter_reg_fields": [
                {
                    "id": "last_name",
                    "csv_column_name": "Last_Name",
                    "data_type": "text",
                    "category": "name",
                },
            ],
            "field_mappings": [
                {"ballot_field_id": "nonexistent", "template": "{last_name}"},
            ],
            "hash_fields": ["nonexistent_field"],
            "crop_config": {"top_crop": 0.1, "bottom_crop": 0.9, "base_threshold": 128},
        }

        spec_file = tmp_path / "bad_integrity.json5"
        spec_file.write_text(json.dumps(spec_data))

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 0
        assert len(errors) == 1
        assert "bad_integrity.json5" in errors[0]


class TestLoadAllSpecs:
    def test_load_multiple_specs(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        for name in ["alpha", "beta"]:
            spec_data = {
                "region_name": f"{name.title()} Region",
                "country_code": "US",
                "ballot_fields": [
                    {
                        "id": "name",
                        "label": "Full Name",
                        "field_type": "text",
                        "required_for_matching": True,
                        "match_weight": 1.0,
                    },
                ],
                "voter_reg_fields": [
                    {
                        "id": "last_name",
                        "csv_column_name": "Last_Name",
                        "data_type": "text",
                        "category": "name",
                    },
                    {
                        "id": "first_name",
                        "csv_column_name": "First_Name",
                        "data_type": "text",
                        "category": "name",
                    },
                ],
                "field_mappings": [
                    {"ballot_field_id": "name", "template": "{first_name} {last_name}"},
                ],
                "hash_fields": ["last_name", "first_name"],
                "crop_config": {
                    "top_crop": 0.1,
                    "bottom_crop": 0.9,
                    "base_threshold": 128,
                },
            }
            (tmp_path / f"{name}.json5").write_text(json.dumps(spec_data))

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 2
        assert errors == []
        assert len(repo.upserted) == 2
        keys = {u[0] for u in repo.upserted}
        assert keys == {"ALPHA", "BETA"}

    def test_upsert_updates_existing_spec(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        spec_data = {
            "region_name": "Updated Region",
            "country_code": "US",
            "ballot_fields": [
                {
                    "id": "name",
                    "label": "Full Name",
                    "field_type": "text",
                    "required_for_matching": True,
                    "match_weight": 1.0,
                },
            ],
            "voter_reg_fields": [
                {
                    "id": "last_name",
                    "csv_column_name": "Last_Name",
                    "data_type": "text",
                    "category": "name",
                },
                {
                    "id": "first_name",
                    "csv_column_name": "First_Name",
                    "data_type": "text",
                    "category": "name",
                },
            ],
            "field_mappings": [
                {"ballot_field_id": "name", "template": "{first_name} {last_name}"},
            ],
            "hash_fields": ["last_name", "first_name"],
            "crop_config": {"top_crop": 0.2, "bottom_crop": 0.8, "base_threshold": 90},
        }

        spec_file = tmp_path / "dc.json5"
        spec_file.write_text(json.dumps(spec_data))

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)

        service.load_all_specs(tmp_path)
        assert len(repo.upserted) == 1

        count, errors = service.load_all_specs(tmp_path)
        assert count == 1
        assert errors == []
        assert len(repo.upserted) == 2

        _, spec, _, _ = repo.upserted[-1]
        assert spec.region_name == "Updated Region"


class TestLoadEdgeCases:
    def test_missing_regions_dir_returns_zero(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        nonexistent = tmp_path / "no_such_dir"
        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)

        count, errors = service.load_all_specs(nonexistent)

        assert count == 0
        assert errors == []
        assert len(repo.upserted) == 0

    def test_empty_regions_dir_returns_zero(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(empty_dir)

        assert count == 0
        assert errors == []

    def test_ignores_non_json5_files(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        (tmp_path / "readme.txt").write_text("not a spec")
        (tmp_path / "notes.md").write_text("# Notes")

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 0
        assert errors == []


class TestRegionKeyNormalization:
    def test_region_key_uppercased_from_filename(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        spec_data = {
            "region_name": "Test",
            "country_code": "US",
            "ballot_fields": [
                {
                    "id": "name",
                    "label": "Name",
                    "field_type": "text",
                    "required_for_matching": True,
                    "match_weight": 1.0,
                },
            ],
            "voter_reg_fields": [
                {
                    "id": "last_name",
                    "csv_column_name": "Last_Name",
                    "data_type": "text",
                    "category": "name",
                },
                {
                    "id": "first_name",
                    "csv_column_name": "First_Name",
                    "data_type": "text",
                    "category": "name",
                },
            ],
            "field_mappings": [
                {"ballot_field_id": "name", "template": "{first_name} {last_name}"},
            ],
            "hash_fields": ["last_name", "first_name"],
            "crop_config": {"top_crop": 0.1, "bottom_crop": 0.9, "base_threshold": 128},
        }
        (tmp_path / "dc.json5").write_text(json.dumps(spec_data))

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        service.load_all_specs(tmp_path)

        assert len(repo.upserted) == 1
        assert repo.upserted[0][0] == "DC"


class TestDcSourceSpec:
    def test_dc_spec_loads_successfully(self):
        import json5 as j5

        spec_path = Path(__file__).resolve().parents[3] / "app" / "regions" / "dc.json5"
        assert spec_path.exists(), f"DC spec not found at {spec_path}"

        raw = spec_path.read_text()
        data = j5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)

        integrity_errors = spec.validate_integrity()
        assert integrity_errors == [], f"DC spec integrity errors: {integrity_errors}"

    def test_dc_spec_loads_via_service(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        spec_path = Path(__file__).resolve().parents[3] / "app" / "regions" / "dc.json5"
        raw = spec_path.read_text()
        (tmp_path / "dc.json5").write_text(raw)

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 1
        assert errors == []
        assert len(repo.upserted) == 1
        key, spec, region_name, country_code = repo.upserted[0]
        assert key == "DC"
        assert region_name == "District of Columbia"
        assert country_code == "US"
        assert len(spec.ballot_fields) == 4
        assert len(spec.voter_reg_fields) == 21


class TestFailFastOnError:
    def test_load_all_specs_collects_all_errors(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService

        (tmp_path / "bad1.json5").write_text("{not valid}}")
        (tmp_path / "bad2.json5").write_text("{also not valid")

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)
        count, errors = service.load_all_specs(tmp_path)

        assert count == 0
        assert len(errors) == 2

    def test_load_raises_on_errors_when_fail_fast(self, tmp_path: Path):
        from app.services.field_spec_service import FieldSpecService, SpecLoadingError

        (tmp_path / "bad.json5").write_text("{not valid}}")

        repo = UpsertTrackingRepo()
        service = FieldSpecService(repo)

        with pytest.raises(SpecLoadingError):
            service.load_all_specs(tmp_path, fail_fast=True)
