"""Repository implementations."""

from app.repositories.campaign_repo import CampaignRepository
from app.repositories.field_spec_repo import FieldSpecRepositoryImpl
from app.repositories.petition_repo import PetitionRepository
from app.repositories.voter_repo import VoterRepository

__all__ = [
    "CampaignRepository",
    "FieldSpecRepositoryImpl",
    "PetitionRepository",
    "VoterRepository",
]
