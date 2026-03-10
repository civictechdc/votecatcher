from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.ocr.data.data_models import EncodedPetitionDocuments


class BatchEncodedImage(BaseModel):
	image: str
	row: int
	page: int
	file_name: str


class BatchOcrRequestInput(BaseModel):
	campaign_id: str = Field(
		description="The id of the campaign associated with the documents."
	)
	encoded_petition_pages: EncodedPetitionDocuments = Field(
		description="The list of encoded petition pages that can span multiple files"
	)


class Payload(BaseModel):
	role: str
	messages: list[dict[str, Any]]
	page: int
	file_name: str


@dataclass
class BatchRequestPayload:
	campaign_id: str
	batch_payloads: list[Payload]

	@property
	def total_payload_size(self) -> int:
		return len(self.batch_payloads)
