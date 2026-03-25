# Voter List Tracking + Dashboard Progress Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add voter list upload tracking with region-scoped visibility and dashboard progress stepper to guide users through campaign setup.

**Architecture:** New `voter_list_uploads` and `region_schemas` tables track upload history and parsing rules. VoterListService handles merge/update logic with hash-based deduplication. Frontend ProgressStepper component shows contextual next actions.

**Tech Stack:** FastAPI, SQLModel, SvelteKit, Tailwind CSS

---

## Phase 1: Database Models

### Task 1: Create VoterListUpload Model

**Files:**
- Create: `backend/app/data/database/model/voter_list_upload.py`
- Modify: `backend/app/data/database/model/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/models/test_voter_list_upload.py`:

```python
import pytest
from datetime import datetime
from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus

def test_voter_list_upload_creation():
    upload = VoterListUpload(
        region_id=1,
        original_filename="voters.csv",
        file_size=12345,
        row_count=1000,
        status=UploadStatus.ACTIVE
    )
    assert upload.original_filename == "voters.csv"
    assert upload.status == UploadStatus.ACTIVE
    assert upload.superseded_at is None

def test_voter_list_upload_status_enum():
    assert UploadStatus.ACTIVE == "active"
    assert UploadStatus.SUPERSEDED == "superseded"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/models/test_voter_list_upload.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write the model**

Create `backend/app/data/database/model/voter_list_upload.py`:

```python
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class UploadStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class VoterListUpload(SQLModel, table=True):
    __tablename__ = "voter_list_uploads"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    region_id: UUID = Field(foreign_key="regions.id", nullable=False, index=True)
    original_filename: str = Field(nullable=False)
    file_size: int = Field(nullable=False)
    row_count: int = Field(nullable=False)
    status: UploadStatus = Field(default=UploadStatus.ACTIVE)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    superseded_at: datetime | None = Field(default=None)
    superseded_by: UUID | None = Field(default=None, foreign_key="voter_list_uploads.id")
```

**Step 4: Update model exports**

Modify `backend/app/data/database/model/__init__.py`:

```python
from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus

__all__ = [
    # ... existing exports ...
    "VoterListUpload",
    "UploadStatus",
]
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/models/test_voter_list_upload.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/data/database/model/voter_list_upload.py backend/app/data/database/model/__init__.py backend/tests/unit/models/test_voter_list_upload.py
git commit -m "feat(models): add VoterListUpload model for tracking voter list history"
```

---

### Task 2: Create RegionSchema Model

**Files:**
- Create: `backend/app/data/database/model/region_schema.py`
- Modify: `backend/app/data/database/model/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/models/test_region_schema.py`:

```python
import pytest
from app.data.database.model.region_schema import RegionSchema

def test_region_schema_creation():
    schema = RegionSchema(
        region_id=1,
        name="DC Voter Roll",
        column_mappings={"VoterID": "voter_id", "FirstName": "first_name"},
        hash_fields=["first_name", "last_name", "street", "zip"]
    )
    assert schema.name == "DC Voter Roll"
    assert "VoterID" in schema.column_mappings
    assert len(schema.hash_fields) == 4

def test_region_schema_defaults():
    schema = RegionSchema(region_id=1, name="Test", column_mappings={}, hash_fields=[])
    assert schema.column_mappings == {}
    assert schema.hash_fields == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/models/test_region_schema.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write the model**

Create `backend/app/data/database/model/region_schema.py`:

```python
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from typing import Any


class RegionSchema(SQLModel, table=True):
    __tablename__ = "region_schemas"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    region_id: UUID = Field(foreign_key="regions.id", nullable=False, unique=True, index=True)
    name: str = Field(nullable=False)
    column_mappings: dict[str, str] = Field(default_factory=dict, sa_column_kwargs={"type_": "json"})
    hash_fields: list[str] = Field(default_factory=list, sa_column_kwargs={"type_": "json"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Step 4: Update model exports**

Modify `backend/app/data/database/model/__init__.py`:

```python
from app.data.database.model.region_schema import RegionSchema

__all__ = [
    # ... existing exports ...
    "RegionSchema",
]
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/models/test_region_schema.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/data/database/model/region_schema.py backend/app/data/database/model/__init__.py backend/tests/unit/models/test_region_schema.py
git commit -m "feat(models): add RegionSchema model for CSV column mapping"
```

---

### Task 3: Add Tracking Fields to RegisteredVoter

**Files:**
- Modify: `backend/app/data/database/model/registered_voter.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/models/test_registered_voter_tracking.py`:

```python
import pytest
from datetime import datetime
from app.data.database.model.registered_voter import RegisteredVoter

def test_registered_voter_tracking_fields():
    voter = RegisteredVoter(
        region_id=1,
        name_data={"first": "John", "last": "Doe"},
        address_data={"street": "123 Main St"},
        data_hash="abc123",
        first_upload_id="00000000-0000-0000-0000-000000000001",
        last_upload_id="00000000-0000-0000-0000-000000000002"
    )
    assert voter.data_hash == "abc123"
    assert voter.first_upload_id is not None
    assert voter.last_upload_id is not None

def test_registered_voter_tracking_timestamps():
    voter = RegisteredVoter(
        region_id=1,
        name_data={},
        address_data={},
        data_hash="xyz789"
    )
    assert voter.first_seen_at is not None
    assert voter.last_seen_at is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/models/test_registered_voter_tracking.py -v`
Expected: FAIL with "AttributeError: 'RegisteredVoter' object has no attribute 'data_hash'"

**Step 3: Update the model**

Modify `backend/app/data/database/model/registered_voter.py`:

Add imports:
```python
from uuid import UUID
```

Add new fields to the model:
```python
class RegisteredVoter(SQLModel, table=True):
    # ... existing fields ...

    # Tracking fields for voter list uploads
    data_hash: str | None = Field(default=None, index=True)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    first_upload_id: UUID | None = Field(default=None, foreign_key="voter_list_uploads.id")
    last_upload_id: UUID | None = Field(default=None, foreign_key="voter_list_uploads.id")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/models/test_registered_voter_tracking.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/data/database/model/registered_voter.py backend/tests/unit/models/test_registered_voter_tracking.py
git commit -m "feat(models): add tracking fields to RegisteredVoter for upload history"
```

---

### Task 4: Create Database Migration

**Files:**
- Create: `backend/app/data/database/migrations/001_add_voter_list_tracking.py`

**Step 1: Create migration script**

Create `backend/app/data/database/migrations/001_add_voter_list_tracking.py`:

```python
"""
Migration: Add voter_list_uploads, region_schemas tables and tracking fields to registered_voters

Run with: alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


def upgrade():
    # Create voter_list_uploads table
    op.create_table(
        'voter_list_uploads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('region_id', sa.String(36), sa.ForeignKey('regions.id'), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('row_count', sa.Integer, nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('uploaded_at', sa.DateTime, nullable=False),
        sa.Column('superseded_at', sa.DateTime, nullable=True),
        sa.Column('superseded_by', sa.String(36), sa.ForeignKey('voter_list_uploads.id'), nullable=True),
    )
    op.create_index('ix_voter_list_uploads_region_id', 'voter_list_uploads', ['region_id'])

    # Create region_schemas table
    op.create_table(
        'region_schemas',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('region_id', sa.String(36), sa.ForeignKey('regions.id'), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('column_mappings', sa.JSON, default={}),
        sa.Column('hash_fields', sa.JSON, default=[]),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_region_schemas_region_id', 'region_schemas', ['region_id'])

    # Add tracking fields to registered_voters
    op.add_column('registered_voters', sa.Column('data_hash', sa.String(64), nullable=True))
    op.add_column('registered_voters', sa.Column('first_seen_at', sa.DateTime, nullable=True))
    op.add_column('registered_voters', sa.Column('last_seen_at', sa.DateTime, nullable=True))
    op.add_column('registered_voters', sa.Column('first_upload_id', sa.String(36), sa.ForeignKey('voter_list_uploads.id'), nullable=True))
    op.add_column('registered_voters', sa.Column('last_upload_id', sa.String(36), sa.ForeignKey('voter_list_uploads.id'), nullable=True))
    op.create_index('ix_registered_voters_data_hash', 'registered_voters', ['data_hash'])

    # Backfill existing voters
    op.execute("""
        UPDATE registered_voters
        SET first_seen_at = created_at,
            last_seen_at = COALESCE(updated_at, created_at)
        WHERE first_seen_at IS NULL
    """)


def downgrade():
    op.drop_index('ix_registered_voters_data_hash', 'registered_voters')
    op.drop_column('registered_voters', 'last_upload_id')
    op.drop_column('registered_voters', 'first_upload_id')
    op.drop_column('registered_voters', 'last_seen_at')
    op.drop_column('registered_voters', 'first_seen_at')
    op.drop_column('registered_voters', 'data_hash')
    op.drop_index('ix_region_schemas_region_id', 'region_schemas')
    op.drop_table('region_schemas')
    op.drop_index('ix_voter_list_uploads_region_id', 'voter_list_uploads')
    op.drop_table('voter_list_uploads')
```

**Step 2: Commit**

```bash
git add backend/app/data/database/migrations/001_add_voter_list_tracking.py
git commit -m "feat(db): add migration for voter list tracking tables"
```

---

## Phase 2: Backend Services

### Task 5: Create VoterListService

**Files:**
- Create: `backend/app/services/voter_list_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/services/test_voter_list_service.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.services.voter_list_service import VoterListService
from app.data.database.model.voter_list_upload import UploadStatus

def test_compute_data_hash():
    service = VoterListService(Mock())
    name_data = {"first": "John", "last": "Doe"}
    address_data = {"street": "123 Main St", "zip": "12345"}
    hash_fields = ["first_name", "last_name", "street", "zip"]

    result = service.compute_data_hash(name_data, address_data, hash_fields)

    assert result is not None
    assert len(result) == 64  # SHA-256 hex digest

def test_compute_data_hash_consistent():
    service = VoterListService(Mock())
    name_data = {"first": "Jane", "last": "Smith"}
    address_data = {"street": "456 Oak Ave", "zip": "67890"}
    hash_fields = ["first_name", "last_name", "street", "zip"]

    hash1 = service.compute_data_hash(name_data, address_data, hash_fields)
    hash2 = service.compute_data_hash(name_data, address_data, hash_fields)

    assert hash1 == hash2

def test_normalize_name():
    service = VoterListService(Mock())

    assert service._normalize_name("  JOHN  ") == "john"
    assert service._normalize_name("McDonald") == "mcdonald"
    assert service._normalize_name("") == ""
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/services/test_voter_list_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write the service**

Create `backend/app/services/voter_list_service.py`:

```python
import hashlib
import csv
from io import StringIO
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
from typing import Any

from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus
from app.data.database.model.region_schema import RegionSchema
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.region import Region


class VoterListService:
    def __init__(self, session: Session):
        self.session = session

    def compute_data_hash(
        self,
        name_data: dict[str, Any],
        address_data: dict[str, Any],
        hash_fields: list[str]
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
        self,
        csv_content: str,
        schema: RegionSchema
    ) -> list[dict[str, Any]]:
        """Parse CSV using region schema mappings."""
        reader = csv.DictReader(StringIO(csv_content))
        rows = []

        for row in reader:
            mapped = {}
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

        # Create default schema
        schema = RegionSchema(
            region_id=region_id,
            name="Default Schema",
            column_mappings={
                "FirstName": "first_name",
                "LastName": "last_name",
                "Street": "street",
                "City": "city",
                "State": "state",
                "Zip": "zip"
            },
            hash_fields=["first_name", "last_name", "street", "zip"]
        )
        self.session.add(schema)
        self.session.commit()
        self.session.refresh(schema)
        return schema

    def merge_voter_list(
        self,
        region_id: UUID,
        rows: list[dict[str, Any]],
        upload: VoterListUpload
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

            data_hash = self.compute_data_hash(name_data, address_data, schema.hash_fields)

            existing = self.session.exec(
                select(RegisteredVoter).where(
                    RegisteredVoter.region_id == region_id,
                    RegisteredVoter.data_hash == data_hash
                )
            ).first()

            if existing:
                existing.last_seen_at = datetime.utcnow()
                existing.last_upload_id = upload.id
                updated_count += 1
            else:
                voter = RegisteredVoter(
                    region_id=region_id,
                    name_data=name_data,
                    address_data=address_data,
                    other_field_data={},
                    data_hash=data_hash,
                    first_seen_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow(),
                    first_upload_id=upload.id,
                    last_upload_id=upload.id
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
                VoterListUpload.id != new_upload.id
            )
        ).all()

        for upload in previous:
            upload.status = UploadStatus.SUPERSEDED
            upload.superseded_at = datetime.utcnow()
            upload.superseded_by = new_upload.id

        self.session.commit()

    def get_active_upload(self, region_id: UUID) -> VoterListUpload | None:
        """Get the current active upload for a region."""
        return self.session.exec(
            select(VoterListUpload).where(
                VoterListUpload.region_id == region_id,
                VoterListUpload.status == UploadStatus.ACTIVE
            ).order_by(VoterListUpload.uploaded_at.desc())
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
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/services/test_voter_list_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/voter_list_service.py backend/tests/unit/services/test_voter_list_service.py
git commit -m "feat(services): add VoterListService with merge/update logic"
```

---

### Task 6: Add Integration Tests for VoterListService

**Files:**
- Create: `backend/tests/integration/services/test_voter_list_service.py`

**Step 1: Write integration test**

Create `backend/tests/integration/services/test_voter_list_service.py`:

```python
import pytest
from uuid import uuid4
from app.services.voter_list_service import VoterListService
from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus
from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.region import Region


@pytest.fixture
def voter_list_service(session):
    return VoterListService(session)


@pytest.fixture
def test_region(session):
    region = Region(name="Test Region")
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


def test_merge_voter_list_creates_new_voters(session, voter_list_service, test_region):
    upload = VoterListUpload(
        region_id=test_region.id,
        original_filename="test.csv",
        file_size=1000,
        row_count=2,
        status=UploadStatus.ACTIVE
    )
    session.add(upload)
    session.commit()

    rows = [
        {"first_name": "John", "last_name": "Doe", "street": "123 Main", "city": "City", "state": "ST", "zip": "12345"},
        {"first_name": "Jane", "last_name": "Smith", "street": "456 Oak", "city": "City", "state": "ST", "zip": "67890"},
    ]

    new_count, updated_count = voter_list_service.merge_voter_list(test_region.id, rows, upload)

    assert new_count == 2
    assert updated_count == 0


def test_merge_voter_list_updates_existing(session, voter_list_service, test_region):
    upload1 = VoterListUpload(
        region_id=test_region.id,
        original_filename="test1.csv",
        file_size=1000,
        row_count=1,
        status=UploadStatus.ACTIVE
    )
    session.add(upload1)
    session.commit()

    rows = [
        {"first_name": "John", "last_name": "Doe", "street": "123 Main", "city": "City", "state": "ST", "zip": "12345"},
    ]

    voter_list_service.merge_voter_list(test_region.id, rows, upload1)

    upload2 = VoterListUpload(
        region_id=test_region.id,
        original_filename="test2.csv",
        file_size=1000,
        row_count=1,
        status=UploadStatus.ACTIVE
    )
    session.add(upload2)
    session.commit()

    new_count, updated_count = voter_list_service.merge_voter_list(test_region.id, rows, upload2)

    assert new_count == 0
    assert updated_count == 1


def test_supersede_previous_uploads(session, voter_list_service, test_region):
    upload1 = VoterListUpload(
        region_id=test_region.id,
        original_filename="old.csv",
        file_size=1000,
        row_count=1,
        status=UploadStatus.ACTIVE
    )
    session.add(upload1)
    session.commit()

    upload2 = VoterListUpload(
        region_id=test_region.id,
        original_filename="new.csv",
        file_size=1000,
        row_count=1,
        status=UploadStatus.ACTIVE
    )
    session.add(upload2)
    session.commit()

    voter_list_service.supersede_previous_uploads(test_region.id, upload2)

    session.refresh(upload1)
    assert upload1.status == UploadStatus.SUPERSEDED
    assert upload1.superseded_by == upload2.id
```

**Step 2: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/integration/services/test_voter_list_service.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/services/test_voter_list_service.py
git commit -m "test(integration): add VoterListService integration tests"
```

---

## Phase 3: API Endpoints

### Task 7: Add Voter List Status Endpoint

**Files:**
- Modify: `backend/app/routers/upload_router.py`

**Step 1: Write the failing test**

Create `backend/tests/integration/api/test_voter_list_status.py`:

```python
import pytest
from uuid import uuid4


def test_get_voter_list_status_returns_null_when_none(client, test_campaign):
    response = client.get(f"/api/regions/{test_campaign.region_id}/voter-list")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["upload"] is None


def test_get_voter_list_status_returns_upload_info(client, session, test_campaign):
    from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus

    upload = VoterListUpload(
        region_id=test_campaign.region_id,
        original_filename="voters.csv",
        file_size=12345,
        row_count=1000,
        status=UploadStatus.ACTIVE
    )
    session.add(upload)
    session.commit()

    response = client.get(f"/api/regions/{test_campaign.region_id}/voter-list")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["upload"]["original_filename"] == "voters.csv"
    assert data["upload"]["row_count"] == 1000
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/integration/api/test_voter_list_status.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Add the endpoint**

Modify `backend/app/routers/upload_router.py`:

Add imports:
```python
from app.services.voter_list_service import VoterListService
from app.data.database.model.voter_list_upload import VoterListUpload
```

Add endpoint:
```python
@router.get("/regions/{region_id}/voter-list")
async def get_voter_list_status(
    region_id: UUID,
    session: Session = Depends(get_session)
) -> dict:
    """Get the current voter list status for a region."""
    service = VoterListService(session)
    upload = service.get_active_upload(region_id)

    if not upload:
        return {"exists": False, "upload": None}

    return {
        "exists": True,
        "upload": {
            "id": str(upload.id),
            "original_filename": upload.original_filename,
            "file_size": upload.file_size,
            "row_count": upload.row_count,
            "uploaded_at": upload.uploaded_at.isoformat(),
            "status": upload.status.value
        }
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/integration/api/test_voter_list_status.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers/upload_router.py backend/tests/integration/api/test_voter_list_status.py
git commit -m "feat(api): add GET /regions/{id}/voter-list endpoint"
```

---

### Task 8: Add Delete Voter List Endpoint

**Files:**
- Modify: `backend/app/routers/upload_router.py`

**Step 1: Write the failing test**

Add to `backend/tests/integration/api/test_voter_list_status.py`:

```python
def test_delete_voter_list_removes_voters(client, session, test_campaign):
    from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus
    from app.data.database.model.registered_voter import RegisteredVoter

    upload = VoterListUpload(
        region_id=test_campaign.region_id,
        original_filename="voters.csv",
        file_size=12345,
        row_count=1,
        status=UploadStatus.ACTIVE
    )
    session.add(upload)

    voter = RegisteredVoter(
        region_id=test_campaign.region_id,
        name_data={"first": "John", "last": "Doe"},
        address_data={"street": "123 Main"},
        data_hash="abc123"
    )
    session.add(voter)
    session.commit()

    response = client.delete(f"/api/regions/{test_campaign.region_id}/voter-list")
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1

    # Verify voter is gone
    voters = session.exec(select(RegisteredVoter).where(RegisteredVoter.region_id == test_campaign.region_id)).all()
    assert len(voters) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/integration/api/test_voter_list_status.py::test_delete_voter_list_removes_voters -v`
Expected: FAIL with "404 Not Found"

**Step 3: Add the endpoint**

Modify `backend/app/routers/upload_router.py`:

Add endpoint:
```python
@router.delete("/regions/{region_id}/voter-list")
async def delete_voter_list(
    region_id: UUID,
    session: Session = Depends(get_session)
) -> dict:
    """Delete all voters for a region and mark uploads as superseded."""
    service = VoterListService(session)

    deleted_count = service.delete_voters_for_region(region_id)

    # Mark all uploads as superseded
    uploads = session.exec(
        select(VoterListUpload).where(VoterListUpload.region_id == region_id)
    ).all()
    for upload in uploads:
        upload.status = UploadStatus.SUPERSEDED

    session.commit()

    return {"deleted_count": deleted_count, "success": True}
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/integration/api/test_voter_list_status.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers/upload_router.py backend/tests/integration/api/test_voter_list_status.py
git commit -m "feat(api): add DELETE /regions/{id}/voter-list endpoint"
```

---

### Task 9: Add Campaign Setup Status Endpoint

**Files:**
- Modify: `backend/app/routers/campaign_router.py`

**Step 1: Write the failing test**

Create `backend/tests/integration/api/test_campaign_setup_status.py`:

```python
import pytest


def test_get_setup_status_empty_campaign(client, test_campaign):
    response = client.get(f"/api/campaigns/{test_campaign.id}/setup-status")
    assert response.status_code == 200
    data = response.json()
    assert data["voter_list"]["exists"] is False
    assert data["petitions"]["exists"] is False
    assert data["jobs"]["total"] == 0
    assert data["state"] == "empty"


def test_get_setup_status_ready_to_process(client, session, test_campaign):
    from app.data.database.model.voter_list_upload import VoterListUpload, UploadStatus
    from app.data.database.model.petition_scan import PetitionScan

    upload = VoterListUpload(
        region_id=test_campaign.region_id,
        original_filename="voters.csv",
        file_size=12345,
        row_count=1000,
        status=UploadStatus.ACTIVE
    )
    session.add(upload)

    scan = PetitionScan(
        campaign_id=test_campaign.id,
        original_filename="petition.pdf",
        file_size=5000,
        page_count=5
    )
    session.add(scan)
    session.commit()

    response = client.get(f"/api/campaigns/{test_campaign.id}/setup-status")
    assert response.status_code == 200
    data = response.json()
    assert data["voter_list"]["exists"] is True
    assert data["petitions"]["exists"] is True
    assert data["state"] == "ready_to_process"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/integration/api/test_campaign_setup_status.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Add the endpoint**

Modify `backend/app/routers/campaign_router.py`:

Add imports:
```python
from app.services.voter_list_service import VoterListService
from app.data.database.model.voter_list_upload import VoterListUpload
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.job import Job
```

Add endpoint:
```python
@router.get("/{campaign_id}/setup-status")
async def get_setup_status(
    campaign_id: UUID,
    session: Session = Depends(get_session)
) -> dict:
    """Get campaign setup status for progress stepper."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    voter_list_service = VoterListService(session)
    voter_upload = voter_list_service.get_active_upload(campaign.region_id)

    scans = session.exec(
        select(PetitionScan).where(PetitionScan.campaign_id == campaign_id)
    ).all()

    jobs = session.exec(
        select(Job).where(Job.campaign_id == campaign_id)
    ).all()

    has_voter_list = voter_upload is not None
    has_petitions = len(scans) > 0
    has_jobs = len(jobs) > 0

    # Determine state
    if not has_voter_list and not has_petitions:
        state = "empty"
    elif has_voter_list and not has_petitions:
        state = "voter_only"
    elif not has_voter_list and has_petitions:
        state = "petitions_only"
    elif not has_jobs:
        state = "ready_to_process"
    else:
        state = "has_jobs"

    return {
        "voter_list": {
            "exists": has_voter_list,
            "row_count": voter_upload.row_count if voter_upload else None,
            "uploaded_at": voter_upload.uploaded_at.isoformat() if voter_upload else None,
            "region_name": campaign.region
        },
        "petitions": {
            "exists": has_petitions,
            "file_count": len(scans),
            "signature_count": sum(s.page_count or 0 for s in scans)
        },
        "jobs": {
            "total": len(jobs),
            "active": len([j for j in jobs if j.status in ["NOT_STARTED", "OCR_PENDING", "OCR_STARTED", "MATCHING"]])
        },
        "state": state
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/integration/api/test_campaign_setup_status.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers/campaign_router.py backend/tests/integration/api/test_campaign_setup_status.py
git commit -m "feat(api): add GET /campaigns/{id}/setup-status endpoint"
```

---

## Phase 4: Frontend Components

### Task 10: Create ProgressStepper Component

**Files:**
- Create: `frontend-svelt/src/lib/components/dashboard/ProgressStepper.svelte`

**Step 1: Create the component**

Create `frontend-svelt/src/lib/components/dashboard/ProgressStepper.svelte`:

```svelte
<script lang="ts">
	import { Button } from '$lib/components/ui';

	interface VoterListStatus {
		exists: boolean;
		row_count?: number;
		uploaded_at?: string;
		region_name?: string;
	}

	interface PetitionStatus {
		exists: boolean;
		file_count?: number;
		signature_count?: number;
	}

	interface Props {
		voterListStatus: VoterListStatus | null;
		petitionStatus: PetitionStatus | null;
		hasJobs: boolean;
		campaignId: string;
	}

	let { voterListStatus, petitionStatus, hasJobs, campaignId }: Props = $props();

	const state = $derived(() => {
		const hasVoterList = voterListStatus?.exists ?? false;
		const hasPetitions = petitionStatus?.exists ?? false;

		if (!hasVoterList && !hasPetitions) return 'empty';
		if (hasVoterList && !hasPetitions) return 'voter_only';
		if (!hasVoterList && hasPetitions) return 'petitions_only';
		if (!hasJobs) return 'ready_to_process';
		return 'has_jobs';
	});

	function formatCount(count: number | undefined): string {
		if (!count) return '0';
		return count.toLocaleString();
	}

	function formatDate(dateStr: string | undefined): string {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		});
	}

	const ctaConfig = $derived(() => {
		switch (state()) {
			case 'empty':
				return { text: 'Upload Voter List', href: `/workspace/${campaignId}/upload` };
			case 'voter_only':
				return { text: 'Upload Petitions', href: `/workspace/${campaignId}/upload` };
			case 'petitions_only':
				return { text: 'Upload Voter List', href: `/workspace/${campaignId}/upload` };
			case 'ready_to_process':
				return { text: 'Create Job', href: `/workspace/${campaignId}/jobs` };
			default:
				return null;
		}
	});
</script>

{#if state() !== 'has_jobs'}
	<div class="rounded-lg border border-slate-200 bg-white p-6 mb-6">
		<h2 class="text-lg font-semibold text-slate-900 mb-4">Campaign Setup</h2>

		<div class="space-y-3">
			<!-- Voter List Step -->
			<div class="flex items-center gap-3">
				{#if voterListStatus?.exists}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div class="flex-1">
						<span class="font-medium text-slate-900">Voter List</span>
						<span class="text-sm text-slate-500 ml-2">
							{formatCount(voterListStatus.row_count)} voters
							{#if voterListStatus.region_name}• {voterListStatus.region_name}{/if}
							{#if voterListStatus.uploaded_at}• Updated {formatDate(voterListStatus.uploaded_at)}{/if}
						</span>
					</div>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Voter List</span>
				{/if}
			</div>

			<!-- Petitions Step -->
			<div class="flex items-center gap-3">
				{#if petitionStatus?.exists}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div class="flex-1">
						<span class="font-medium text-slate-900">Petitions</span>
						<span class="text-sm text-slate-500 ml-2">
							{petitionStatus.file_count} files
							{#if petitionStatus.signature_count}• {petitionStatus.signature_count} signatures{/if}
						</span>
					</div>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Petitions</span>
				{/if}
			</div>

			<!-- Run Job Step -->
			<div class="flex items-center gap-3">
				{#if hasJobs}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<span class="font-medium text-slate-900">Run Job</span>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Run Job</span>
				{/if}
			</div>
		</div>

		{#if ctaConfig()}
			<div class="mt-4 pt-4 border-t border-slate-200">
				<Button variant="primary" text={ctaConfig()!.text} onclick={() => window.location.href = ctaConfig()!.href} />
			</div>
		{/if}
	</div>
{/if}
```

**Step 2: Export from index**

Modify `frontend-svelt/src/lib/components/dashboard/index.ts`:

```typescript
export { default as ProgressStepper } from './ProgressStepper.svelte';
```

**Step 3: Commit**

```bash
git add frontend-svelt/src/lib/components/dashboard/ProgressStepper.svelte frontend-svelt/src/lib/components/dashboard/index.ts
git commit -m "feat(frontend): add ProgressStepper component"
```

---

### Task 11: Integrate ProgressStepper into Dashboard

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/+page.svelte`

**Step 1: Update the dashboard page**

Modify `frontend-svelt/src/routes/workspace/[id]/+page.svelte`:

Add imports:
```svelte
<script lang="ts">
	// ... existing imports ...
	import { ProgressStepper } from '$lib/components/dashboard';
```

Add state for setup status:
```svelte
	interface SetupStatus {
		voter_list: { exists: boolean; row_count?: number; uploaded_at?: string; region_name?: string };
		petitions: { exists: boolean; file_count?: number; signature_count?: number };
		jobs: { total: number; active: number };
		state: string;
	}

	let setupStatus = $state<SetupStatus | null>(null);
	let loadingStatus = $state(true);

	async function fetchSetupStatus() {
		try {
			const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/setup-status`);
			if (response.ok) {
				setupStatus = await response.json();
			}
		} catch (error) {
			console.error('Failed to fetch setup status:', error);
		} finally {
			loadingStatus = false;
		}
	}
```

Update onMount:
```svelte
	onMount(() => {
		campaigns.fetchAll();
		jobs.fetchAll();
		fetchMetrics();
		fetchSetupStatus();

		pollInterval = setInterval(fetchMetrics, POLL_INTERVAL_MS);
	});
```

Add ProgressStepper to template (after the header, before metrics):
```svelte
		{#if !loadingStatus && setupStatus && !hasMatchResults}
			<ProgressStepper
				voterListStatus={setupStatus.voter_list}
				petitionStatus={setupStatus.petitions}
				hasJobs={setupStatus.jobs.total > 0}
				{campaignId}
			/>
		{/if}
```

**Step 2: Commit**

```bash
git add frontend-svelt/src/routes/workspace/[id]/+page.svelte
git commit -m "feat(frontend): integrate ProgressStepper into dashboard"
```

---

### Task 12: Add Voter List Display to Upload Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/upload/+page.svelte`

**Step 1: Add voter list status state**

Add to script:
```svelte
	interface VoterListStatus {
		exists: boolean;
		upload?: {
			id: string;
			original_filename: string;
			file_size: number;
			row_count: number;
			uploaded_at: string;
		};
	}

	let voterListStatus = $state<VoterListStatus | null>(null);
	let loadingVoterList = $state(false);
	let showVoterListDeleteConfirm = $state(false);

	async function fetchVoterListStatus() {
		if (!campaign?.region) return;
		loadingVoterList = true;
		try {
			const response = await fetch(`${API_BASE}/api/regions/${campaign.region_id}/voter-list`);
			if (response.ok) {
				voterListStatus = await response.json();
			}
		} catch (error) {
			console.error('Failed to fetch voter list status:', error);
		} finally {
			loadingVoterList = false;
		}
	}

	async function deleteVoterList() {
		if (!campaign?.region) return;
		try {
			const response = await fetch(`${API_BASE}/api/regions/${campaign.region_id}/voter-list`, {
				method: 'DELETE'
			});
			if (response.ok) {
				voterListStatus = { exists: false };
				messages = 'Voter list deleted successfully.';
				messageType = 'success';
			}
		} catch (error) {
			console.error('Failed to delete voter list:', error);
			messages = 'Failed to delete voter list.';
			messageType = 'error';
		} finally {
			showVoterListDeleteConfirm = false;
		}
	}

	onMount(() => {
		campaigns.fetchAll();
		fetchExistingScans();
		fetchVoterListStatus();
	});

	// Re-fetch when campaign changes
	$effect(() => {
		if (campaign) {
			fetchVoterListStatus();
		}
	});
```

**Step 2: Add voter list display to template**

Add to Voter List tab in the template:
```svelte
		{:else if activeTab === 'voters'}
			<div class="space-y-6">
				<!-- Existing Voter List -->
				{#if loadingVoterList}
					<div class="text-center py-8 text-slate-500">Loading...</div>
				{:else if voterListStatus?.exists && voterListStatus.upload}
					<div class="rounded-lg border border-slate-200 bg-white">
						<div class="p-4 border-b border-slate-200">
							<h3 class="font-medium text-slate-900">Current Voter List</h3>
						</div>
						<div class="p-4">
							<div class="flex items-center justify-between">
								<div>
									<p class="font-medium text-slate-900">{voterListStatus.upload.original_filename}</p>
									<p class="text-sm text-slate-500 mt-1">
										{voterListStatus.upload.row_count.toLocaleString()} voters
										• {formatFileSize(voterListStatus.upload.file_size)}
										• Uploaded {formatDate(voterListStatus.upload.uploaded_at)}
									</p>
								</div>
								<Button
									variant="secondary"
									text="Delete"
									onclick={() => showVoterListDeleteConfirm = true}
								/>
							</div>
						</div>
					</div>
				{/if}

				<!-- Upload Form -->
				<!-- ... existing upload form ... -->
			</div>
```

**Step 3: Add delete confirmation dialog**

Add after the duplicate dialog:
```svelte
	<!-- Voter List Delete Confirmation -->
	{#if showVoterListDeleteConfirm}
		<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
				<h3 class="text-lg font-semibold text-slate-900 mb-2">Delete Voter List?</h3>
				<p class="text-slate-600 mb-4">
					This will permanently delete all {voterListStatus?.upload?.row_count?.toLocaleString() || 'registered'} voters for this region.
					This action cannot be undone.
				</p>
				<div class="flex gap-3 justify-end">
					<Button variant="secondary" text="Cancel" onclick={() => showVoterListDeleteConfirm = false} />
					<Button variant="primary" text="Delete" onclick={deleteVoterList} />
				</div>
			</div>
		</div>
	{/if}
```

**Step 4: Commit**

```bash
git add frontend-svelt/src/routes/workspace/[id]/upload/+page.svelte
git commit -m "feat(frontend): add voter list display to upload page"
```

---

## Phase 5: Testing & Polish

### Task 13: Run Full Test Suite

**Step 1: Run backend tests**

Run: `cd backend && uv run pytest -v`
Expected: All tests pass

**Step 2: Run frontend build**

Run: `cd frontend-svelt && npm run build`
Expected: Build succeeds

**Step 3: Run E2E tests**

Run: `cd frontend-svelt && npm run test:e2e`
Expected: Tests pass

**Step 4: Fix any failures**

If any tests fail, investigate and fix before proceeding.

---

### Task 14: Update Documentation

**Files:**
- Modify: `openspec/SPEC.md`
- Modify: `.agent-workspace/problem/PROGRESS.md`
- Modify: `openspec/ISSUES-AND-CHANGES.md`

**Step 1: Update SPEC.md**

Add Phase 13 to the specification:
- Mark Issue #5 and #10 as addressed
- Update route structure with new endpoints

**Step 2: Update PROGRESS.md**

Add Phase 13 section with completion status.

**Step 3: Update ISSUES-AND-CHANGES.md**

Mark Issues #5 and #10 as fixed with resolution notes.

**Step 4: Commit**

```bash
git add openspec/SPEC.md .agent-workspace/problem/PROGRESS.md openspec/ISSUES-AND-CHANGES.md
git commit -m "docs: update documentation for Phase 13 completion"
```

---

## Summary

| Phase | Tasks | Est. Hours |
|-------|-------|------------|
| Phase 1: Database Models | 4 | 4 |
| Phase 2: Backend Services | 2 | 6 |
| Phase 3: API Endpoints | 3 | 4 |
| Phase 4: Frontend Components | 3 | 5 |
| Phase 5: Testing & Polish | 2 | 4 |
| **Total** | **14** | **23** |

---

## Dependencies

- Phase 2 depends on Phase 1
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 3
- Phase 5 depends on all previous phases

---

## Rollback Plan

If issues arise:
1. Each task is a single commit - can revert individually
2. Database migration has downgrade path
3. Frontend changes are additive - can be removed without breaking existing functionality
