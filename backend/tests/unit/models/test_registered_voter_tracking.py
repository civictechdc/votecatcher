"""Unit tests for RegisteredVoter tracking fields."""

import uuid
from datetime import datetime

from app.data.database.model.registered_voter import RegisteredVoter


class TestRegisteredVoterTracking:
	"""Tests for RegisteredVoter upload tracking fields."""

	def test_registered_voter_tracking_fields(self):
		"""Test that tracking fields exist on RegisteredVoter."""
		region_id = uuid.uuid4()
		upload_id = uuid.uuid4()
		voter = RegisteredVoter(
			region_id=region_id,
			name_data={"first_name": "John", "last_name": "Doe"},
			address_data={"street": "123 Main St"},
			other_field_data={},
			data_hash="abc123def456",
			first_upload_id=upload_id,
			last_upload_id=upload_id,
		)
		assert voter.data_hash == "abc123def456"
		assert voter.first_upload_id == upload_id
		assert voter.last_upload_id == upload_id

	def test_registered_voter_tracking_timestamps(self):
		"""Test that tracking timestamps exist on RegisteredVoter."""
		region_id = uuid.uuid4()
		voter = RegisteredVoter(
			region_id=region_id,
			name_data={},
			address_data={},
			other_field_data={},
		)
		assert isinstance(voter.first_seen_at, datetime)
		assert isinstance(voter.last_seen_at, datetime)

	def test_registered_voter_data_hash_indexed(self):
		"""Test that data_hash field is present."""
		region_id = uuid.uuid4()
		voter = RegisteredVoter(
			region_id=region_id,
			name_data={},
			address_data={},
			other_field_data={},
			data_hash="test_hash_value",
		)
		assert voter.data_hash == "test_hash_value"

	def test_registered_voter_upload_ids_optional(self):
		"""Test that upload IDs can be None for legacy data."""
		region_id = uuid.uuid4()
		voter = RegisteredVoter(
			region_id=region_id,
			name_data={},
			address_data={},
			other_field_data={},
		)
		assert voter.first_upload_id is None
		assert voter.last_upload_id is None
