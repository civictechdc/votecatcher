import uuid

from sqlmodel import Session, select

from app.campaign.campaign_repository import CreateCampaign, ReadCampaign
from app.data.database.model.schema import Campaign, Region


class DemoCampaignRepository:
    def __init__(self, session: Session) -> None:
        self.db: Session = session

    async def save_campaign(self, new_campaign: CreateCampaign) -> uuid.UUID:
        region: Region = self.db.exec(
            select(Region).where(Region.region_key == new_campaign.region_key)
        ).one()

        model: Campaign = Campaign(
            unique_name=new_campaign.unique_name,
            title=new_campaign.title,
            year=new_campaign.year_active,
            description=new_campaign.description,
            region_id=region.id,
        )

        db_model: Campaign = Campaign.model_validate(model)
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return db_model.id

    async def fetch_campaign(self, unique_name: str) -> ReadCampaign:
        item: Campaign = self.db.exec(
            select(Campaign).where(Campaign.unique_name == unique_name)
        ).one()

        region: Region = self.db.exec(
            select(Region).where(Region.id == item.region_id)
        ).one()

        return ReadCampaign(
            id=str(item.id),
            created_at=item.created_at,
            updated_at=item.updated_at,
            unique_name=item.unique_name,
            title=item.title,
            description=item.description,
            year_active=item.year,
            region_id=str(item.region_id),
            region_key=region.region_key,
        )
