"""Unit tests for MatchingService.

Tests follow BDD scenarios from SPEC.md §3.4:
- Name + address extraction from OCR results
- RapidFuzz fuzzy matching with weighted scoring
- Confidence level assignment
"""

from unittest.mock import MagicMock

from app.matching.matching_service import MatchingService


class TestMatchingServiceExtraction:
	"""Tests for extracting name and address from OCR results."""

	def test_extract_from_ocr_result_simple(self):
		"""Should extract name and address from simple OCR text."""
		service = MatchingService(session=MagicMock())
		ocr_text = {
			"name": "John Smith",
			"address": "123 Main St",
		}

		name, address = service.extract_name_and_address(ocr_text)

		assert name == "John Smith"
		assert address == "123 Main St"

	def test_extract_from_ocr_result_missing_fields(self):
		"""Should handle missing fields gracefully."""
		service = MatchingService(session=MagicMock())
		ocr_text = {"name": "John Smith"}

		name, address = service.extract_name_and_address(ocr_text)

		assert name == "John Smith"
		assert address == ""

	def test_extract_from_ocr_result_empty(self):
		"""Should handle empty OCR text."""
		service = MatchingService(session=MagicMock())
		ocr_text = {}

		name, address = service.extract_name_and_address(ocr_text)

		assert name == ""
		assert address == ""


class TestMatchingServiceSimilarity:
	"""Tests for fuzzy matching similarity calculation."""

	def test_calculate_similarity_exact_match(self):
		"""Should return high score for exact match."""
		service = MatchingService(session=MagicMock())
		score = service.calculate_similarity(
			ocr_name="John Smith",
			ocr_address="123 Main St",
			voter_name="John Smith",
			voter_address="123 Main St",
		)

		assert score >= 0.95

	def test_calculate_similarity_partial_match(self):
		"""Should return medium score for partial match."""
		service = MatchingService(session=MagicMock())
		score = service.calculate_similarity(
			ocr_name="John Smith",
			ocr_address="123 Main St",
			voter_name="John Smyth",
			voter_address="123 Main Street",
		)

		assert 0.60 <= score < 0.95

	def test_calculate_similarity_no_match(self):
		"""Should return low score for no match."""
		service = MatchingService(session=MagicMock())
		score = service.calculate_similarity(
			ocr_name="John Smith",
			ocr_address="123 Main St",
			voter_name="Jane Doe",
			voter_address="456 Oak Ave",
		)

		assert score < 0.60

	def test_calculate_similarity_empty_ocr(self):
		"""Should return 0 for empty OCR input."""
		service = MatchingService(session=MagicMock())
		score = service.calculate_similarity(
			ocr_name="",
			ocr_address="",
			voter_name="John Smith",
			voter_address="123 Main St",
		)

		assert score == 0.0


class TestMatchingServiceConfidence:
	"""Tests for confidence level assignment."""

	def test_assign_confidence_high(self):
		"""Should assign HIGH for score >= 0.85."""
		from app.data.database.model.match_result import ConfidenceLevel

		service = MatchingService(session=MagicMock())
		confidence = service.assign_confidence(0.90)

		assert confidence == ConfidenceLevel.HIGH

	def test_assign_confidence_medium(self):
		"""Should assign MEDIUM for 0.60 <= score < 0.85."""
		from app.data.database.model.match_result import ConfidenceLevel

		service = MatchingService(session=MagicMock())
		confidence = service.assign_confidence(0.70)

		assert confidence == ConfidenceLevel.MEDIUM

	def test_assign_confidence_low(self):
		"""Should assign LOW for score < 0.60."""
		from app.data.database.model.match_result import ConfidenceLevel

		service = MatchingService(session=MagicMock())
		confidence = service.assign_confidence(0.40)

		assert confidence == ConfidenceLevel.LOW

	def test_assign_confidence_boundary_high(self):
		"""Should assign HIGH at exact 0.85 threshold."""
		from app.data.database.model.match_result import ConfidenceLevel

		service = MatchingService(session=MagicMock())
		confidence = service.assign_confidence(0.85)

		assert confidence == ConfidenceLevel.HIGH

	def test_assign_confidence_boundary_medium(self):
		"""Should assign MEDIUM at exact 0.60 threshold."""
		from app.data.database.model.match_result import ConfidenceLevel

		service = MatchingService(session=MagicMock())
		confidence = service.assign_confidence(0.60)

		assert confidence == ConfidenceLevel.MEDIUM


class TestMatchingServiceInitialization:
	"""Tests for MatchingService initialization."""

	def test_matching_service_initializes_with_session(self):
		"""MatchingService should initialize with database session."""
		mock_session = MagicMock()
		service = MatchingService(session=mock_session)
		assert service.session == mock_session

	def test_matching_service_has_default_thresholds(self):
		"""MatchingService should have default confidence thresholds."""
		service = MatchingService(session=MagicMock())
		assert service.high_threshold == 0.85
		assert service.medium_threshold == 0.60

	def test_matching_service_allows_custom_thresholds(self):
		"""MatchingService should allow custom thresholds."""
		service = MatchingService(
			session=MagicMock(),
			high_threshold=0.90,
			medium_threshold=0.70,
		)
		assert service.high_threshold == 0.90
		assert service.medium_threshold == 0.70
