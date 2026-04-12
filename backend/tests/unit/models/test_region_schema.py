"""Unit tests for RegionSchema model."""

import uuid
from datetime import datetime

from app.data.database.model.region_schema import RegionSchema


class TestRegionSchemaModel:
    """Tests for RegionSchema model."""

    def test_region_schema_creation(self):
        """Test basic RegionSchema instantiation."""
        region_id = uuid.uuid4()
        schema = RegionSchema(
            region_id=region_id,
            name="DC Voter Roll",
            column_mappings={"VoterID": "voter_id", "FirstName": "first_name"},
            hash_fields=["first_name", "last_name", "street", "zip"],
        )
        assert schema.region_id == region_id
        assert schema.name == "DC Voter Roll"
        assert "VoterID" in schema.column_mappings
        assert schema.column_mappings["VoterID"] == "voter_id"
        assert len(schema.hash_fields) == 4
        assert "first_name" in schema.hash_fields

    def test_region_schema_defaults(self):
        """Test default values for RegionSchema."""
        region_id = uuid.uuid4()
        schema = RegionSchema(region_id=region_id, name="Test Schema")
        assert schema.column_mappings == {}
        assert schema.hash_fields == []
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_region_schema_uuid_generated(self):
        """Test that id is auto-generated as UUID."""
        region_id = uuid.uuid4()
        schema = RegionSchema(region_id=region_id, name="Test")
        assert isinstance(schema.id, uuid.UUID)

    def test_region_schema_column_mappings(self):
        """Test various column mapping configurations."""
        region_id = uuid.uuid4()
        schema = RegionSchema(
            region_id=region_id,
            name="Custom Schema",
            column_mappings={
                "VOTER_ID": "voter_id",
                "FNAME": "first_name",
                "LNAME": "last_name",
                "STREET_ADDRESS": "street",
                "CITY_NAME": "city",
                "STATE_CODE": "state",
                "ZIP_CODE": "zip",
            },
            hash_fields=["first_name", "last_name", "street", "zip"],
        )
        assert len(schema.column_mappings) == 7
        assert schema.column_mappings["FNAME"] == "first_name"
