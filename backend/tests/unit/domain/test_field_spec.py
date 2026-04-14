from pydantic import ValidationError

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)


class TestBallotField:
    def test_create_ballot_field(self):
        f = BallotField(
            id="name",
            label="Full Name",
            field_type="text",
            required_for_matching=True,
            match_weight=1.0,
        )
        assert f.id == "name"
        assert f.match_weight == 1.0

    def test_ballot_field_is_frozen(self):
        f = BallotField(
            id="name",
            label="Name",
            field_type="text",
            required_for_matching=True,
        )
        try:
            f.id = "changed"
            assert False, "Should be frozen"
        except ValidationError:
            pass

    def test_match_weight_must_be_non_negative(self):
        try:
            BallotField(
                id="x",
                label="X",
                field_type="text",
                required_for_matching=True,
                match_weight=-1.0,
            )
            assert False, "Should reject negative weight"
        except ValidationError:
            pass

    def test_field_type_must_be_valid(self):
        try:
            BallotField(
                id="x",
                label="X",
                field_type="invalid",
                required_for_matching=True,
            )
            assert False, "Should reject invalid field_type"
        except ValidationError:
            pass

    def test_default_match_weight(self):
        f = BallotField(
            id="x",
            label="X",
            field_type="text",
            required_for_matching=True,
        )
        assert f.match_weight == 1.0


class TestVoterRegField:
    def test_create_voter_reg_field(self):
        f = VoterRegField(
            id="first_name",
            csv_column_name="First_Name",
            data_type="text",
            category="name",
        )
        assert f.id == "first_name"
        assert f.csv_column_name == "First_Name"

    def test_voter_reg_field_is_frozen(self):
        f = VoterRegField(
            id="x",
            csv_column_name="X",
            data_type="text",
            category="name",
        )
        try:
            f.id = "changed"
            assert False, "Should be frozen"
        except ValidationError:
            pass

    def test_invalid_data_type(self):
        try:
            VoterRegField(
                id="x",
                csv_column_name="X",
                data_type="float",
                category="name",
            )
            assert False, "Should reject invalid data_type"
        except ValidationError:
            pass

    def test_invalid_category(self):
        try:
            VoterRegField(
                id="x",
                csv_column_name="X",
                data_type="text",
                category="other",
            )
            assert False, "Should reject invalid category"
        except ValidationError:
            pass


class TestFieldMapping:
    def test_create_field_mapping(self):
        m = FieldMapping(ballot_field_id="name", template="{first_name} {last_name}")
        assert m.ballot_field_id == "name"
        assert "{first_name}" in m.template

    def test_field_mapping_is_frozen(self):
        m = FieldMapping(ballot_field_id="name", template="{first_name}")
        try:
            m.ballot_field_id = "changed"
            assert False, "Should be frozen"
        except ValidationError:
            pass


class TestCropConfig:
    def test_create_crop_config(self):
        c = CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=128)
        assert c.top_crop == 0.1
        assert c.bottom_crop == 0.9

    def test_crop_config_is_frozen(self):
        c = CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=128)
        try:
            c.top_crop = 0.5
            assert False, "Should be frozen"
        except ValidationError:
            pass

    def test_top_crop_must_be_in_range(self):
        try:
            CropConfig(top_crop=1.5, bottom_crop=0.9, base_threshold=128)
            assert False, "Should reject out-of-range top_crop"
        except ValidationError:
            pass

    def test_bottom_crop_must_be_in_range(self):
        try:
            CropConfig(top_crop=0.1, bottom_crop=1.5, base_threshold=128)
            assert False, "Should reject out-of-range bottom_crop"
        except ValidationError:
            pass

    def test_base_threshold_must_be_in_range(self):
        try:
            CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=300)
            assert False, "Should reject out-of-range base_threshold"
        except ValidationError:
            pass


def _make_spec(**overrides) -> RegionFieldSpecConfig:
    defaults = dict(
        region_name="Test Region",
        country_code="US",
        ballot_fields=[
            BallotField(
                id="name",
                label="Name",
                field_type="text",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="address",
                label="Address",
                field_type="address",
                required_for_matching=True,
                match_weight=0.8,
            ),
            BallotField(
                id="ward",
                label="Ward",
                field_type="integer",
                required_for_matching=False,
                match_weight=0.3,
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
            VoterRegField(
                id="street_name",
                csv_column_name="Street_Name",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="city", csv_column_name="City", data_type="text", category="address"
            ),
            VoterRegField(
                id="zip_code",
                csv_column_name="Zip_Code",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="ward",
                csv_column_name="Ward",
                data_type="integer",
                category="geography",
            ),
        ],
        field_mappings=[
            FieldMapping(ballot_field_id="name", template="{first_name} {last_name}"),
            FieldMapping(
                ballot_field_id="address",
                template="{street_number} {street_name}, {city} {zip_code}",
            ),
            FieldMapping(ballot_field_id="ward", template="{ward}"),
        ],
        hash_fields=[
            "first_name",
            "last_name",
            "street_number",
            "street_name",
            "zip_code",
        ],
        crop_config=CropConfig(top_crop=0.1, bottom_crop=0.9, base_threshold=128),
    )
    defaults.update(overrides)
    return RegionFieldSpecConfig(**defaults)


class TestRegionFieldSpecConfig:
    def test_create_full_spec(self):
        spec = _make_spec()
        assert spec.region_name == "Test Region"
        assert len(spec.ballot_fields) == 3
        assert len(spec.voter_reg_fields) == 7

    def test_get_mapping_for_existing_field(self):
        spec = _make_spec()
        mapping = spec.get_mapping_for("name")
        assert mapping is not None
        assert mapping.ballot_field_id == "name"

    def test_get_mapping_for_missing_field_returns_none(self):
        spec = _make_spec()
        assert spec.get_mapping_for("nonexistent") is None

    def test_matchable_fields_excludes_zero_weight(self):
        spec = _make_spec(
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Name",
                    field_type="text",
                    required_for_matching=True,
                    match_weight=1.0,
                ),
                BallotField(
                    id="notes",
                    label="Notes",
                    field_type="text",
                    required_for_matching=True,
                    match_weight=0.0,
                ),
                BallotField(
                    id="ward",
                    label="Ward",
                    field_type="integer",
                    required_for_matching=False,
                    match_weight=0.3,
                ),
            ],
        )
        matchable = spec.matchable_fields()
        ids = {f.id for f in matchable}
        assert "name" in ids
        assert "notes" not in ids
        assert "ward" not in ids

    def test_matchable_fields_excludes_not_required(self):
        spec = _make_spec()
        matchable = spec.matchable_fields()
        ids = {f.id for f in matchable}
        assert "ward" not in ids

    def test_total_match_weight(self):
        spec = _make_spec(
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Name",
                    field_type="text",
                    required_for_matching=True,
                    match_weight=1.0,
                ),
                BallotField(
                    id="address",
                    label="Address",
                    field_type="address",
                    required_for_matching=True,
                    match_weight=0.8,
                ),
            ],
        )
        assert spec.total_match_weight() == 1.8

    def test_validate_integrity_good_spec(self):
        spec = _make_spec()
        errors = spec.validate_integrity()
        assert errors == []

    def test_validate_duplicate_ballot_field_ids(self):
        spec = _make_spec(
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Name",
                    field_type="text",
                    required_for_matching=True,
                ),
                BallotField(
                    id="name",
                    label="Name2",
                    field_type="text",
                    required_for_matching=True,
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("Duplicate ballot field ID" in e for e in errors)

    def test_validate_duplicate_voter_reg_field_ids(self):
        spec = _make_spec(
            voter_reg_fields=[
                VoterRegField(
                    id="first_name",
                    csv_column_name="First",
                    data_type="text",
                    category="name",
                ),
                VoterRegField(
                    id="first_name",
                    csv_column_name="Second",
                    data_type="text",
                    category="name",
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("Duplicate voter reg field ID" in e for e in errors)

    def test_validate_duplicate_csv_column_names(self):
        spec = _make_spec(
            voter_reg_fields=[
                VoterRegField(
                    id="a", csv_column_name="Col", data_type="text", category="name"
                ),
                VoterRegField(
                    id="b", csv_column_name="Col", data_type="text", category="name"
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("Duplicate CSV column name" in e for e in errors)

    def test_validate_mapping_references_unknown_ballot_field(self):
        spec = _make_spec(
            field_mappings=[
                FieldMapping(ballot_field_id="nonexistent", template="{first_name}"),
            ],
        )
        errors = spec.validate_integrity()
        assert any("unknown ballot field" in e for e in errors)

    def test_validate_template_references_unknown_voter_field(self):
        spec = _make_spec(
            field_mappings=[
                FieldMapping(
                    ballot_field_id="name", template="{first_name} {unknown_field}"
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("unknown voter field" in e for e in errors)

    def test_validate_matchable_field_without_mapping(self):
        spec = _make_spec(
            ballot_fields=[
                BallotField(
                    id="name",
                    label="Name",
                    field_type="text",
                    required_for_matching=True,
                ),
                BallotField(
                    id="orphan",
                    label="Orphan",
                    field_type="text",
                    required_for_matching=True,
                ),
            ],
            field_mappings=[
                FieldMapping(
                    ballot_field_id="name", template="{first_name} {last_name}"
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("no field mapping" in e for e in errors)

    def test_validate_hash_field_references_unknown(self):
        spec = _make_spec(hash_fields=["first_name", "nonexistent"])
        errors = spec.validate_integrity()
        assert any("Hash field references unknown" in e for e in errors)

    def test_validate_no_matchable_fields(self):
        spec = _make_spec(
            ballot_fields=[
                BallotField(
                    id="ward",
                    label="Ward",
                    field_type="integer",
                    required_for_matching=False,
                    match_weight=0.3,
                ),
            ],
        )
        errors = spec.validate_integrity()
        assert any("at least one matchable" in e for e in errors)

    def test_validate_crop_config_top_not_less_than_bottom(self):
        spec = _make_spec(
            crop_config=CropConfig(top_crop=0.9, bottom_crop=0.1, base_threshold=128)
        )
        errors = spec.validate_integrity()
        assert any("top_crop" in e and "bottom_crop" in e for e in errors)

    def test_spec_is_frozen(self):
        spec = _make_spec()
        try:
            spec.region_name = "changed"
            assert False, "Should be frozen"
        except ValidationError:
            pass

    def test_default_country_code(self):
        spec = _make_spec()
        assert spec.country_code == "US"
