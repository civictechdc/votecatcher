"""Matching service for fuzzy matching OCR results against voter registration lists.

Implements the matching pipeline from SPEC.md §3.4:
1. Load Voter List → Load OCR Results
2. For each OCR result:
   - DB pre-filter (region, zipcode)
   - Extract name + address components
   - RapidFuzz fuzzy match
   - Calculate weighted similarity score
   - Rank top 5 predictions
   - Store match results with confidence levels
"""

from typing import Any

import structlog
from rapidfuzz import fuzz
from sqlmodel import Session, col, select

from app.data.database.model.jobs import MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.registered_voter import RegisteredVoter

logger = structlog.get_logger(__name__)


class MatchingService:
	"""Service for fuzzy matching OCR results against registered voters.

	Confidence Thresholds (defaults, can be calibrated):
	    - HIGH: >= 0.85
	    - MEDIUM: 0.60 - 0.84
	    - LOW: < 0.60

	Attributes:
	    session: Database session for queries and persistence
	    high_threshold: Minimum score for HIGH confidence (default 0.85)
	    medium_threshold: Minimum score for MEDIUM confidence (default 0.60)
	"""

	def __init__(
		self,
		session: Session,
		high_threshold: float = 0.85,
		medium_threshold: float = 0.60,
	) -> None:
		"""Initialize matching service.

		Args:
		    session: Database session
		    high_threshold: Minimum score for HIGH confidence (default 0.85)
		    medium_threshold: Minimum score for MEDIUM confidence (default 0.60)
		"""
		self.session = session
		self.high_threshold = high_threshold
		self.medium_threshold = medium_threshold

	def pre_filter_voters(
		self,
		region_id: Any,
		zipcode: str | None = None,
	) -> list[RegisteredVoter]:
		"""Pre-filter voters by region and optional zipcode.

		Implements DB pre-filtering from SPEC.md §3.4 to reduce the
		search space before fuzzy matching.

		Args:
		    region_id: Region UUID to filter by
		    zipcode: Optional zipcode to further narrow results

		Returns:
		    List of RegisteredVoter instances matching filters
		"""
		statement = select(RegisteredVoter).where(
			RegisteredVoter.region_id == region_id
		)

		if zipcode:
			statement = statement.where(
				col(RegisteredVoter.address_data)["zip"].as_string() == zipcode
			)

		voters = self.session.exec(statement).all()

		logger.debug(
			"Pre-filtered voters",
			region_id=str(region_id),
			zipcode=zipcode,
			count=len(voters),
		)

		return list(voters)

	def extract_name_and_address(self, ocr_text: dict[str, Any]) -> tuple[str, str]:
		"""Extract name and address from OCR result text.

		Handles various OCR output formats gracefully.

		Args:
		    ocr_text: Dictionary with extracted OCR text

		Returns:
		    Tuple of (name, address) strings
		"""
		name = ocr_text.get("name", "")
		if not name:
			name = ocr_text.get("Name", "")

		address = ocr_text.get("address", "")
		if not address:
			address = ocr_text.get("Address", "")

		return str(name), str(address)

	def calculate_similarity(
		self,
		ocr_name: str,
		ocr_address: str,
		voter_name: str,
		voter_address: str,
	) -> float:
		"""Calculate weighted similarity score between OCR and voter data.

		Uses harmonic mean of name and address similarity scores to balance
		the contribution of each field.

		Args:
		    ocr_name: OCR-extracted name
		    ocr_address: OCR-extracted address
		    voter_name: Voter registration name
		    voter_address: Voter registration address

		Returns:
		    Similarity score between 0.0 and 1.0
		"""
		if not ocr_name and not ocr_address:
			return 0.0

		name_score = fuzz.ratio(ocr_name, voter_name) / 100.0
		address_score = fuzz.ratio(ocr_address, voter_address) / 100.0

		if name_score + address_score == 0:
			return 0.0

		harmonic_mean = (2 * name_score * address_score) / (name_score + address_score)

		return harmonic_mean

	def assign_confidence(self, similarity_score: float) -> ConfidenceLevel:
		"""Assign confidence level based on similarity score.

		Uses thresholds defined in SPEC.md §3.4:
		    - HIGH: >= 0.85
		    - MEDIUM: 0.60 - 0.84
		    - LOW: < 0.60

		Args:
		    similarity_score: Similarity score between 0.0 and 1.0

		Returns:
		    ConfidenceLevel enum value
		"""
		if similarity_score >= self.high_threshold:
			return ConfidenceLevel.HIGH
		elif similarity_score >= self.medium_threshold:
			return ConfidenceLevel.MEDIUM
		else:
			return ConfidenceLevel.LOW

	def match_ocr_result(
		self,
		ocr_text: dict[str, Any],
		region_id: Any,
		top_n: int = 5,
	) -> list[dict[str, Any]]:
		"""Match single OCR result against registered voters.

		Implements the matching algorithm:
		1. Pre-filter voters by region
		2. Extract name and address from OCR
		3. Calculate similarity for each voter
		4. Rank by score and return top N

		Args:
		    ocr_text: OCR extracted text dictionary
		    region_id: Region UUID for pre-filtering
		    top_n: Number of top predictions to return (default 5)

		Returns:
		    List of match dictionaries with voter_id, similarity_score,
		    confidence_level, and field_scores
		"""
		voters = self.pre_filter_voters(region_id=region_id)

		if not voters:
			logger.warning(
				"No voters found for region",
				region_id=str(region_id),
			)
			return []

		ocr_name, ocr_address = self.extract_name_and_address(ocr_text)

		matches: list[dict[str, Any]] = []

		for voter in voters:
			voter_name = self._build_voter_name(voter)
			voter_address = self._build_voter_address(voter)

			similarity = self.calculate_similarity(
				ocr_name=ocr_name,
				ocr_address=ocr_address,
				voter_name=voter_name,
				voter_address=voter_address,
			)

			name_score = fuzz.ratio(ocr_name, voter_name) / 100.0
			address_score = fuzz.ratio(ocr_address, voter_address) / 100.0

			matches.append(
				{
					"voter_id": voter.id,
					"similarity_score": similarity,
					"confidence_level": self.assign_confidence(similarity),
					"field_scores": {
						"name": name_score,
						"address": address_score,
					},
				}
			)

		matches.sort(key=lambda x: x["similarity_score"], reverse=True)

		top_matches = matches[:top_n]

		logger.debug(
			"Matched OCR result",
			ocr_name=ocr_name[:30],
			top_score=top_matches[0]["similarity_score"] if top_matches else 0,
			matches_returned=len(top_matches),
		)

		return top_matches

	def _build_voter_name(self, voter: RegisteredVoter) -> str:
		"""Build full name string from voter name_data.

		Args:
		    voter: RegisteredVoter instance

		Returns:
		    Full name string
		"""
		name_data = voter.name_data or {}
		parts = [
			name_data.get("first_name", ""),
			name_data.get("middle_name", ""),
			name_data.get("last_name", ""),
		]
		return " ".join(part for part in parts if part)

	def _build_voter_address(self, voter: RegisteredVoter) -> str:
		"""Build full address string from voter address_data.

		Args:
		    voter: RegisteredVoter instance

		Returns:
		    Full address string
		"""
		address_data = voter.address_data or {}
		parts = [
			address_data.get("street_number", ""),
			address_data.get("street_name", ""),
			address_data.get("street_type", ""),
			address_data.get("street_dir_suffix", ""),
		]
		return " ".join(part for part in parts if part)

	async def run_matching(self, job_id: int) -> dict[str, Any]:
		"""Run complete matching pipeline for a matcher job.

		Processes all OCR results associated with the job's campaign
		and creates MatchResult records for top predictions.

		Args:
		    job_id: MatcherJob database ID

		Returns:
		    Summary dictionary with:
		        - total_ocr_results: Number of OCR results processed
		        - total_matches_created: Total match results created
		        - high_confidence_count: Matches with HIGH confidence
		        - medium_confidence_count: Matches with MEDIUM confidence
		        - low_confidence_count: Matches with LOW confidence

		Raises:
		    ValueError: If job not found
		"""
		job = self.session.get(MatcherJob, job_id)

		if not job:
			raise ValueError(f"Job not found: {job_id}")

		logger.info(
			"Starting matching pipeline",
			job_id=job_id,
			campaign_id=str(job.campaign_id),
		)

		ocr_results = self.session.exec(
			select(OcrResult)
			.join(MatcherJob, OcrResult.ocr_job_id == MatcherJob.id)
			.where(MatcherJob.campaign_id == job.campaign_id)
		).all()

		logger.info(
			"Found OCR results to process",
			job_id=job_id,
			ocr_result_count=len(ocr_results),
		)

		total_matches = 0
		high_count = 0
		medium_count = 0
		low_count = 0

		for ocr_result in ocr_results:
			matches = self.match_ocr_result(
				ocr_text=ocr_result.extracted_text,
				region_id=job.campaign.region_id,
				top_n=5,
			)

			self.store_match_results(
				ocr_result_id=ocr_result.id,
				matcher_job_id=job_id,
				matches=matches,
			)

			total_matches += len(matches)

			for match in matches:
				if match["confidence_level"] == ConfidenceLevel.HIGH:
					high_count += 1
				elif match["confidence_level"] == ConfidenceLevel.MEDIUM:
					medium_count += 1
				else:
					low_count += 1

		logger.info(
			"Matching pipeline complete",
			job_id=job_id,
			total_matches=total_matches,
			high=high_count,
			medium=medium_count,
			low=low_count,
		)

		return {
			"total_ocr_results": len(ocr_results),
			"total_matches_created": total_matches,
			"high_confidence_count": high_count,
			"medium_confidence_count": medium_count,
			"low_confidence_count": low_count,
		}

	def store_match_results(
		self,
		ocr_result_id: int,
		matcher_job_id: int,
		matches: list[dict[str, Any]],
	) -> None:
		"""Store match results in database.

		Clears any existing match results for the OCR result before
		creating new records.

		Args:
		    ocr_result_id: OCR result database ID
		    matcher_job_id: Matcher job database ID
		    matches: List of match dictionaries from match_ocr_result
		"""
		existing = self.session.exec(
			select(MatchResult).where(MatchResult.ocr_result_id == ocr_result_id)
		).all()

		for match in existing:
			self.session.delete(match)

		self.session.commit()

		for rank, match in enumerate(matches, start=1):
			match_result = MatchResult(
				ocr_result_id=ocr_result_id,
				matcher_job_id=matcher_job_id,
				rank=rank,
				voter_id=match["voter_id"],
				similarity_score=match["similarity_score"],
				confidence_level=match["confidence_level"],
				field_scores=match["field_scores"],
			)
			self.session.add(match_result)

		self.session.commit()

		logger.debug(
			"Stored match results",
			ocr_result_id=ocr_result_id,
			match_count=len(matches),
		)
