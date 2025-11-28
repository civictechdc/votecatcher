import asyncio
import base64
import logging
import os
from collections.abc import AsyncGenerator
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from logging import Formatter
from math import floor
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any

import fitz  # Add this import at the top with other imports
import pandas as pd
import pymupdf
from _asyncio import Task
from app.logging.app_logger import AppLogger
from app.ocr import extract_from_encoding_async
from app.ocr.batching.batch_handler import (
    create_batch_payload,
    observe_batch_job_status,
)
from app.ocr.batching.batch_ocr_client import BatchJobStatus, JobStatus
from app.ocr.batching.request_types import BatchEncodedImage, BatchOcrRequestInput
from app.ocr.data_model import EncodedPetitionDocuments, EncodedPetitionPage
from app.ocr.ocr_config import CropConfig, get_current_crop_config
from app.ocr.response_types import (
    MatchingJobStatusProgress,
    adapt_ocr_batch_status_to_progress_response,
)
from app.settings import load_settings
from dotenv import load_dotenv

# TODO explore migrating to PyMuPDF imports
from fitz import Page, Pixmap, Rect
from openai.types import batch
from pandas.core.frame import DataFrame
from tqdm.notebook import tqdm

load_dotenv()

# Set up logging after imports

logger = AppLogger.get_logger(
    log_name=__name__,
    # log_file=f"ocr_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
)

log_format: Formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# open ai api key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HELICONE_PERSONAL_API_KEY = os.getenv("HELICONE_PERSONAL_API_KEY")

OCR_COLUMNS: list[str] = ["OCR Name", "OCR Address", "OCR Ward"]


def encode_document_pages(file_path: Path) -> list[EncodedPetitionPage]:
    """Convert a PDF's pages to encoded images, cropping to target area.
    Returns list of base64 encoded image strings."""

    crop_config: CropConfig = get_current_crop_config()

    logger.info(f"Starting PDF conversion for file: {file_path}")
    encoded_image_list: list[EncodedPetitionPage] = []
    # Open PDF document
    with fitz.open(filename=file_path) as doc:

        total_pages = len(doc)

        logger.info(f"PDF opened successfully. Total pages: {total_pages}")
        logger.debug("\nCropping Images and Converting to Bytes Objects")
        # Process each page
        for page_num in range(total_pages):
            page: Page = doc[page_num]
            # Get page dimensions
            rect: Rect = page.rect
            width: float = rect.width
            height: float = rect.height

            # Calculate crop rectangle
            crop_rect: Rect = Rect(
                0,  # left
                height * crop_config.TOP_CROP,  # top
                width,  # right
                height * crop_config.BOTTOM_CROP,  # bottom
            )

            # Get pixmap with cropped area and grayscale
            pix: Pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1, 1),  # zoom factors of 1 = 72 dpi
                colorspace=fitz.csGRAY,  # convert to grayscale
                clip=crop_rect,  # crop to our target area
            )

            # Convert to bytes and encode
            img_bytes: bytes = pix.tobytes(output="jpeg")
            encoded: str = base64.b64encode(img_bytes).decode("utf-8")
            encoded_page: EncodedPetitionPage = EncodedPetitionPage(
                page_num=page_num,
                encoded_page=encoded,
                petition_file_name=file_path.name,
                petition_file_page_total=total_pages,
            )
            logger.debug(f"Encoded: {encoded}")
            # Adding each cropped encoded page to the list
            encoded_image_list.append(encoded_page)

        logger.info(
            f"Completed encoding for {file_path.name}. Generated {len(encoded_image_list)} encoded pages for OCR"
        )
    return encoded_image_list


# function for adding data
def add_metadata(initial_data: list[dict], page_no: int, filename: str) -> list[dict]:
    """
    Adds page number, row number, and filename metadata to the recognized signatures

    Args:
        initial_data (list[dict]): The initial data to add metadata to.
        page_no (int): The page number of the current page.
        filename (str): The name of the file.

    Returns:
        list[dict]: The final data with metadata.
    """

    final_data = list()
    for row, data in enumerate(initial_data):
        temp_dict = dict(data)
        temp_dict["Page Number"] = page_no + 1
        temp_dict["Row Number"] = row + 1
        temp_dict["Filename"] = filename
        final_data.append(temp_dict)

    return final_data


async def process_text_extraction(encodings: list[str]) -> list[list[dict]]:
    """
    Process a batch of images concurrently
    """
    async with asyncio.TaskGroup() as tg:
        tasks: list[Task[list[dict[Any, Any]]]] = [
            tg.create_task(extract_from_encoding_async(encoding))
            for encoding in encodings
        ]

    results = [task.result() for task in tasks]

    tasks = []
    for encoding in encodings:
        tasks.append(extract_from_encoding_async(encoding))

    results = await asyncio.gather(*tasks)
    return results


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


async def collect_ocr_data(
    filedir: str,
    filename: str,
    max_page_num: int = None,
    batch_size: int = 10,
    st_bar=None,
) -> list[dict]:
    """
    Collects OCR data from a PDF file.

    Args:
        filedir (str): The directory of the PDF file.
        filename (str): The name of the PDF file.
        max_page_num (int): The maximum number of pages to process.
        batch_size (int): The number of pages to process in each batch.
        st_bar (st.progress): A progress bar to display the progress of the OCR process.

    Returns:
        list: A list of dictionaries with the OCR data.
    """
    logger.info(f"Starting OCR collection for {filename}")
    logger.info(f"Parameters - max_page_num: {max_page_num}, batch_size: {batch_size}")

    # collecting images
    encoded_images: list[str] = []
    with ProcessPoolExecutor() as executor:
        for encoded_pages in executor.map(
            encode_document_pages, os.path.join(filedir, filename)
        ):
            for page in encoded_pages:
                encoded_images.extend(page.encoded_page)

    logger.debug(f"Collected {len(encoded_images)} images from scan.")
    # encoded_images = collecting_pdf_encoded_images(os.path.join(filedir, filename))

    # selecting pages
    if max_page_num:
        encoded_images = encoded_images[:max_page_num]
        logger.info(f"Limited processing to {max_page_num} pages")

    logger.debug(f"Files Successfully Converted to Bytes")
    logger.debug(f"Performing OCR to read Names and Addresses")

    full_data = []
    total_pages = len(encoded_images)

    # getting event loop
    loop = get_or_create_event_loop()

    # Process in batches
    logger.info(f"Processing {total_pages} pages in batches of {batch_size}")
    for i in tqdm(range(0, total_pages, batch_size)):
        batch = encoded_images[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1} of {(total_pages + batch_size - 1) // batch_size}"
        )

        if st_bar:
            st_bar.progress(
                i / total_pages,
                text="Processing pages {} to {} (of {})".format(
                    i + 1, i + batch_size, total_pages
                ),
            )

        # create_batch_payload()

        # Run async batch processing using the event loop
        batch_results = await process_text_extraction(batch)
        # batch_results = loop.run_until_complete(process_text_extraction(batch))

        # Add metadata for each result in the batch
        for page_idx, result in enumerate(batch_results):
            current_page = i + page_idx
            ocr_data = add_metadata(result, current_page, filename)
            full_data.extend(ocr_data)

        logger.info(
            f"Batch {i // batch_size + 1} complete. Processed {len(batch_results)} pages"
        )

    logger.info(f"OCR collection complete. Total entries: {len(full_data)}")
    return full_data


async def create_batched_ocr_job(
    campaign_id: str, files: list[Path]
) -> MatchingJobStatusProgress:
    total_pages = 0
    ocr_dfs: list[pd.DataFrame] = []
    """
    1 - List of files belonging to the same campaign
    2 - For each file, encoded the pages
    3 - Then compile a list of encoded files that each contain encoded pages
    4 - Submit the whole list to OCR
    5 - OCR iterates through each set of encoded files
    """
    pages: list[EncodedPetitionPage] = []
    with ProcessPoolExecutor() as executor:
        for encoded_file_pages in executor.map(encode_document_pages, files):
            total_pages += len(encoded_file_pages)
            pages.extend(encoded_file_pages)

    all_encoded_pages: EncodedPetitionDocuments = EncodedPetitionDocuments(
        campaign_id=campaign_id, encoded_pages=pages
    )

    request_data: BatchOcrRequestInput = BatchOcrRequestInput(
        campaign_id=campaign_id, encoded_petition_pages=all_encoded_pages
    )

    ocr_status: BatchJobStatus = await create_batch_payload(
        load_settings(enable_env_override=True).selected_config, request_data
    )
    return adapt_ocr_batch_status_to_progress_response(ocr_status)


async def emit_batch_job_status(
    job_id: str,
) -> AsyncGenerator[str, JobStatus]:
    async for job in observe_batch_job_status(job_id):
        logger.debug(f"Job {job.job_id} ended with status: {job.status}")
        match job.status:
            case (
                JobStatus.COMPLETED
                | JobStatus.CANCELLED
                | JobStatus.EXPIRED
                | JobStatus.FAILED
            ):

                yield MatchingJobStatusProgress(
                    campaign_id=job.campaign_id,
                    ocr_provider=job.provider_id,
                    started_at=job.started_at,
                    ocr_job_id=job.job_id,
                    job_status=job.status,
                    last_updated_at=job.last_updated_at,
                    failure_reason=job.error if job.error else None,
                    ended_at=job.completed_at if job.completed_at else None,
                ).model_dump_json()
                break
            case _:
                yield MatchingJobStatusProgress(
                    campaign_id=job.campaign_id,
                    ocr_provider=job.provider_id,
                    started_at=job.started_at,
                    ocr_job_id=job.job_id,
                    last_updated_at=job.last_updated_at,
                    job_status=job.status,
                ).model_dump_json()
        _ = await asyncio.sleep(5)  # 5 seconds poll rate


async def create_ocr_results(
    files: list[Path],
) -> list[pd.DataFrame]:

    total_pages = 0
    ocr_dfs: list[pd.DataFrame] = []
    encoded_batches: list[EncodedPetitionPage] = []
    with ProcessPoolExecutor() as executor:
        for res in executor.map(encode_document_pages, files):
            total_pages += len(res)
            encoded_batches.extend(res)

    logger.debug("Files Successfully Converted to Bytes")
    logger.debug("Performing OCR to read Names and Addresses")

    pages = len(encoded_batches)

    logger.info(f"Processing {total_pages} pages in {pages} groups")
    encoded: list[str] = []
    for l in encoded_batches:
        encoded.append(l.encoded_page)

    create_batch_payload(
        load_settings(enable_env_override=True).selected_config, encoded
    )
    return ocr_dfs

    idx = 0
    for file_path, batch in encoded_batches.items():
        full_data = []
        batch_results = await process_text_extraction(encodings=batch)
        # batch_results = loop.run_until_complete(process_text_extraction(batch))

        # Add metadata for each result in the batch
        for page_idx, result in enumerate(batch_results):
            current_page = idx + page_idx
            ocr_data = add_metadata(result, current_page, Path(file_path).name)
            full_data.extend(ocr_data)

        logger.info(
            f"Batch {idx // pages + 1} complete. Processed {len(batch_results)} pages"
        )

        logger.info(f"OCR collection complete. Total entries: {len(full_data)}")
        df: DataFrame = pd.DataFrame(data=full_data)
        logger.info(f"Created DataFrame with shape: {df.shape}")
        # renaming columns
        df.rename(
            columns={"Name": "OCR Name", "Address": "OCR Address", "Ward": "OCR Ward"},
            inplace=True,
        )
        # converting all caps names to title format
        df["OCR Name"] = df["OCR Name"].apply(lambda row: row.title())

        logger.info("OCR DataFrame creation complete")
        ocr_dfs.append(df)
        idx += idx

    return ocr_dfs


async def create_ocr_df(
    filedir: str,
    filename: str,
    max_page_num: int | None = None,
    batch_size: int = 10,
    st_bar=None,
) -> pd.DataFrame:
    """
    Creates a dataframe from OCR data.

    Args:
        filedir (str): The directory of the PDF file.
        filename (str): The name of the PDF file.
        max_page_num (int): The maximum number of pages to process.
        batch_size (int): The number of pages to process in each batch.
        st_bar (st.progress): A progress bar to display the progress of the OCR process.

    Returns:
        pd.DataFrame: A dataframe with the OCR data.
    """
    logger.info("Starting OCR DataFrame creation")

    # gathering ocr_data
    ocr_data = await collect_ocr_data(
        filedir,
        filename,
        max_page_num=max_page_num,
        batch_size=batch_size,
        st_bar=st_bar,
    )

    # convert dataframe
    ocr_df = pd.DataFrame(data=ocr_data)
    logger.info(f"Created DataFrame with shape: {ocr_df.shape}")

    # renaming columns
    ocr_df.rename(
        columns={"Name": "OCR Name", "Address": "OCR Address", "Ward": "OCR Ward"},
        inplace=True,
    )

    # converting all caps names to title format
    ocr_df["OCR Name"] = ocr_df["OCR Name"].apply(lambda row: row.title())

    logger.info("OCR DataFrame creation complete")
    return ocr_df
