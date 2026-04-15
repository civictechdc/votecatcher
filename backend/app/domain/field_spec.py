import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BallotField(BaseModel, frozen=True):
    id: str
    label: str
    field_type: Literal["text", "address", "integer", "date"]
    required_for_matching: bool
    match_weight: float = Field(default=1.0, ge=0.0)


class VoterRegField(BaseModel, frozen=True):
    id: str
    csv_column_name: str
    data_type: Literal["text", "integer", "date"]
    category: Literal["name", "address", "registration", "geography"]


class FieldMapping(BaseModel, frozen=True):
    ballot_field_id: str
    template: str


class CropConfig(BaseModel, frozen=True):
    top_crop: float = Field(ge=0.0, le=1.0)
    bottom_crop: float = Field(ge=0.0, le=1.0)
    base_threshold: int = Field(ge=0, le=255)


class RegionFieldSpecConfig(BaseModel, frozen=True):
    region_name: str
    country_code: str = "US"
    ballot_fields: list[BallotField]
    voter_reg_fields: list[VoterRegField]
    field_mappings: list[FieldMapping]
    hash_fields: list[str]
    crop_config: CropConfig
    pre_filter_field_id: str | None = None

    def get_mapping_for(self, ballot_field_id: str) -> FieldMapping | None:
        for m in self.field_mappings:
            if m.ballot_field_id == ballot_field_id:
                return m
        return None

    def matchable_fields(self) -> list[BallotField]:
        return [
            f
            for f in self.ballot_fields
            if f.required_for_matching and f.match_weight > 0
        ]

    def total_match_weight(self) -> float:
        return sum(f.match_weight for f in self.matchable_fields())

    def pre_filter_field(self) -> VoterRegField | None:
        if not self.pre_filter_field_id:
            return None
        for f in self.voter_reg_fields:
            if f.id == self.pre_filter_field_id:
                return f
        return None

    def validate_integrity(self) -> list[str]:
        errors: list[str] = []
        ballot_ids = [f.id for f in self.ballot_fields]
        voter_ids = {f.id for f in self.voter_reg_fields}
        csv_names = [f.csv_column_name for f in self.voter_reg_fields]

        seen_ballot: set[str] = set()
        for fid in ballot_ids:
            if fid in seen_ballot:
                errors.append(f"Duplicate ballot field ID: {fid}")
            seen_ballot.add(fid)

        seen_voter: set[str] = set()
        for f in self.voter_reg_fields:
            if f.id in seen_voter:
                errors.append(f"Duplicate voter reg field ID: {f.id}")
            seen_voter.add(f.id)

        seen_csv: set[str] = set()
        for name in csv_names:
            if name in seen_csv:
                errors.append(f"Duplicate CSV column name: {name}")
            seen_csv.add(name)

        for m in self.field_mappings:
            if m.ballot_field_id not in seen_ballot:
                errors.append(
                    f"Field mapping references unknown ballot field: {m.ballot_field_id}"
                )
            placeholders: list[str] = re.findall(r"\{(\w+)\}", m.template)
            for placeholder in placeholders:
                if placeholder not in voter_ids:
                    errors.append(
                        f"Template references unknown voter field: {placeholder}"
                    )

        for bf in self.matchable_fields():
            if not any(m.ballot_field_id == bf.id for m in self.field_mappings):
                errors.append(f"Matchable field '{bf.id}' has no field mapping")

        for hf in self.hash_fields:
            if hf not in voter_ids:
                errors.append(f"Hash field references unknown voter reg field: {hf}")

        if not self.matchable_fields():
            errors.append("Spec must have at least one matchable field")

        if self.crop_config.top_crop >= self.crop_config.bottom_crop:
            errors.append("top_crop must be less than bottom_crop")

        return errors


class FieldSpecNotFoundError(Exception):
    def __init__(self, region_id: UUID):
        self.region_id: UUID = region_id
        super().__init__(f"Field spec not found for region: {region_id}")


NA_SENTINELS = {"N/A", "NA"}


def _extract_placeholders(template: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", template)


def render_template(template: str, voter_row: dict[str, str]) -> str:
    if not template:
        return ""

    placeholders = _extract_placeholders(template)
    result = template
    for field in placeholders:
        value = (voter_row.get(field) or "").strip()
        if value.upper() in NA_SENTINELS:
            value = ""
        result = result.replace(f"{{{field}}}", value)

    result = re.sub(r"\s+", " ", result).strip()
    result = re.sub(r"\bApt\s*$", "", result).strip()
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r",\s*$", "", result)
    result = re.sub(r"^\s*,\s*", "", result)
    return result.strip()
