"""Voter list service for handling uploads and merge logic."""

import csv
import hashlib
from datetime import UTC, datetime
from io import StringIO
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.data.database.model.region_schema import RegionSchema
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload


class VoterListService:
    """Service for managing voter list uploads and merge logic."""

    def __init__(self, session: Session):
        self.session = session

    def compute_data_hash(
        self,
        name_data: dict[str, Any],
        address_data: dict[str, Any],
        hash_fields: list[str],
    ) -> str:
        """Compute SHA-256 hash from normalized field values."""
        values = []

        for field in hash_fields:
            if field in name_data:
                values.append(self._normalize_name(str(name_data[field])))
            elif field in address_data:
                values.append(self._normalize_name(str(address_data[field])))

        combined = "|".join(values)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _normalize_name(self, value: str) -> str:
        """Normalize a field value for hashing."""
        return value.strip().lower()

    def parse_csv_with_schema(
        self, csv_content: str, schema: RegionSchema
    ) -> list[dict[str, Any]]:
        """Parse CSV using region schema mappings."""
        reader = csv.DictReader(StringIO(csv_content))
        rows = []

        for row in reader:
            mapped: dict[str, Any] = {}
            for csv_col, canonical in schema.column_mappings.items():
                if csv_col in row:
                    mapped[canonical] = row[csv_col]
            rows.append(mapped)

        return rows

    def get_or_create_schema(self, region_id: UUID) -> RegionSchema:
        """Get existing schema or create default."""
        schema = self.session.exec(
            select(RegionSchema).where(RegionSchema.region_id == region_id)
        ).first()

        if schema:
            return schema

        schema = RegionSchema(
            region_id=region_id,
            name="Default Schema",
            column_mappings={
                "FirstName": "first_name",
                "LastName": "last_name",
                "Street": "street",
                "City": "city",
                "State": "state",
                "Zip": "zip",
            },
            hash_fields=["first_name", "last_name", "street", "zip"],
        )
        self.session.add(schema)
        self.session.commit()
        self.session.refresh(schema)
        return schema

    def merge_voter_list(
        self,
        region_id: UUID,
        rows: list[dict[str, Any]],
        upload: VoterListUpload,
    ) -> tuple[int, int]:
        """Merge voter rows with existing voters. Returns (new_count, updated_count)."""
        schema = self.get_or_create_schema(region_id)
        new_count = 0
        updated_count = 0

        for row in rows:
            name_data = {
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
            }
            address_data = {
                "street": row.get("street", ""),
                "city": row.get("city", ""),
                "state": row.get("state", ""),
                "zip": row.get("zip", ""),
            }

            data_hash = self.compute_data_hash(
                name_data, address_data, schema.hash_fields
            )

            existing = self.session.exec(
                select(RegisteredVoter).where(
                    RegisteredVoter.region_id == region_id,
                    RegisteredVoter.data_hash == data_hash,
                )
            ).first()

            now = datetime.now(UTC)
            if existing:
                existing.last_seen_at = now
                existing.last_upload_id = upload.id
                updated_count += 1
            else:
                voter = RegisteredVoter(
                    region_id=region_id,
                    name_data=name_data,
                    address_data=address_data,
                    other_field_data={},
                    data_hash=data_hash,
                    first_seen_at=now,
                    last_seen_at=now,
                    first_upload_id=upload.id,
                    last_upload_id=upload.id,
                )
                self.session.add(voter)
                new_count += 1

        self.session.commit()
        return (new_count, updated_count)

    def supersede_previous_uploads(self, region_id: UUID, new_upload: VoterListUpload):
        """Mark previous active uploads as superseded."""
        previous = self.session.exec(
            select(VoterListUpload).where(
                VoterListUpload.region_id == region_id,
                VoterListUpload.status == UploadStatus.ACTIVE,
                VoterListUpload.id != new_upload.id,
            )
        ).all()

        for upload in previous:
            upload.status = UploadStatus.SUPERSEDED
            upload.superseded_at = datetime.now(UTC)
            upload.superseded_by = new_upload.id

        self.session.commit()

    def get_active_upload(self, region_id: UUID) -> VoterListUpload | None:
        """Get the current active upload for a region."""
        return self.session.exec(
            select(VoterListUpload)
            .where(
                VoterListUpload.region_id == region_id,
                VoterListUpload.status == UploadStatus.ACTIVE,
            )
            .order_by(VoterListUpload.uploaded_at.desc())
        ).first()

    def delete_voters_for_region(self, region_id: UUID) -> int:
        """Delete all voters for a region. Returns count deleted."""
        voters = self.session.exec(
            select(RegisteredVoter).where(RegisteredVoter.region_id == region_id)
        ).all()

        count = len(voters)
        for voter in voters:
            self.session.delete(voter)

        self.session.commit()
        return count
