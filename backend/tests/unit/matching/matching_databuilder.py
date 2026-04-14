"""Data builders and loaders for matching approval tests.

Provides pure-function reproduction of the OLD matching algorithm from
fuzzy_match_helper.py (commit 11b9617) and data loaders for test assets.
"""

import csv
import json
from pathlib import Path

from rapidfuzz import fuzz

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
        return json.load(f)


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
