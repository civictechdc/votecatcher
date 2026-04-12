"""Unit tests for UUID normalization utilities.

Tests cover UUID format normalization for consistent 32-character hex storage.
"""

import uuid

import pytest

from app.utils.uuid_utils import is_valid_uuid, normalize_uuid, normalize_uuid_to_uuid

_UUID_SEED = "a" * 8 + "-bbbb-cccc-dddd-" + "e" * 12
_TEST_UUID = uuid.UUID(_UUID_SEED)
_TEST_UUID_STR = str(_TEST_UUID)
_TEST_UUID_HEX = _TEST_UUID.hex
_PARTIAL_HEX = _TEST_UUID_HEX[:8]


class TestNormalizeUuid:
    """Test suite for normalize_uuid function."""

    def test_normalize_uuid_with_dashes(self):
        """Test normalizing UUID with dashes to 32-char hex."""
        result = normalize_uuid(_TEST_UUID_STR)
        assert result == _TEST_UUID_HEX

    def test_normalize_uuid_without_dashes(self):
        """Test that UUID without dashes passes through unchanged."""
        result = normalize_uuid(_TEST_UUID_HEX)
        assert result == _TEST_UUID_HEX

    def test_normalize_uuid_object(self):
        """Test normalizing uuid.UUID object to 32-char hex."""
        result = normalize_uuid(_TEST_UUID)
        assert result == _TEST_UUID_HEX

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
            normalize_uuid(_PARTIAL_HEX)


class TestNormalizeUuidToUuid:
    """Test suite for normalize_uuid_to_uuid function."""

    def test_normalize_to_uuid_with_dashes(self):
        """Test converting UUID string with dashes to UUID object."""
        result = normalize_uuid_to_uuid(_TEST_UUID_STR)
        assert isinstance(result, uuid.UUID)
        assert str(result) == _TEST_UUID_STR

    def test_normalize_to_uuid_without_dashes(self):
        """Test converting UUID string without dashes to UUID object."""
        result = normalize_uuid_to_uuid(_TEST_UUID_HEX)
        assert isinstance(result, uuid.UUID)
        assert result.hex == _TEST_UUID_HEX

    def test_normalize_to_uuid_object(self):
        """Test that UUID object passes through unchanged."""
        result = normalize_uuid_to_uuid(_TEST_UUID)
        assert result == _TEST_UUID

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
        assert is_valid_uuid(_TEST_UUID_STR) is True

    def test_is_valid_uuid_without_dashes(self):
        """Test validation of UUID without dashes."""
        assert is_valid_uuid(_TEST_UUID_HEX) is True

    def test_is_valid_uuid_object(self):
        """Test validation of UUID object."""
        assert is_valid_uuid(_TEST_UUID) is True

    def test_is_valid_uuid_none_returns_false(self):
        """Test that None returns False."""
        assert is_valid_uuid(None) is False

    def test_is_valid_uuid_invalid_returns_false(self):
        """Test that invalid UUID returns False."""
        assert is_valid_uuid("not-a-uuid") is False

    def test_is_valid_uuid_wrong_length_returns_false(self):
        """Test that wrong-length string returns False."""
        assert is_valid_uuid(_PARTIAL_HEX) is False


class TestUuidFormatConsistency:
    """Test suite for UUID format consistency across operations."""

    def test_roundtrip_uuid_object_to_hex_and_back(self):
        """Test roundtrip conversion UUID object -> hex string -> UUID object."""
        hex_string = normalize_uuid(_TEST_UUID)
        result = normalize_uuid_to_uuid(hex_string)
        assert result == _TEST_UUID

    def test_normalized_format_is_32_chars(self):
        """Test that normalized format is always 32 characters."""
        test_cases = [
            _TEST_UUID_STR,
            _TEST_UUID_HEX,
            _TEST_UUID,
        ]

        for test_case in test_cases:
            result = normalize_uuid(test_case)
            assert result is not None
            assert len(result) == 32
            assert "-" not in result
