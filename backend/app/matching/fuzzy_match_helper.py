# needed libraries
### structured outputs; replacements
import concurrent.futures
import json
import logging
import os
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial
from logging import Formatter
from math import log
from multiprocessing import cpu_count
from typing import Any

import numpy as np
import pandas as pd
import structlog
from app.logging.app_logger import AppLogger
from app.matching.match_columns import MatchColumns
from app.matching.response_adapter import (
    OcrMatchResults,
    create_ocr_match_result_response,
)
from app.ocr.data.ocr_repository import OcrResultItem
from app.ocr.data_model import OCREntry
from app.ocr.ocr_config import CropConfig, get_current_crop_config
from dotenv import load_dotenv
from pandas import DataFrame
from pandas.core.frame import DataFrame
from rapidfuzz import fuzz
from tqdm.notebook import tqdm

# local environment storage
# repo_name = "Ballot-Initiative"
# REPODIR = os.getcwd()
# load_dotenv(os.path.join(REPODIR, ".env"), override=True)

load_dotenv()
# Set up logging after imports

logger = structlog.get_logger(__name__)

log_format: Formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


###
## MATCHING FUNCTIONS
###

match_columns: MatchColumns = MatchColumns()


def _transform_ocr_results_to_df(result_item: OcrResultItem) -> dict[str, Any]:
    ocr_entry: OCREntry = result_item.ocr_entry
    return {
        MatchColumns.OCR_NAME: ocr_entry.Name,
        MatchColumns.OCR_ADDRESS: ocr_entry.Address,
        MatchColumns.DATE: ocr_entry.Date,
        MatchColumns.WARD: ocr_entry.Ward,
        MatchColumns.PAGE_NUMBER: result_item.page_num,
        MatchColumns.ROW_NUMBER: result_item.row_num,
        MatchColumns.FILE_NAME: result_item.file_name,
    }


def create_select_voter_records(voter_records: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a simplified DataFrame with full names and addresses from voter records.

    Args:
        voter_records (pd.DataFrame): DataFrame containing voter information with columns for
            first name, last name, and address components.

    Returns:
        pd.DataFrame: DataFrame with 'Full Name' and 'Full Address' columns
    """
    # Create full name by combining first and last names
    name_components: list[str] = ["First_Name", "Last_Name"]
    voter_records[name_components] = voter_records[name_components].fillna("")
    voter_records["Full Name"] = (
        voter_records[name_components].astype(str).agg(" ".join, axis=1)
    )

    # Create full address by combining address components
    address_components: list[str] = [
        "Street_Number",
        "Street_Name",
        "Street_Type",
        "Street_Dir_Suffix",
    ]
    voter_records[address_components] = voter_records[address_components].fillna("")
    voter_records["Full Address"] = (
        voter_records[address_components].astype(str).agg(" ".join, axis=1)
    )

    # Return only the columns we need
    return voter_records[["Full Name", "Full Address"]]


def score_fuzzy_match_slim(
    ocr_result: str, comparison_list: list[str], scorer_=fuzz.ratio, limit_=10
) -> list[tuple[str, int, int]]:
    """
    Scores the fuzzy match between the OCR result and the comparison list.

    Args:
        ocr_result (str): The OCR result to match.
        comparison_list (list[str]): The list of strings to compare against.
        scorer_ (function): The scorer function to use.
        limit_ (int): The number of top matches to return.

    Returns:
        list[tuple[str, int, int]]: The list of top matches with their scores and indices.
    """
    logger.debug(f"Starting fuzzy matching for: {ocr_result[:30]}...")

    # Convert to numpy array for faster operations
    comparison_array = np.array(comparison_list)

    # Vectorize the scorer function
    vectorized_scorer = np.vectorize(lambda x: scorer_(ocr_result, x))

    # Calculate all scores at once
    scores = vectorized_scorer(comparison_array)

    # Get top N indices
    top_indices = np.argpartition(scores, -limit_)[-limit_:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

    results = [(comparison_array[i], scores[i], i) for i in top_indices]
    logger.debug(f"Top match score: {results[0][1]}, Match: {results[0][0][:30]}...")
    return results


def get_matched_name_address(
    ocr_name: str, ocr_address: str, select_voter_records: pd.DataFrame
) -> list[tuple[str, str, float, int]]:
    """
    Optimized name and address matching

    Args:
        ocr_name (str): The OCR result for the name.
        ocr_address (str): The OCR result for the address.
        select_voter_records (pd.DataFrame): The DataFrame containing voter records.

    Returns:
        list[tuple[str, str, float, int]]: The list of top matches with their scores and indices.
    """
    logger.debug(f"Matching - Name: {ocr_name[:30]}... Address: {ocr_address[:30]}...")

    # Get name matches
    name_matches: list[tuple[str, int, int]] = score_fuzzy_match_slim(
        ocr_name, select_voter_records["Full Name"].values
    )
    logger.debug(f"Best name match score: {name_matches[0][1]}")

    # Get address matches
    matched_indices: list[int] = [x[2] for x in name_matches]
    relevant_addresses = select_voter_records["Full Address"].values[matched_indices]
    address_matches: list[tuple[str, int, int]] = score_fuzzy_match_slim(
        ocr_address, relevant_addresses
    )
    logger.debug(f"Best address match score: {address_matches[0][1]}")

    # Calculate harmonic means
    name_scores = np.array([x[1] for x in name_matches])
    addr_scores = np.array([x[1] for x in address_matches])
    harmonic_means = 2 * name_scores * addr_scores / (name_scores + addr_scores)

    # Create and sort results
    results: list[tuple[str, str, float, int]] = list[tuple[str, str, float, int]](
        zip(
            [x[0] for x in name_matches],
            [x[0] for x in address_matches],
            harmonic_means,
            matched_indices,
        )
    )
    results: list[tuple[str, str, float, int]] = sorted(
        results, key=lambda x: x[2], reverse=True
    )

    logger.debug(f"Best combined match score: {results[0][2]}")
    return results


def create_ocr_matched_df(
    ocr_df: pd.DataFrame,
    select_voter_records: pd.DataFrame,
    threshold: float | None = None,
    st_bar=None,
) -> pd.DataFrame:
    """
    Creates a DataFrame with matched name and address.

    Args:
        ocr_df (pd.DataFrame): The DataFrame containing OCR results.
        select_voter_records (pd.DataFrame): The DataFrame containing voter records.
        threshold (float): The threshold for matching.
        st_bar (st.progress): The progress bar to display.

    Returns:
        pd.DataFrame: The DataFrame with matched name and address.
    """
    logger.info(
        f"Starting matching process for {len(ocr_df)} records with threshold {threshold}"
    )

    total_records: int = len(ocr_df)

    if threshold is None:
        logger.debug(f"Setting default theshold value")
        threshold = get_current_crop_config().BASE_THRESHOLD

    # Process in batches for better memory management
    batch_size = 1000
    results: list[tuple[str, str, float]] = []
    total_batches: int = total_records // batch_size

    for batch_idx, batch_start in enumerate(
        range(0, total_records, batch_size), start=1
    ):
        batch: DataFrame = ocr_df.iloc[batch_start : batch_start + batch_size]

        names: list[str] = batch[match_columns.OCR_NAME].astype(str).tolist()
        addrs: list[str] = batch[match_columns.OCR_ADDRESS].astype(str).tolist()
        voters: list[DataFrame] = [select_voter_records] * len(names)

        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            futures = [
                executor.submit(
                    get_matched_name_address,
                    row[match_columns.OCR_NAME],
                    row[match_columns.OCR_ADDRESS],
                    select_voter_records,
                )
                for _, row in batch.iterrows()
            ]
            batch_results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Extract best matches
        batch_matches: list[tuple[str, str, float]] = []
        for res in batch_results:
            best: tuple[str, str, float, int] = res[0]
            batch_matches.append((best[0], best[1], float(best[2])))
        # batch_matches = [(res[0][0], res[0][1], res[0][2]) for res in batch_results]
        results.extend(batch_matches)

        # Log batch statistics
        batch_scores: list[float] = (
            [m[2] for m in batch_matches] if batch_matches else [0.0]
        )

        logger.info(
            f"Batch {batch_idx}/{total_batches} - records: {len(batch_matches)},\n"
            f"Avg score: {np.mean(batch_scores):.2f},\n"
            f"Min score: {min(batch_scores):.2f},\n"
            f"Max score: {max(batch_scores):.2f},\n"
            f"Valid matches: {sum(score >= threshold for score in batch_scores)}"
        )

        if st_bar:
            st_bar.progress(
                batch_start / len(ocr_df),
                text=f"Processing batch {batch_start} out of {len(ocr_df) // batch_size + 1} batches",
            )

    logger.info("Creating final DataFrame")
    match_df: DataFrame = pd.DataFrame(
        results,
        columns=[
            match_columns.MATCHED_NAME,
            match_columns.MATCHED_ADDRESS,
            match_columns.MATCH_SCORE,
        ],
    ).astype(
        {
            match_columns.MATCHED_NAME: pd.StringDtype(),
            match_columns.MATCHED_ADDRESS: pd.StringDtype(),
            match_columns.MATCH_SCORE: pd.Float64Dtype(),
        }
    )

    # TODO reset index on concat?
    logger.debug(
        f"size of voter records: {len(ocr_df)}\nsize of fuzzy match {len(match_df)}"
    )
    logger.debug(
        f"size of voter records columns: {len(ocr_df.columns)}\nsize of fuzzy match {len(match_df.columns)}"
    )

    logger.debug(f"OCR table")
    ocr_df.info()

    logger.debug(f"Matching table")
    match_df.info()

    result_df: DataFrame = pd.concat([ocr_df, match_df], axis=1)

    result_df[match_columns.VALID_MATCH] = (
        result_df[match_columns.MATCH_SCORE] >= threshold
    )

    # Reorder columns
    column_order: list[str] = match_columns.COLUMNS()

    # Log final statistics
    total_valid = result_df["Valid"].sum()
    logger.info(
        f"Matching complete - Total records: {len(result_df)}, "
        f"Valid matches: {total_valid} ({total_valid / len(result_df) * 100:.1f}%)"
    )

    return result_df[column_order]


async def perform_fuzzy_matching(
    ocr_results: Iterable[OcrResultItem], voter_records: DataFrame
) -> DataFrame:

    result_data: list[dict[str, Any]] = [
        _transform_ocr_results_to_df(item) for item in ocr_results
    ]
    ocr_df: DataFrame = pd.DataFrame(data=result_data, dtype=pd.StringDtype)

    logger.debug(f"perform_fuzzy_matching\n:{ocr_df.head()}")

    # TODO Separate fuzzy match configuration
    fuzzy_threshold = get_current_crop_config().BASE_THRESHOLD

    fuzzy_match_df: DataFrame = create_ocr_matched_df(
        select_voter_records=voter_records, ocr_df=ocr_df, threshold=fuzzy_threshold
    )

    logger.debug(f"Fuzzy matching found {len(fuzzy_match_df)} results.")
    return fuzzy_match_df
