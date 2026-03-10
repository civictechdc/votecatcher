from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CampaignTable:
	campaign_id: str
	campaign_name_id: str
	region_id: str
	created_at: datetime = field(default_factory=datetime.now)
	updated_at: datetime | None = None
