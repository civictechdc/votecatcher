from dataclasses import dataclass


@dataclass
class MatchInfo:
    campaign_id: str
    ocr_name: str
    ocr_address: str
    match_score: float
    row_number: int
    page_number: int


@dataclass
class MatchEntry:
    id: str
    campaign_id: str
    file_id: str
    date: str
