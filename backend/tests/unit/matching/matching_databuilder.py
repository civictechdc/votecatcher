"""Data builders and loaders for matching approval tests.

Provides pure-function reproduction of the OLD matching algorithm from
fuzzy_match_helper.py (commit 11b9617), spec-driven test object builders,
and data loaders for test assets.
"""

import csv
import json
from pathlib import Path
from uuid import uuid4

from rapidfuzz import fuzz

from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)
from app.domain.voter import RegisteredVoter

ASSETS_DIR = Path(__file__).parent / "assets"
CSV_PATH = (
    Path(__file__).resolve().parents[3]
    / "uploads"
    / "voter-lists"
    / "fake_voter_records.csv"
)

HAS_VOTER_CSV = CSV_PATH.exists()

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60


def load_ocr_results() -> list[dict]:
    with open(ASSETS_DIR / "live_ocr_results.json") as f:
        data = json.load(f)
    return [{k: v for k, v in r.items() if k != "id"} for r in data["ocr_results"]]


def load_matched_voters() -> list[dict]:
    with open(ASSETS_DIR / "live_matched_voters.json") as f:
        data = json.load(f)
    return data["voters"]


def load_voters_from_csv() -> list[dict]:
    voters = []
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            name = f"{row['First_Name']} {row['Last_Name']}"
            address = " ".join(
                p
                for p in [
                    row.get("Street_Number", ""),
                    row.get("Street_Name", ""),
                    row.get("Street_Type", ""),
                    row.get("Street_Dir_Suffix", ""),
                ]
                if p.strip()
            )
            voters.append(
                {
                    "id": i,
                    "first_name": row["First_Name"],
                    "last_name": row["Last_Name"],
                    "full_name": name,
                    "full_address": address,
                }
            )
    return voters


def old_algorithm_score(
    ocr_name: str, ocr_address: str, voters: list[dict]
) -> list[dict]:
    results = []
    for voter in voters:
        name_score = fuzz.ratio(ocr_name, voter["full_name"]) / 100.0
        address_score = fuzz.ratio(ocr_address, voter["full_address"]) / 100.0

        if name_score + address_score == 0:
            harmonic = 0.0
        else:
            harmonic = (2 * name_score * address_score) / (name_score + address_score)

        results.append(
            {
                "voter_id": voter["id"],
                "voter_name": voter["full_name"],
                "voter_address": voter["full_address"],
                "name_score": round(name_score, 6),
                "address_score": round(address_score, 6),
                "combined_score": round(harmonic, 6),
            }
        )

    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results


def assign_confidence(score: float) -> str:
    if score >= CONFIDENCE_HIGH:
        return "HIGH"
    elif score >= CONFIDENCE_MEDIUM:
        return "MEDIUM"
    return "LOW"


def run_old_algorithm_batch(ocr_results: list[dict], voters: list[dict]) -> list[dict]:
    all_results = []
    for ocr in ocr_results:
        matches = old_algorithm_score(ocr["name"], ocr["address"], voters)
        top = matches[0]
        all_results.append(
            {
                "ocr_id": ocr["id"],
                "ocr_name": ocr["name"],
                "ocr_address": ocr["address"],
                "top_match": {
                    "voter_id": top["voter_id"],
                    "voter_name": top["voter_name"],
                    "voter_address": top["voter_address"],
                    "name_score": top["name_score"],
                    "address_score": top["address_score"],
                    "combined_score": top["combined_score"],
                    "confidence": assign_confidence(top["combined_score"]),
                },
            }
        )
    return all_results


def dc_production_spec() -> RegionFieldSpecConfig:
    """Exact production spec from dc.json5 — same fields, weights, templates, thresholds."""
    return RegionFieldSpecConfig(
        region_name="District of Columbia",
        country_code="US",
        ballot_fields=[
            BallotField(
                id="name",
                label="Full Name",
                field_type="text",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="address",
                label="Address",
                field_type="address",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="ward",
                label="Ward",
                field_type="integer",
                required_for_matching=False,
                match_weight=0.3,
            ),
            BallotField(
                id="date_signed",
                label="Date Signed",
                field_type="date",
                required_for_matching=False,
                match_weight=0.0,
            ),
        ],
        voter_reg_fields=[
            VoterRegField(
                id="last_name",
                csv_column_name="Last_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="first_name",
                csv_column_name="First_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="middle_name",
                csv_column_name="Middle_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="name_style",
                csv_column_name="Name_Style",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="street_number",
                csv_column_name="Street_Number",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_number_suffix",
                csv_column_name="Street_Number_Suffix",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_name",
                csv_column_name="Street_Name",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_type",
                csv_column_name="Street_Type",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="street_dir_suffix",
                csv_column_name="Street_Dir_Suffix",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="unit_type",
                csv_column_name="Unit_Type",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="apartment_number",
                csv_column_name="Apartment_Number",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="zip_code",
                csv_column_name="Zip_Code",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="city_name",
                csv_column_name="City_Name",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="registration_date",
                csv_column_name="Registration_Date",
                data_type="date",
                category="registration",
            ),
            VoterRegField(
                id="party",
                csv_column_name="Party",
                data_type="text",
                category="registration",
            ),
            VoterRegField(
                id="voter_status",
                csv_column_name="Voter Status",
                data_type="text",
                category="registration",
            ),
            VoterRegField(
                id="is_us_citizen",
                csv_column_name="IsUSCitizen",
                data_type="text",
                category="registration",
            ),
            VoterRegField(
                id="precinct",
                csv_column_name="Precinct",
                data_type="text",
                category="geography",
            ),
            VoterRegField(
                id="smd", csv_column_name="SMD", data_type="text", category="geography"
            ),
            VoterRegField(
                id="anc", csv_column_name="ANC", data_type="text", category="geography"
            ),
            VoterRegField(
                id="ward",
                csv_column_name="WARD",
                data_type="integer",
                category="geography",
            ),
        ],
        field_mappings=[
            FieldMapping(
                ballot_field_id="name",
                template="{first_name} {middle_name} {last_name}",
            ),
            FieldMapping(
                ballot_field_id="address",
                template="{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}",
            ),
            FieldMapping(ballot_field_id="ward", template="{ward}"),
            FieldMapping(ballot_field_id="date_signed", template=""),
        ],
        hash_fields=[
            "last_name",
            "first_name",
            "street_number",
            "street_name",
            "zip_code",
        ],
        crop_config=CropConfig(top_crop=0.385, bottom_crop=0.725, base_threshold=85),
        pre_filter_field_id="zip_code",
    )


def build_spec_voter(
    vid: int,
    first_name: str,
    last_name: str,
    street_number: str = "",
    street_name: str = "",
    street_type: str = "",
    street_dir_suffix: str = "",
    apartment_number: str = "",
    zip_code: str = "",
    middle_name: str = "",
    ward: str = "",
) -> RegisteredVoter:
    """Build a voter with spec-format (structured) address_data."""
    return RegisteredVoter(
        id=vid,
        region_id=uuid4(),
        name_data={
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
        },
        address_data={
            "street_number": street_number,
            "street_number_suffix": "",
            "street_name": street_name,
            "street_type": street_type,
            "street_dir_suffix": street_dir_suffix,
            "unit_type": "",
            "apartment_number": apartment_number,
            "zip_code": zip_code,
            "city_name": "",
        },
        other_field_data={"ward": ward},
    )


def build_legacy_voter(
    vid: int,
    first_name: str,
    last_name: str,
    street: str,
    middle_name: str = "",
) -> RegisteredVoter:
    """Build a voter with legacy-format address_data (pre-G10 import)."""
    return RegisteredVoter(
        id=vid,
        region_id=uuid4(),
        name_data={
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
        },
        address_data={"street": street, "city": "", "state": "", "zip": ""},
        other_field_data={},
    )
