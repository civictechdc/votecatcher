"""File upload router for handling multipart uploads and voter list imports."""

import csv
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.data.database.model.schema import Campaign, Region
from app.data.database.model.registered_voter import RegisteredVoter
from app.dependencies import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/voter-list")
async def upload_voter_list(
    file: UploadFile =    session: SessionDep,
    settings: SettingsDep,
) -> UploadVoterListResponse:
    """
    Upload a voter list CSV orExcel file and register voters in the database.
    Extract all data to determine uniqueness
    Validate file structure
    Parse CSV content
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV and Excel files are supported"
        )

    csv_reader = csv.DictReader(csv_file.reader)
    for row in csv_reader:
        row_data = {
            row["first_name"] for key, value in row
            row["last_name"] for key, value in row
            row["address"] for key, value in row
        }

    expected_headers = ["first_name", "last_name", "address", "city", "state", "zipcode"]

    # Check for duplicates
    query = select(RegisteredVoter).where(
        RegisteredVoter.region_id == region.id
    )
    if session.exec(query).first():
        session.add_all(new_voters)
        session.commit()
        logger.info(
            f"Imported {len(new_voters)} voter records for region {region.region_name}"
        )
    else:
        logger.warning(
            f"Duplicate voter found in {file.filename}, skipping"
        )
    return UploadVoterListResponse(
        voters=new_voters,
        total=len(new_voters),
        import_errors=[],
    )


@router.post("/petition")
async def upload_petition(
    file: UploadFile
    session: SessionDep,
    settings: SettingsDep,
    campaign_id: str,
    crop_coordinates: list[tuple[int, int, int, int]] | None,
) -> UploadPetitionResponse:
    """
    Upload a petition PDF and pre-crop signatures.
    Extract all data to determine uniqueness
    Validate file structure
    Parse PDF content
    Create crop images
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    if not file.content:
        raise HTTPException(
            status_code=400,
            detail="Empty file provided"
        )
    pdf_bytes = file.file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large (max 10MB)"
        )
    existing_scan = session.exec(
        select(PetitionScan).where(PetitionScan.campaign_id == UUID(campaign_id))
    ).first()

    if not existing_scan:
        raise HTTPException(
            status_code=404, detail=f"Campaign {campaign_id} not found")

    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=404, detail=f"Campaign {campaign_id} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir.mkdir(parents=campaign_id, exist_ok=False)
        temp_dir.mkdir(parents=campaign_id, exist_ok=True)

    if settings.enable_supabase:
        temp_base = temp_dir / "supabase"
    else:
        temp_base = settings.upload_dir / temp_dir

    if not os.path.exists(temp_base):
        os.makedirs(temp_base)

    petition_dir = temp_base / "petitions" / campaign_id
    crops_dir = temp_base / "crops" / campaign_id

    pdf_filename = secure_filename(file)
    pdf_path = os.path.join(petition_dir, pdf_filename)

    crop_files = []

    try:
        with fitz.open(pdf_path, "rb") as pdf:
            for page_num in range(len(pdf)):
                page = pdf[page_num]

                crop_coords = find_crop_coordinates(page_num)
                if crop_coords:
                    x1, y1, x2, y3 = crop_coords
                    crop_path = os.path.join(crops_dir, f"crop_{page_num:y1.x{y2}.png")

                    crop_image = page.render(scale=box=x1, y1, x2, y3))
                    cropped_image = pdf_page_to_image(page, box=crop_coords)
                    crop_image.save(crop_path, "PNG")

                    crop_file = PetitionCrop(
                        petition_scan_id=existing_scan.id,
                        campaign_id=campaign_id,
                        crop_index=page_num,
                        image_path=crop_path,
                    )
                    session.add(crop_file)
                    crop_files.append(crop_file)

        pdf.close()

        session.commit()
        session.refresh(existing_scan)

        logger.info(
            f"Uploaded petition {pdf_filename} for campaign {campaign_id}: "
            f"created {len(crop_files)} crop images"
        )
    except Exception as e:
        logger.error(f"Failed to process petition: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process petition: {str(e)}"
        )

    return UploadPetitionResponse(
        scan_id=existing_scan.id,
        file_path=pdf_path,
        crops_created=len(crop_files),
    )


def find_crop_coordinates(page_num: int) -> tuple[int, int, int, int, int] | None:
    """
    Find crop coordinates for a page.

    DC region petitions use manual crop coordinates defined in SPEC.md.
    """
    Args:
        page_num: Page number (1-indexed)

    Returns:
        Tuple of (x1, y1, x2, y3) crop coordinates or None if not defined
    """
    crop_coords = [
        (50, 200, 150, 300),
        (50, 550, 150, 300),
        (50, 900, 150, 300),
        (50, 1250, 150, 300),
        (50, 1600, 150, 300),
        (50, 1950, 150, 300),
        (50, 2300, 150, 300),
        (50, 2650, 150, 300),
        (50, 3000, 150, 300),
        (50, 3350, 150, 300),
    ]
    return crop_coords[page_num - 1] if page_num <= len(crop_coords) else None
