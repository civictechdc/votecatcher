import re

from app.domain.field_spec import VoterRegField
from app.domain.voter import RegisteredVoter

_CATEGORY_TO_BLOB = {
    "name": "name_data",
    "address": "address_data",
    "registration": "other_field_data",
    "geography": "other_field_data",
}

_LEGACY_KEY_MAP: dict[str, str] = {
    "street_name": "street",
    "zip_code": "zip",
    "city_name": "city",
}

_STREET_NUMBER_RE = re.compile(r"^(\d+)\s*(.*)")


def _legacy_lookup(blob: dict[str, str], field_id: str) -> str | None:
    legacy_key = _LEGACY_KEY_MAP.get(field_id)
    if legacy_key and legacy_key in blob:
        value = blob[legacy_key]
        if field_id == "street_name" and "street_number" not in blob:
            m = _STREET_NUMBER_RE.match(value)
            if m:
                return m.group(2).strip() or value
        return value
    return None


def flatten_voter_data(
    voter: RegisteredVoter,
    voter_reg_fields: list[VoterRegField],
) -> dict[str, str]:
    flat: dict[str, str] = {}
    for field in voter_reg_fields:
        blob_name = _CATEGORY_TO_BLOB.get(field.category, "other_field_data")
        blob: dict[str, str] | None = getattr(voter, blob_name, None)
        blob = blob or {}
        value = blob.get(field.id, "")
        if not value:
            legacy = _legacy_lookup(blob, field.id)
            if legacy is not None:
                value = legacy
        flat[field.id] = value

    if "street_number" in flat and not flat["street_number"]:
        addr_blob: dict[str, str] | None = getattr(voter, "address_data", None)
        if addr_blob and "street" in addr_blob:
            m = _STREET_NUMBER_RE.match(addr_blob["street"])
            if m and m.group(1):
                flat["street_number"] = m.group(1)
                if "street_name" in flat and flat["street_name"] == addr_blob["street"]:
                    flat["street_name"] = m.group(2).strip()

    return flat
