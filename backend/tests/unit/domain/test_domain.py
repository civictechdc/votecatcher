"""Tests for domain objects."""

from datetime import date, datetime
from uuid import UUID


class TestCampaign:
	"""Tests for Campaign domain object."""

	def test_create_campaign(self):
		"""Should create campaign with required fields."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test-campaign-2026",
			title="Test Campaign",
			year="2026",
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		assert campaign.unique_name == "test-campaign-2026"
		assert campaign.title == "Test Campaign"
		assert campaign.year == "2026"
		assert isinstance(campaign.id, UUID)

	def test_campaign_has_timestamps(self):
		"""Campaign should have created_at timestamp."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test",
			title="Test",
			year="2026",
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		assert campaign.created_at is not None
		assert isinstance(campaign.created_at, datetime)

	def test_campaign_description_optional(self):
		"""Campaign description should be optional."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test",
			title="Test",
			year="2026",
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		assert campaign.description is None

	def test_is_active_current_year(self):
		"""Campaign in current year should be active."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test",
			title="Test",
			year=str(date.today().year),
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		assert campaign.is_active() is True

	def test_is_active_past_year(self):
		"""Campaign in past year should not be active."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test",
			title="Test",
			year="2020",
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		assert campaign.is_active() is False

	def test_repr_masks_sensitive_fields(self):
		"""Campaign repr should be safe for logging."""
		from app.domain.campaign import Campaign

		campaign = Campaign(
			unique_name="test",
			title="Test",
			year="2026",
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
		)
		r = repr(campaign)
		assert "test" in r
		assert "Test" in r


class TestPetition:
	"""Tests for Petition domain object."""

	def test_create_petition(self):
		"""Should create petition with campaign reference."""
		from app.domain.petition import Petition

		petition = Petition(
			campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
			original_filename="petition.pdf",
			stored_path="/uploads/petition.pdf",
			file_hash="abc123",
		)
		assert petition.original_filename == "petition.pdf"
		assert petition.stored_path == "/uploads/petition.pdf"
		assert petition.file_hash == "abc123"

	def test_is_processed_false_when_no_page_count(self):
		"""Petition without page_count should not be processed."""
		from app.domain.petition import Petition

		petition = Petition(
			campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
			original_filename="test.pdf",
			stored_path="/test.pdf",
			file_hash="abc",
		)
		assert petition.is_processed() is False

	def test_is_processed_true_with_page_count(self):
		"""Petition with page_count should be processed."""
		from app.domain.petition import Petition

		petition = Petition(
			campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
			original_filename="test.pdf",
			stored_path="/test.pdf",
			file_hash="abc",
			page_count=5,
		)
		assert petition.is_processed() is True

	def test_repr_safe_for_logging(self):
		from app.domain.petition import Petition

		petition = Petition(
			campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
			original_filename="test.pdf",
			stored_path="/test.pdf",
			file_hash="abc",
		)
		r = repr(petition)
		assert "test.pdf" in r


class TestRegisteredVoter:
	"""Tests for RegisteredVoter domain object."""

	def test_create_voter_with_json_data(self):
		"""Should create voter with name and address data dicts."""
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"first_name": "John", "last_name": "Doe"},
			address_data={"city": "Washington", "state": "DC"},
		)
		assert voter.name_data["first_name"] == "John"
		assert voter.address_data["city"] == "Washington"

	def test_voter_full_name_property(self):
		"""Should compute full name from name_data."""
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"first_name": "John", "middle_name": "M", "last_name": "Doe"},
		)
		assert voter.full_name == "John M Doe"

	def test_voter_full_name_without_middle(self):
		"""Should handle missing middle name."""
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"first_name": "John", "last_name": "Doe"},
		)
		assert voter.full_name == "John Doe"

	def test_is_matchable_with_last_name(self):
		"""Voter with last_name should be matchable."""
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"last_name": "Doe"},
		)
		assert voter.is_matchable() is True

	def test_is_matchable_without_last_name(self):
		"""Voter without last_name should not be matchable."""
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"first_name": "John"},
		)
		assert voter.is_matchable() is False

	def test_repr_safe_for_logging(self):
		from app.domain.voter import RegisteredVoter

		voter = RegisteredVoter(
			region_id=UUID("00000000-0000-0000-0000-000000000001"),
			name_data={"first_name": "John", "last_name": "Doe"},
		)
		r = repr(voter)
		assert "John Doe" in r
