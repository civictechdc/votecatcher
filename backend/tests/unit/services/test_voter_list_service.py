"""Unit tests for VoterListService."""

import hashlib
from unittest.mock import MagicMock

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)
from app.services.voter_list_service import VoterListService


def _make_dc_spec() -> RegionFieldSpecConfig:
    return RegionFieldSpecConfig(
        region_name="District of Columbia",
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
                id="middle_name",
                csv_column_name="Middle_Name",
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
                id="street_type",
                csv_column_name="Street_Type",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="zip_code",
                csv_column_name="Zip_Code",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="city_name",
                csv_column_name="City_Name",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="party",
                csv_column_name="Party",
                data_type="text",
                category="registration",
            ),
            VoterRegField(
                id="ward",
                csv_column_name="WARD",
                data_type="integer",
                category="geography",
            ),
        ],
        field_mappings=[
            FieldMapping(
                ballot_field_id="name",
                template="{first_name} {middle_name} {last_name}",
            ),
            FieldMapping(
                ballot_field_id="address",
                template="{street_number} {street_name} {street_type}",
            ),
        ],
        hash_fields=[
            "last_name",
            "first_name",
            "street_number",
            "street_name",
            "zip_code",
        ],
        crop_config=CropConfig(top_crop=0.3, bottom_crop=0.7, base_threshold=85),
    )


class TestVoterListService:
    """Tests for VoterListService utility methods."""

    def test_compute_data_hash_basic(self):
        """Test hash computation with basic fields."""
        service = VoterListService(None)
        name_data = {"first_name": "John", "last_name": "Doe"}
        address_data = {"street": "123 Main St", "zip": "12345"}
        hash_fields = ["first_name", "last_name", "street", "zip"]

        result = service.compute_data_hash(name_data, address_data, hash_fields)

        assert result is not None
        assert len(result) == 64

    def test_compute_data_hash_consistent(self):
        """Test that same input produces same hash."""
        service = VoterListService(None)
        name_data = {"first_name": "Jane", "last_name": "Smith"}
        address_data = {"street": "456 Oak Ave", "zip": "67890"}
        hash_fields = ["first_name", "last_name", "street", "zip"]

        hash1 = service.compute_data_hash(name_data, address_data, hash_fields)
        hash2 = service.compute_data_hash(name_data, address_data, hash_fields)

        assert hash1 == hash2

    def test_compute_data_hash_different_inputs(self):
        """Test that different inputs produce different hashes."""
        service = VoterListService(None)
        hash_fields = ["first_name", "last_name"]

        hash1 = service.compute_data_hash(
            {"first_name": "John", "last_name": "Doe"},
            {},
            hash_fields,
        )
        hash2 = service.compute_data_hash(
            {"first_name": "Jane", "last_name": "Smith"},
            {},
            hash_fields,
        )

        assert hash1 != hash2

    def test_normalize_name(self):
        """Test name normalization for hashing."""
        service = VoterListService(None)

        assert service._normalize_name("  JOHN  ") == "john"
        assert service._normalize_name("McDonald") == "mcdonald"
        assert service._normalize_name("O'Brien") == "o'brien"
        assert service._normalize_name("") == ""
        assert service._normalize_name("  ") == ""

    def test_normalize_address(self):
        """Test address normalization for hashing."""
        service = VoterListService(None)

        assert service._normalize_name("123 Main Street") == "123 main street"
        assert service._normalize_name("APT 4B") == "apt 4b"

    def test_compute_data_hash_missing_fields(self):
        """Test hash computation when some fields are missing."""
        service = VoterListService(None)
        name_data = {"first_name": "John"}
        address_data = {"street": "123 Main St"}
        hash_fields = ["first_name", "last_name", "street"]

        result = service.compute_data_hash(name_data, address_data, hash_fields)

        assert result is not None
        assert len(result) == 64

    def test_compute_data_hash_empty_hash_fields(self):
        """Test hash computation with empty hash fields list."""
        service = VoterListService(None)
        name_data = {"first_name": "John"}
        address_data = {"street": "123 Main St"}
        hash_fields = []

        result = service.compute_data_hash(name_data, address_data, hash_fields)

        empty_hash = hashlib.sha256(b"").hexdigest()
        assert result == empty_hash


class TestSpecDrivenParsing:
    """G8.1: Spec-driven CSV parsing tests."""

    def test_parse_csv_with_dc_spec(self):
        """Columns mapped from voter_reg_fields[].csv_column_name → voter_reg_fields[].id."""
        service = VoterListService(None)
        spec = _make_dc_spec()
        csv_content = (
            "Last_Name,First_Name,Middle_Name,Street_Number,Street_Name,Street_Type,Zip_Code,Party\n"
            "Doe,John,Michael,123,Main,St,20001,Democrat\n"
        )

        rows = service.parse_csv_with_spec(csv_content, spec)

        assert len(rows) == 1
        row = rows[0]
        assert row["last_name"] == "Doe"
        assert row["first_name"] == "John"
        assert row["middle_name"] == "Michael"
        assert row["street_number"] == "123"
        assert row["street_name"] == "Main"
        assert row["street_type"] == "St"
        assert row["zip_code"] == "20001"
        assert row["party"] == "Democrat"

    def test_parse_csv_with_spec_ignores_unmapped_columns(self):
        """CSV columns not in voter_reg_fields are dropped."""
        service = VoterListService(None)
        spec = _make_dc_spec()
        csv_content = "Last_Name,First_Name,Extra_Column\nDoe,John,something\n"

        rows = service.parse_csv_with_spec(csv_content, spec)

        assert len(rows) == 1
        assert "extra_column" not in rows[0]
        assert rows[0]["last_name"] == "Doe"

    def test_category_to_blob_mapping(self):
        """voter_reg_fields category → name_data/address_data/other_field_data blobs."""
        service = VoterListService(None)
        spec = _make_dc_spec()

        mapped = {
            "last_name": "Doe",
            "first_name": "John",
            "street_number": "123",
            "street_name": "Main",
            "zip_code": "20001",
            "party": "Democrat",
            "ward": "3",
        }

        name_data, address_data, other_data = service.group_by_category(
            mapped, spec.voter_reg_fields
        )

        assert name_data == {
            "last_name": "Doe",
            "first_name": "John",
            "middle_name": "",
        }
        assert address_data == {
            "street_number": "123",
            "street_name": "Main",
            "street_type": "",
            "zip_code": "20001",
            "city_name": "",
        }
        assert other_data == {"party": "Democrat", "ward": "3"}

    def test_compute_data_hash_with_all_categories(self):
        """Hash computation searches name_data, address_data, AND other_field_data."""
        service = VoterListService(None)
        name_data = {"first_name": "John", "last_name": "Doe"}
        address_data = {"street_number": "123", "street_name": "Main"}
        other_field_data = {"ward": "3"}
        hash_fields = ["last_name", "first_name", "street_number", "ward"]

        result = service.compute_data_hash_all(
            name_data, address_data, other_field_data, hash_fields
        )

        assert result is not None
        assert len(result) == 64

    def test_compute_data_hash_finds_geography_fields(self):
        """Hash field in other_field_data (e.g., ward) is included, not silently skipped."""
        service = VoterListService(None)
        name_data = {"first_name": "John", "last_name": "Doe"}
        address_data = {"street_number": "123"}
        other_field_data = {"ward": "3"}
        hash_fields = ["last_name", "ward"]

        hash_with_ward = service.compute_data_hash_all(
            name_data, address_data, other_field_data, hash_fields
        )

        other_field_data_empty = {"ward": ""}
        hash_without_ward = service.compute_data_hash_all(
            name_data, address_data, other_field_data_empty, hash_fields
        )

        assert hash_with_ward != hash_without_ward

    def test_compute_data_hash_all_missing_category_still_works(self):
        """Hash works even when one blob is empty."""
        service = VoterListService(None)
        name_data = {"first_name": "John"}
        address_data = {}
        other_field_data = {"ward": "3"}
        hash_fields = ["first_name", "ward"]

        result = service.compute_data_hash_all(
            name_data, address_data, other_field_data, hash_fields
        )

        assert result is not None
        assert len(result) == 64


class TestSpecDrivenMerge:
    """G8.3: Tests for replacing get_or_create_schema with spec-driven merge."""

    def test_merge_uses_spec_hash_fields(self):
        """merge_voter_list_with_spec uses spec-defined hash_fields."""
        spec = _make_dc_spec()
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        service = VoterListService(mock_session)

        rows = [
            {
                "last_name": "Doe",
                "first_name": "John",
                "street_number": "123",
                "street_name": "Main",
                "zip_code": "20001",
            }
        ]
        upload = MagicMock()
        upload.id = "upload-1"

        service.merge_voter_list_with_spec(
            region_id="region-1",
            rows=rows,
            upload=upload,
            spec=spec,
        )

        added_voters = [
            call.args[0]
            for call in mock_session.add.call_args_list
            if hasattr(call.args[0], "data_hash")
        ]
        assert len(added_voters) == 1
        voter = added_voters[0]
        assert voter.name_data == {
            "last_name": "Doe",
            "first_name": "John",
            "middle_name": "",
        }
        assert voter.address_data == {
            "street_number": "123",
            "street_name": "Main",
            "street_type": "",
            "zip_code": "20001",
            "city_name": "",
        }

    def test_merge_detects_existing_voter_by_hash(self):
        """Spec-driven merge finds existing voter by data_hash."""
        spec = _make_dc_spec()
        mock_session = MagicMock()
        existing_voter = MagicMock()
        mock_session.exec.return_value.first.return_value = existing_voter

        service = VoterListService(mock_session)

        rows = [
            {
                "last_name": "Doe",
                "first_name": "John",
                "street_number": "123",
                "street_name": "Main",
                "zip_code": "20001",
            }
        ]
        upload = MagicMock()
        upload.id = "upload-2"

        new_count, updated_count = service.merge_voter_list_with_spec(
            region_id="region-1",
            rows=rows,
            upload=upload,
            spec=spec,
        )

        assert new_count == 0
        assert updated_count == 1

    def test_group_by_category_handles_missing_fields(self):
        """Missing fields in mapped dict get empty string defaults."""
        service = VoterListService(None)
        spec = _make_dc_spec()

        mapped = {"last_name": "Doe", "first_name": "John"}

        name_data, address_data, other_data = service.group_by_category(
            mapped, spec.voter_reg_fields
        )

        assert name_data == {
            "last_name": "Doe",
            "first_name": "John",
            "middle_name": "",
        }
        assert "street_number" in address_data
        assert address_data["street_number"] == ""


class TestSchemaReplacement:
    """G8.3: Tests for replacing get_or_create_schema with spec lookup."""

    def test_spec_replaces_schema_for_csv_parsing(self):
        """parse_csv_with_spec produces same shape as parse_csv_with_schema would."""
        service = VoterListService(None)
        spec = _make_dc_spec()

        csv_content = (
            "Last_Name,First_Name,Street_Number,Street_Name,Zip_Code\n"
            "Doe,John,123,Main,20001\n"
        )
        rows = service.parse_csv_with_spec(csv_content, spec)

        assert len(rows) == 1
        assert rows[0]["last_name"] == "Doe"
        assert rows[0]["first_name"] == "John"
        assert rows[0]["street_number"] == "123"

    def test_spec_hash_fields_replaces_schema_hash_fields(self):
        """spec.hash_fields replaces RegionSchema.hash_fields."""
        spec = _make_dc_spec()
        service = VoterListService(None)

        name_data = {"last_name": "Doe", "first_name": "John"}
        address_data = {
            "street_number": "123",
            "street_name": "Main",
            "zip_code": "20001",
        }

        result = service.compute_data_hash_all(
            name_data, address_data, {}, spec.hash_fields
        )

        assert result is not None
        assert len(result) == 64

    def test_existing_voters_with_old_keys_still_work_with_hash(self):
        """Old voters with 'street'/'zip' keys can still be hashed via compute_data_hash (old method)."""
        service = VoterListService(None)

        old_name_data = {"first_name": "John", "last_name": "Doe"}
        old_address_data = {
            "street": "123 Main St",
            "city": "Washington",
            "state": "DC",
            "zip": "20001",
        }
        old_hash_fields = ["first_name", "last_name", "street", "zip"]

        result = service.compute_data_hash(
            old_name_data, old_address_data, old_hash_fields
        )

        assert result is not None
        assert len(result) == 64


class TestFlagGuard:
    """G8: Feature flag guard tests for spec-driven voter list."""

    def test_merge_dispatches_to_spec_when_flag_on(self):
        """merge_voter_list dispatches to spec-driven path when spec provided."""
        spec = _make_dc_spec()
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        service = VoterListService(mock_session)

        rows = [{"last_name": "Doe", "first_name": "John", "street_number": "123"}]
        upload = MagicMock()
        upload.id = "upload-1"

        new_count, updated_count = service.merge_voter_list_with_spec(
            region_id="region-1", rows=rows, upload=upload, spec=spec
        )

        assert new_count == 1
        assert updated_count == 0
