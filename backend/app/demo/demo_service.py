"""Service for loading and resetting demo data."""

import structlog
from sqlmodel import Session, delete

from app.data.database.model.jobs import JobStatus, MatcherJob, OcrJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Campaign, Region

logger = structlog.get_logger(__name__)

# Minimal synthetic voters for demo
DEMO_VOTERS = [
	{
		"first_name": "John",
		"last_name": "Smith",
		"zip": "20001",
		"street": "123 Main St NW",
	},
	{
		"first_name": "Maria",
		"last_name": "Garcia",
		"zip": "20002",
		"street": "456 Oak Ave NE",
	},
	{
		"first_name": "Robert",
		"last_name": "Johnson",
		"zip": "20003",
		"street": "789 Pine St SW",
	},
	{
		"first_name": "Sarah",
		"last_name": "Williams",
		"zip": "20004",
		"street": "321 Elm Blvd SE",
	},
	{
		"first_name": "David",
		"last_name": "Brown",
		"zip": "20005",
		"street": "654 Cedar Ln NW",
	},
	{
		"first_name": "Jennifer",
		"last_name": "Davis",
		"zip": "20006",
		"street": "987 Maple Dr NE",
	},
	{
		"first_name": "Michael",
		"last_name": "Miller",
		"zip": "20007",
		"street": "147 Birch Ave NW",
	},
	{
		"first_name": "Lisa",
		"last_name": "Wilson",
		"zip": "20008",
		"street": "258 Walnut Way SE",
	},
	{
		"first_name": "James",
		"last_name": "Taylor",
		"zip": "20009",
		"street": "369 Cherry Ct NW",
	},
	{
		"first_name": "Emily",
		"last_name": "Anderson",
		"zip": "20010",
		"street": "741 Spruce Pl NE",
	},
]

# Simulated OCR results (matching voter names with slight variations)
DEMO_OCR_RESULTS = [
	{"extracted_name": "Jon Smith", "extracted_address": "123 Main St"},
	{"extracted_name": "Maria Garca", "extracted_address": "456 Oak Ave"},
	{"extracted_name": "Rob Johnson", "extracted_address": "789 Pine St"},
	{"extracted_name": "S. Williams", "extracted_address": "321 Elm Blvd"},
	{"extracted_name": "Dave Brown", "extracted_address": "654 Cedar Ln"},
	{"extracted_name": "J. Davis", "extracted_address": "987 Maple Dr"},
	{"extracted_name": "Mike Miller", "extracted_address": "147 Birch Ave"},
	{"extracted_name": "L Wilson", "extracted_address": "258 Walnut Way"},
	{"extracted_name": "Jms Taylor", "extracted_address": "369 Cherry Ct"},
	{"extracted_name": "E Anderson", "extracted_address": "741 Spruce Pl"},
]


class DemoDataService:
	"""Service for loading and resetting demo data."""

	def __init__(self, session: Session):
		self.session = session

	def load_minimal_session(self) -> dict:
		"""Load minimal demo session with 10 entries."""
		logger.info("Loading minimal demo session")

		# 1. Create Region
		region = Region(
			region_key="dc",
			region_name="Washington, DC",
			country_code="US",
		)
		self.session.add(region)
		self.session.flush()

		# 2. Create Campaign
		campaign = Campaign(
			unique_name="dc-demo-2024",
			title="DC Demo 2024",
			description="Minimal demo session with 10 entries",
			year="2024",
			region_id=region.id,
		)
		self.session.add(campaign)
		self.session.flush()

		# 3. Create Voters
		voters = []
		for voter_data in DEMO_VOTERS:
			voter = RegisteredVoter(
				region_id=region.id,
				name_data={
					"first_name": voter_data["first_name"],
					"last_name": voter_data["last_name"],
				},
				address_data={
					"street": voter_data["street"],
					"zip": voter_data["zip"],
					"city": "Washington",
					"state": "DC",
				},
			)
			self.session.add(voter)
			voters.append(voter)
		self.session.flush()

		# 4. Create PetitionScan
		scan = PetitionScan(
			campaign_id=campaign.id,
			original_filename="demo_petition.pdf",
			stored_path=f"/data/campaigns/{campaign.id}/petitions/demo_petition.pdf",
			file_hash="demo_hash_" + str(campaign.id),
			page_count=1,
		)
		self.session.add(scan)
		self.session.flush()

		# 5. Create PetitionCrops
		crops = []
		for i in range(10):
			crop = PetitionCrop(
				scan_id=scan.id,
				crop_index=i,
				stored_path=f"/data/campaigns/{campaign.id}/crops/crop_{i}.png",
				crop_coordinates={"top": i * 0.1, "bottom": (i + 1) * 0.1},
				page_number=1,
			)
			self.session.add(crop)
			crops.append(crop)
		self.session.flush()

		# 6. Create MatcherJob
		matcher_job = MatcherJob(
			campaign_id=campaign.id,
			current_status=JobStatus.MATCHING_COMPLETED,
		)
		self.session.add(matcher_job)
		self.session.flush()

		# 7. Create OcrJob
		ocr_job = OcrJob(
			matcher_job_id=matcher_job.id,
			status=JobStatus.OCR_COMPLETED,
		)
		self.session.add(ocr_job)
		self.session.flush()

		# 8. Create OcrResults and MatchResults
		for crop, ocr_data in zip(crops, DEMO_OCR_RESULTS, strict=False):
			ocr_result = OcrResult(
				crop_id=crop.id,
				ocr_job_id=ocr_job.id,
				extracted_text={
					"name": ocr_data["extracted_name"],
					"address": ocr_data["extracted_address"],
				},
				confidence_score=0.85,
			)
			self.session.add(ocr_result)
			self.session.flush()

			# Create top 5 match results per OCR result
			for rank, voter in enumerate(voters[:5], start=1):
				# First match is the correct one (high confidence)
				if rank == 1:
					confidence = ConfidenceLevel.HIGH
					score = 0.92
				elif rank == 2:
					confidence = ConfidenceLevel.MEDIUM
					score = 0.75
				else:
					confidence = ConfidenceLevel.LOW
					score = 0.50 - (rank * 0.05)

				match_result = MatchResult(
					ocr_result_id=ocr_result.id,
					matcher_job_id=matcher_job.id,
					rank=rank,
					voter_id=voter.id if rank <= len(voters) else None,
					similarity_score=score,
					confidence_level=confidence,
					field_scores={"name": score, "address": score - 0.1},
				)
				self.session.add(match_result)

		self.session.commit()
		logger.info("Demo session loaded successfully")

		return {
			"success": True,
			"campaign_id": str(campaign.id),
			"voters_count": 10,
			"crops_count": 10,
			"match_results_count": 50,
		}

	def reset(self) -> None:
		"""Reset all demo data."""
		logger.info("Resetting demo data")

		# Delete in reverse dependency order
		self.session.exec(delete(MatchResult))
		self.session.exec(delete(OcrResult))
		self.session.exec(delete(OcrJob))
		self.session.exec(delete(MatcherJob))
		self.session.exec(delete(PetitionCrop))
		self.session.exec(delete(PetitionScan))
		self.session.exec(delete(RegisteredVoter))
		self.session.exec(delete(Campaign))
		self.session.exec(delete(Region))

		self.session.commit()
		logger.info("Demo data reset complete")
