"""Voter list service for handling uploads and merge logic."""

import csv
import hashlib
from datetime import UTC, datetime
from io import StringIO
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload
from app.domain.field_spec import RegionFieldSpecConfig, VoterRegField


class VoterListService:
    """Service for managing voter list uploads and merge logic."""

    def __init__(self, session: Session):
        self.session = session

    def compute_data_hash_all(
        self,
        name_data: dict[str, Any],
        address_data: dict[str, Any],
        other_field_data: dict[str, Any],
        hash_fields: list[str],
    ) -> str:
        """Compute SHA-256 hash across all field categories."""
        all_fields = {**name_data, **address_data, **other_field_data}
        values = [
            self._normalize_name(str(all_fields.get(field, "")))
            for field in hash_fields
        ]
        combined = "|".join(values)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _normalize_name(self, value: str) -> str:
        """Normalize a field value for hashing."""
        return value.strip().lower()

    def parse_csv_with_spec(
        self, csv_content: str, spec: RegionFieldSpecConfig
    ) -> list[dict[str, Any]]:
        """Parse CSV using spec's voter_reg_fields for column mapping.

        Maps csv_column_name → voter_reg_field.id for each field in the spec.
        """
        column_map: dict[str, str] = {
            f.csv_column_name: f.id for f in spec.voter_reg_fields
        }
        reader = csv.DictReader(StringIO(csv_content))
        rows: list[dict[str, Any]] = []

        for row in reader:
            mapped: dict[str, Any] = {}
            for csv_col, field_id in column_map.items():
                if csv_col in row:
                    mapped[field_id] = row[csv_col]
            rows.append(mapped)

        return rows

    @staticmethod
    def group_by_category(
        mapped_fields: dict[str, Any],
        voter_reg_fields: list[VoterRegField],
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Group mapped fields into name_data, address_data, other_field_data blobs."""
        name_data: dict[str, str] = {}
        address_data: dict[str, str] = {}
        other_data: dict[str, str] = {}

        for field in voter_reg_fields:
            value = str(mapped_fields.get(field.id, ""))
            if field.category == "name":
                name_data[field.id] = value
            elif field.category == "address":
                address_data[field.id] = value
            else:
                other_data[field.id] = value

        return name_data, address_data, other_data

    def merge_voter_list_with_spec(
        self,
        region_id: Any,
        rows: list[dict[str, Any]],
        upload: Any,
        spec: RegionFieldSpecConfig,
    ) -> tuple[int, int]:
        """Spec-driven merge: group fields by category, hash across all blobs."""
        new_count = 0
        updated_count = 0

        for row in rows:
            name_data, address_data, other_data = self.group_by_category(
                row, spec.voter_reg_fields
            )
            data_hash = self.compute_data_hash_all(
                name_data, address_data, other_data, spec.hash_fields
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
                    other_field_data=other_data,
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

    def merge(
        self,
        region_id: Any,
        rows: list[dict[str, Any]],
        upload: Any,
        spec: RegionFieldSpecConfig | None = None,
    ) -> tuple[int, int]:
        """Merge voter list using spec-driven parsing and hashing."""
        if spec is None:
            raise ValueError("spec is required — hardcoded merge removed in G10")
        return self.merge_voter_list_with_spec(
            region_id=region_id, rows=rows, upload=upload, spec=spec
        )

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
