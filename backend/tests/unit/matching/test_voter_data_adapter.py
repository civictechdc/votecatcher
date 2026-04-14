from app.domain.field_spec import VoterRegField
from app.domain.voter import RegisteredVoter
from app.matching.voter_data_adapter import flatten_voter_data
from uuid import uuid4


def _make_voter(
    name_data: dict | None = None,
    address_data: dict | None = None,
    other_field_data: dict | None = None,
) -> RegisteredVoter:
    return RegisteredVoter(
        id=1,
        region_id=uuid4(),
        name_data=name_data or {},
        address_data=address_data or {},
        other_field_data=other_field_data or {},
    )


def _dc_name_fields() -> list[VoterRegField]:
    return [
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
    ]


def _dc_address_fields() -> list[VoterRegField]:
    return [
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
    ]


def _dc_geo_fields() -> list[VoterRegField]:
    return [
        VoterRegField(
            id="ward", csv_column_name="WARD", data_type="integer", category="geography"
        ),
        VoterRegField(
            id="precinct",
            csv_column_name="Precinct",
            data_type="text",
            category="geography",
        ),
    ]


def _dc_reg_fields() -> list[VoterRegField]:
    return [
        VoterRegField(
            id="party",
            csv_column_name="Party",
            data_type="text",
            category="registration",
        ),
    ]


class TestFlattenVoterData:
    def test_flatten_name_fields(self):
        voter = _make_voter(
            name_data={
                "first_name": "Jane",
                "middle_name": "A",
                "last_name": "Doe",
            }
        )
        fields = _dc_name_fields()
        result = flatten_voter_data(voter, fields)
        assert result["first_name"] == "Jane"
        assert result["middle_name"] == "A"
        assert result["last_name"] == "Doe"

    def test_flatten_address_fields(self):
        voter = _make_voter(
            address_data={
                "street_number": "123",
                "street_name": "Main",
                "street_type": "St",
                "zip_code": "20001",
            }
        )
        fields = _dc_address_fields()
        result = flatten_voter_data(voter, fields)
        assert result["street_number"] == "123"
        assert result["street_name"] == "Main"
        assert result["street_type"] == "St"
        assert result["zip_code"] == "20001"

    def test_flatten_missing_blob_returns_empty_strings(self):
        voter = _make_voter()
        fields = _dc_name_fields() + _dc_address_fields()
        result = flatten_voter_data(voter, fields)
        for field in fields:
            assert result[field.id] == ""

    def test_flatten_preserves_all_categories(self):
        voter = _make_voter(
            name_data={"first_name": "Jane", "last_name": "Doe"},
            address_data={"street_number": "123", "street_name": "Main"},
            other_field_data={"ward": "3", "party": "DEM"},
        )
        fields = (
            _dc_name_fields()
            + _dc_address_fields()
            + _dc_geo_fields()
            + _dc_reg_fields()
        )
        result = flatten_voter_data(voter, fields)
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Doe"
        assert result["street_number"] == "123"
        assert result["ward"] == "3"
        assert result["party"] == "DEM"

    def test_flatten_with_empty_blobs(self):
        voter = RegisteredVoter(
            id=1,
            region_id=uuid4(),
            name_data={},
            address_data={},
            other_field_data={},
        )
        fields = _dc_name_fields()
        result = flatten_voter_data(voter, fields)
        assert result["first_name"] == ""
        assert result["last_name"] == ""
