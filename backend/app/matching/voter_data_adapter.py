from app.domain.field_spec import VoterRegField
from app.domain.voter import RegisteredVoter

_CATEGORY_TO_BLOB = {
    "name": "name_data",
    "address": "address_data",
    "registration": "other_field_data",
    "geography": "other_field_data",
}


def flatten_voter_data(
    voter: RegisteredVoter,
    voter_reg_fields: list[VoterRegField],
) -> dict[str, str]:
    flat: dict[str, str] = {}
    for field in voter_reg_fields:
        blob_name = _CATEGORY_TO_BLOB.get(field.category, "other_field_data")
        blob: dict[str, str] | None = getattr(voter, blob_name, None)
        flat[field.id] = (blob or {}).get(field.id, "")
    return flat
