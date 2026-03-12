"""UUID normalization utilities for consistent storage format.

All UUID fields must be stored as 32-character hex strings without dashes.
This module provides utilities to ensure consistent UUID formatting across the codebase.

Example:
    '25ea5e1c-2fd8-49e8-8062-c15e8b04492c' -> '25ea5e1c2fd849e88062c15e8b04492c'
"""

import uuid


def normalize_uuid(uuid_value: str | uuid.UUID | None) -> str | None:
	"""Normalize a UUID to 32-character hex format without dashes.

	Args:
		uuid_value: UUID as string (with or without dashes) or UUID object

	Returns:
		32-character hex string, or None if input is None

	Raises:
		ValueError: If the input is not a valid UUID

	Examples:
		>>> normalize_uuid("25ea5e1c-2fd8-49e8-8062-c15e8b04492c")
		'25ea5e1c2fd849e88062c15e8b04492c'
		>>> normalize_uuid("25ea5e1c2fd849e88062c15e8b04492c")
		'25ea5e1c2fd849e88062c15e8b04492c'
		>>> normalize_uuid(uuid.UUID("25ea5e1c-2fd8-49e8-8062-c15e8b04492c"))
		'25ea5e1c2fd849e88062c15e8b04492c'
	"""
	if uuid_value is None:
		return None

	if isinstance(uuid_value, uuid.UUID):
		return uuid_value.hex

	normalized = str(uuid_value).replace("-", "")

	if len(normalized) == 32:
		try:
			uuid.UUID(hex=normalized)
			return normalized
		except ValueError as e:
			raise ValueError(f"Invalid UUID hex string: {uuid_value}") from e

	if len(normalized) in (32, 36):
		try:
			parsed = uuid.UUID(str(uuid_value))
			return parsed.hex
		except ValueError as e:
			raise ValueError(f"Invalid UUID: {uuid_value}") from e

	raise ValueError(f"Invalid UUID format: {uuid_value}")


def normalize_uuid_to_uuid(uuid_value: str | uuid.UUID | None) -> uuid.UUID | None:
	"""Normalize a UUID input to a uuid.UUID object.

	Args:
		uuid_value: UUID as string (with or without dashes) or UUID object

	Returns:
		uuid.UUID object, or None if input is None

	Raises:
		ValueError: If the input is not a valid UUID
	"""
	if uuid_value is None:
		return None

	if isinstance(uuid_value, uuid.UUID):
		return uuid_value

	try:
		if len(str(uuid_value).replace("-", "")) == 32:
			return uuid.UUID(hex=str(uuid_value).replace("-", ""))
		return uuid.UUID(str(uuid_value))
	except ValueError as e:
		raise ValueError(f"Invalid UUID: {uuid_value}") from e


def is_valid_uuid(uuid_value: str | uuid.UUID | None) -> bool:
	"""Check if a value is a valid UUID.

	Args:
		uuid_value: Value to check

	Returns:
		True if valid UUID, False otherwise
	"""
	if uuid_value is None:
		return False

	try:
		normalize_uuid(uuid_value)
		return True
	except ValueError:
		return False
