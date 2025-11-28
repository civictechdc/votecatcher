from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class OCREntry(BaseModel):
    """Ballot signatory data"""

    Name: str = Field(description="Name of the petition signer")
    Address: str = Field(description="Address of the petition signatory")
    Date: str = Field(description="Date of the signed")
    Ward: int = Field(description="The area or 'Ward' that the signer belongs to")


class OCRData(BaseModel):
    data: list[OCREntry] = Field(description="List of OCR Entries")


@dataclass
class EncodedPetitionPage:
    petition_file_name: str
    page_num: int
    encoded_page: str
    # For tracking
    petition_file_page_total: int


@dataclass
class EncodedPetitionDocuments:
    # TODO x of y scans?
    campaign_id: str
    encoded_pages: list[EncodedPetitionPage]

    def __post_init__(self) -> None:
        # Arrange the pages in file name and then file page order
        self.encoded_pages.sort(
            key=lambda page: (page.petition_file_name, page.page_num)
        )

    @property
    def total_pages(self) -> int:
        return len(self.encoded_pages)
