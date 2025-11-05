from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO

import pandas as pd
from app.voter.voter_schema import VoterRegistrationSchema, get_default_voter_schema
from fastapi import UploadFile
from pandas import DataFrame


@dataclass
class RegisteredVotersData:
    voters_df: DataFrame
    voter_schema: VoterRegistrationSchema


DEMO_VOTER_RECORD_STATE: RegisteredVotersData | None = None


async def process_voter_data(voter_records_file: UploadFile) -> RegisteredVotersData:
    content_bytes = await voter_records_file.read()
    buffer = BytesIO(initial_bytes=content_bytes)
    df: DataFrame = pd.read_csv(buffer, dtype=str)

    df["Full Name"] = f"{df["First_Name"]} {df["Last_Name"]}"
    df["Full Address"] = (
        f"{df["Street_Number"]} {df["Street_Name"]} {df["Street_Type"]} {df["Street_Dir_Suffix"]}"
    )
    DEMO_VOTER_RECORD_STATE = RegisteredVotersData(
        voters_df=df, voter_schema=get_default_voter_schema()
    )
    return DEMO_VOTER_RECORD_STATE
