"""Unit tests for UUID normalization utilities.

Tests cover UUID format normalization for consistent 32-character hex storage.
"""

import uuid

import pytest

from app.utils.uuid_utils import is_valid_uuid, normalize_uuid, normalize_uuid_to_uuid


class TestNormalizeUuid:
	"""Test suite for normalize_uuid function."""

	def test_normalize_uuid_with_dashes(self):
		"""Test normalizing UUID with dashes to 32-char hex."""
		input_uuid = "25ea5e1c-2fd8-49e8-8062-c15e8b04492c"
		expected = "25ea5e1c2fd849e88062c15e8b04492c"

		result = normalize_uuid(input_uuid)

		assert result == expected

	def test_normalize_uuid_without_dashes(self):
		"""Test that UUID without dashes passes through unchanged."""
		input_uuid = "25ea5e1c2fd849e88062c15e8b04492c"
		expected = "25ea5e1c2fd849e88062c15e8b04492c"

		result = normalize_uuid(input_uuid)

		assert result == expected

	def test_normalize_uuid_object(self):
		"""Test normalizing uuid.UUID object to 32-char hex."""
		input_uuid = uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c")
		expected = "25ea5e1c2fd849e88062c15e8b04492c"

		result = normalize_uuid(input_uuid)

		assert result == expected

	def test_normalize_uuid_none_returns_none(self):
		"""Test that None input returns None."""
		result = normalize_uuid(None)

		assert result is None

	def test_normalize_uuid_invalid_raises_value_error(self):
		"""Test that invalid UUID raises ValueError."""
		with pytest.raises(ValueError, match="Invalid UUID"):
			normalize_uuid("not-a-uuid")

	def test_normalize_uuid_wrong_length_raises_value_error(self):
		"""Test that wrong-length string raises ValueError."""
		with pytest.raises(ValueError, match="Invalid UUID format"):
			normalize_uuid("25ea5e1c")


class TestNormalizeUuidToUuid:
	"""Test suite for normalize_uuid_to_uuid function."""

	def test_normalize_to_uuid_with_dashes(self):
		"""Test converting UUID string with dashes to UUID object."""
		input_uuid = "25ea5e1c-2fd8-49e8-8062-c15e8b04492c"

		result = normalize_uuid_to_uuid(input_uuid)

		assert isinstance(result, uuid.UUID)
		assert str(result) == input_uuid

	def test_normalize_to_uuid_without_dashes(self):
		"""Test converting UUID string without dashes to UUID object."""
		input_uuid = "25ea5e1c2fd849e88062c15e8b04492c"

		result = normalize_uuid_to_uuid(input_uuid)

		assert isinstance(result, uuid.UUID)
		assert result.hex == input_uuid

	def test_normalize_to_uuid_object(self):
		"""Test that UUID object passes through unchanged."""
		input_uuid = uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c")

		result = normalize_uuid_to_uuid(input_uuid)

		assert result == input_uuid

	def test_normalize_to_uuid_none_returns_none(self):
		"""Test that None input returns None."""
		result = normalize_uuid_to_uuid(None)

		assert result is None

	def test_normalize_to_uuid_invalid_raises_value_error(self):
		"""Test that invalid UUID raises ValueError."""
		with pytest.raises(ValueError, match="Invalid UUID"):
			normalize_uuid_to_uuid("not-a-uuid")


class TestIsValidUuid:
	"""Test suite for is_valid_uuid function."""

	def test_is_valid_uuid_with_dashes(self):
		"""Test validation of UUID with dashes."""
		assert is_valid_uuid("25ea5e1c-2fd8-49e8-8062-c15e8b04492c") is True

	def test_is_valid_uuid_without_dashes(self):
		"""Test validation of UUID without dashes."""
		assert is_valid_uuid("25ea5e1c2fd849e88062c15e8b04492c") is True

	def test_is_valid_uuid_object(self):
		"""Test validation of UUID object."""
		assert is_valid_uuid(uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c")) is True

	def test_is_valid_uuid_none_returns_false(self):
		"""Test that None returns False."""
		assert is_valid_uuid(None) is False

	def test_is_valid_uuid_invalid_returns_false(self):
		"""Test that invalid UUID returns False."""
		assert is_valid_uuid("not-a-uuid") is False

	def test_is_valid_uuid_wrong_length_returns_false(self):
		"""Test that wrong-length string returns False."""
		assert is_valid_uuid("25ea5e1c") is False


class TestUuidFormatConsistency:
	"""Test suite for UUID format consistency across operations."""

	def test_roundtrip_uuid_object_to_hex_and_back(self):
		"""Test roundtrip conversion UUID object -> hex string -> UUID object."""
		original = uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c")

		hex_string = normalize_uuid(original)
		result = normalize_uuid_to_uuid(hex_string)

		assert result == original

	def test_normalized_format_is_32_chars(self):
		"""Test that normalized format is always 32 characters."""
		test_cases = [
			"25ea5e1c-2fd8-49e8-8062-c15e8b04492c",
			"25ea5e1c2fd849e88062c15e8b04492c",
			uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c"),
		]

		for test_case in test_cases:
			result = normalize_uuid(test_case)
			assert result is not None
			assert len(result) == 32
			assert "-" not in result
