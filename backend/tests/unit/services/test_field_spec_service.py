from uuid import uuid4

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
                id="first_name",
                csv_column_name="First_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="last_name",
                csv_column_name="Last_Name",
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
            FieldMapping(ballot_field_id="name", template="{first_name} {last_name}"),
            FieldMapping(ballot_field_id="address", template="{street_number}"),
        ],
        hash_fields=["first_name", "last_name"],
        crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=128),
    )
    defaults.update(overrides)
    return RegionFieldSpecConfig(**defaults)


class StubRepo:
    def __init__(self, specs: dict | None = None):
        self._specs: dict = specs or {}

    def find_by_region(self, region_id):
        return self._specs.get(region_id)

    def find_by_region_key(self, region_key):
        for spec in self._specs.values():
            return spec
        return None

    def save(self, spec, region_id):
        self._specs[region_id] = spec
        return spec

    def upsert(self, region_key, spec, *, region_name, country_code="US"):
        pass

    def delete(self, region_id):
        return self._specs.pop(region_id, None) is not None

    def list_regions(self):
        return []


class TestGetSpec:
    def test_get_spec_returns_spec(self):
        from app.services.field_spec_service import FieldSpecService

        region_id = uuid4()
        spec = _make_spec()
        repo = StubRepo({region_id: spec})
        service = FieldSpecService(repo)

        result = service.get_spec(region_id)
        assert result is spec

    def test_get_spec_raises_when_not_found(self):
        from app.domain.field_spec import FieldSpecNotFoundError
        from app.services.field_spec_service import FieldSpecService

        repo = StubRepo()
        service = FieldSpecService(repo)
        missing_id = uuid4()

        with pytest.raises(FieldSpecNotFoundError) as exc_info:
            service.get_spec(missing_id)
        assert exc_info.value.region_id == missing_id


class TestMapVoterToBallot:
    def test_map_voter_to_ballot(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec()
        service = FieldSpecService(StubRepo())
        voter_data = {"first_name": "Jane", "last_name": "Doe", "street_number": "123"}

        result = service.map_voter_to_ballot(spec, voter_data)
        assert result["name"] == "Jane Doe"
        assert result["address"] == "123"

    def test_map_voter_to_ballot_partial_data(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec()
        service = FieldSpecService(StubRepo())
        voter_data = {"first_name": "Jane"}

        result = service.map_voter_to_ballot(spec, voter_data)
        assert result["name"] == "Jane"
        assert result["address"] == ""

    def test_map_voter_to_ballot_empty_data(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec()
        service = FieldSpecService(StubRepo())

        result = service.map_voter_to_ballot(spec, {})
        assert result["name"] == ""
        assert result["address"] == ""


class TestValidateSpec:
    def test_validate_good_spec(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec()
        service = FieldSpecService(StubRepo())

        errors = service.validate_spec(spec)
        assert errors == []

    def test_validate_spec_with_bad_references(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec(
            field_mappings=[
                FieldMapping(ballot_field_id="nonexistent", template="{first_name}"),
            ],
        )
        service = FieldSpecService(StubRepo())

        errors = service.validate_spec(spec)
        assert any("unknown ballot field" in e.lower() for e in errors)

    def test_validate_spec_empty_ballot_fields(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec(
            ballot_fields=[],
            field_mappings=[],
            hash_fields=[],
        )
        service = FieldSpecService(StubRepo())

        errors = service.validate_spec(spec)
        assert any("ballot field" in e.lower() for e in errors)

    def test_validate_spec_empty_voter_reg_fields(self):
        from app.services.field_spec_service import FieldSpecService

        spec = _make_spec(
            voter_reg_fields=[],
            hash_fields=[],
            field_mappings=[],
        )
        service = FieldSpecService(StubRepo())

        errors = service.validate_spec(spec)
        assert any("voter reg field" in e.lower() for e in errors)
