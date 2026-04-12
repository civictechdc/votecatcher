"""Unit tests for VoterListService."""

import hashlib

from app.services.voter_list_service import VoterListService


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
