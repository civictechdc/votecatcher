from dataclasses import dataclass
from io import BytesIO

import pandas as pd
from fastapi import UploadFile
from pandas import DataFrame

from app.voter.voter_schema import VoterRegistrationSchema, get_demo_voter_schema


@dataclass
class RegisteredVotersData:
    voters_df: DataFrame
    voter_schema: VoterRegistrationSchema


DEMO_VOTER_RECORD_STATE: RegisteredVotersData | None = None


async def process_voter_data(voter_records_file: UploadFile) -> RegisteredVotersData:
    content_bytes: bytes = await voter_records_file.read()
    buffer: BytesIO = BytesIO(initial_bytes=content_bytes)
    df: DataFrame = pd.read_csv(buffer, dtype=pd.StringDtype())
    schema: VoterRegistrationSchema = get_demo_voter_schema()

    df["Full Name"] = df[schema.name_fields].agg(" ".join, axis=1)
    df["Full Address"] = df[schema.address_fields].agg(" ".join, axis=1)
    (
        f"{df['Street_Number']} {df['Street_Name']} {df['Street_Type']} "
        f"{df['Street_Dir_Suffix']}"
    )
    DEMO_VOTER_RECORD_STATE = RegisteredVotersData(  # noqa: N806
        voters_df=df.astype(
            {
                "Full Name": pd.StringDtype(),
                "Full Address": pd.StringDtype(),
            }
        ),
        voter_schema=schema,
    )
    return DEMO_VOTER_RECORD_STATE
