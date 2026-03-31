# Phase 2: Persistence Layer Refactor

> **Prerequisite:** Phase 1 complete (all tests pass, type check passes)

**Goal:** Create engine contracts, domain objects, and repositories to abstract database access from business logic.

**Duration Estimate:** 8-12 hours

---

## Phase Status

| Task Group | Status | Exit Gate |
|------------|--------|-----------|
| 2A: Engine Contracts | Complete | 4 tests pass |
| 2B: Engine Implementations | Complete | 9 tests pass |
| 2C: Domain Objects | Complete | 7 tests pass |
| 2D: Repositories | Complete | 4 tests pass |
| 2E: Session Management | Complete | 3 tests pass |

---

## Developer Notes

| Date | Status | Notes/Blockers/Concerns |
|------|--------|-------------------------|
| | Not Started | |

---

## Entrance Gate

Verify Phase 1 is complete:

```bash
cd backend && uv run pytest tests/unit/settings/ -v && uv run basedpyright app/settings/
```

**Expected:** All tests pass, no type errors

---

## Task Group 2A: Engine Contracts

**Files:**
- Create: `backend/app/data/persistence/__init__.py`
- Create: `backend/app/persistence/contracts.py`
- Create: `backend/tests/unit/persistence/test_contracts.py`

### Step 1: Write failing tests for engine contracts

```python
# backend/tests/unit/persistence/test_contracts.py
"""Tests for persistence contracts."""

import pytest


class TestProvidesEngine:
    """Tests for ProvidesEngine protocol."""

    def test_protocol_has_required_methods(self):
        """Protocol must define all required methods."""
        from app.persistence.contracts import ProvidesEngine

        attrs = ProvidesEngine.__protocol_attrs__
        assert "name" in attrs
        assert "connection_url" in attrs
        assert "create_session" in attrs
        assert "initialize" in attrs
        assert "health_check" in attrs


class TestProvidesRepositoryContracts:
    """Tests for repository protocol contracts."""

    def test_petition_repository_contract(self):
        """PetitionRepository must define required methods."""
        from app.persistence.contracts import PetitionRepository

        attrs = PetitionRepository.__protocol_attrs__
        assert "save" in attrs
        assert "find_by_id" in attrs
```

### Step 2: Run test to verify it fails

```bash
cd backend && uv run pytest tests/unit/persistence/test_contracts.py -v
```

**Expected:** FAIL - module not found

### Step 3: Implement contracts

```python
# backend/app/data/persistence/__init__.py
"""Persistence layer."""

from app.persistence.contracts import (
    ProvidesEngine,
    PetitionRepository,
    CampaignRepository,
    VoterRepository,
)

__all__ = [
    "ProvidesEngine",
    "PetitionRepository",
    "CampaignRepository",
    "VoterRepository",
]
```

```python
# backend/app/persistence/contracts.py
"""Persistence engine and repository contracts."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlmodel import Session


@runtime_checkable
class ProvidesEngine(Protocol):
    """Any database engine that can create sessions."""

    @property
    def name(self) -> str:
        """Human-readable name (sqlite, postgres, supabase)."""
        ...

    @property
    def connection_url(self) -> str:
        """Connection string (masked for logging)."""
        ...

    def create_session(self) -> Session:
        """Create a new database session."""
        ...

    def initialize(self) -> None:
        """Run migrations, create tables if needed."""
        ...

    def health_check(self) -> bool:
        """Verify database is reachable."""
        ...


@runtime_checkable
class PetitionRepository(Protocol):
    """Manages petition persistence."""

    def save(self, petition: "Petition") -> "Petition":
        """Save a petition."""
        ...

    def find_by_id(self, petition_id: UUID) -> "Petition | None":
        """Find petition by ID."""
        ...

    def find_by_campaign(self, campaign_id: UUID) -> list["Petition"]:
        """Find all petitions for a campaign."""
        ...


@runtime_checkable
class CampaignRepository(Protocol):
    """Manages campaign persistence."""

    def save(self, campaign: "Campaign") -> "Campaign":
        """Save a campaign."""
        ...

    def find_by_id(self, campaign_id: UUID) -> "Campaign | None":
        """Find campaign by ID."""
        ...

    def list_active(self) -> list["Campaign"]:
        """List all active campaigns."""
        ...


@runtime_checkable
class VoterRepository(Protocol):
    """Manages voter persistence."""

    def save(self, voter: "RegisteredVoter") -> "RegisteredVoter":
        """Save a voter record."""
        ...

    def find_by_id(self, voter_id: UUID) -> "RegisteredVoter | None":
        """Find voter by ID."""
        ...

    def find_by_campaign(self, campaign_id: UUID) -> list["RegisteredVoter"]:
        """Find all voters for a campaign."""
        ...
```

### Step 4: Run test to verify it passes

```bash
cd backend && uv run pytest tests/unit/persistence/test_contracts.py -v
```

**Expected:** PASS

### Step 5: Commit

```bash
git add backend/app/data/persistence/ backend/app/persistence/ backend/tests/unit/persistence/
git commit -m "feat(persistence): add engine and repository contracts"
```

---

## Task Group 2B: Engine Implementations

**Files:**
- Create: `backend/app/persistence/engines/__init__.py`
- Create: `backend/app/persistence/engines/base.py`
- Create: `backend/app/persistence/engines/sqlite.py`
- Create: `backend/app/persistence/engines/postgres.py`
- Create: `backend/app/persistence/engines/supabase.py`
- Create: `backend/tests/unit/persistence/test_engines.py`

### Step 1: Write failing tests for engines

```python
# backend/tests/unit/persistence/test_engines.py
"""Tests for persistence engines."""

import tempfile
from pathlib import Path

import pytest
from sqlmodel import Session


class TestSqliteEngine:
    """Tests for SQLite engine."""

    def test_creates_engine_with_name(self, tmp_path: Path):
        """Should create engine with correct name."""
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        assert engine.name == "sqlite"

    def test_creates_session(self, tmp_path: Path):
        """Should create valid session."""
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        session = engine.create_session()
        assert isinstance(session, Session)

    def test_health_check_returns_true(self, tmp_path: Path):
        """Health check should return True for accessible database."""
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        assert engine.health_check() is True

    def test_masks_connection_url(self, tmp_path: Path):
        """Should not expose full path in connection_url."""
        from app.persistence.engines.sqlite import SqliteEngine

        db_path = tmp_path / "test.db"
        engine = SqliteEngine(url=f"sqlite:///{db_path}")
        url = engine.connection_url
        # Should contain sqlite but not full path details
        assert "sqlite" in url.lower()


class TestSupabaseEngine:
    """Tests for Supabase engine."""

    def test_name_is_supabase(self):
        """Should have name 'supabase'."""
        from app.persistence.engines.supabase import SupabaseEngine

        engine = SupabaseEngine(
            project_url="https://test.supabase.co",
            service_key="test_key",  # pragma: allowlist secret
            database_url="postgresql://test",
        )
        assert engine.name == "supabase"

    def test_health_check_without_connection(self):
        """Health check should fail without real connection."""
        from app.persistence.engines.supabase import SupabaseEngine

        engine = SupabaseEngine(
            project_url="https://nonexistent.supabase.co",
            service_key="invalid",  # pragma: allowlist secret
            database_url="postgresql://invalid",
        )
        # Should return False for invalid connection
        assert engine.health_check() is False
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/persistence/test_engines.py -v
```

**Expected:** FAIL - modules not found

### Step 3: Implement base engine

```python
# backend/app/persistence/engines/base.py
"""Base engine implementation."""

from abc import abstractmethod

from sqlmodel import Session


class BaseEngine:
    """Abstract base class for database engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""
        ...

    @property
    @abstractmethod
    def connection_url(self) -> str:
        """Connection string (masked for logging)."""
        ...

    @abstractmethod
    def create_session(self) -> Session:
        """Create a new database session."""
        ...

    @abstractmethod
    def initialize(self) -> None:
        """Run migrations, create tables if needed."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify database is reachable."""
        ...
```

### Step 4: Implement SQLite engine

```python
# backend/app/persistence/engines/sqlite.py
"""SQLite database engine."""

import re
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine
import structlog

from app.persistence.engines.base import BaseEngine

logger = structlog.get_logger(__name__)


class SqliteEngine(BaseEngine):
    """SQLite database engine."""

    def __init__(self, url: str):
        self._url = url
        self._engine = create_engine(url, echo=False)

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def connection_url(self) -> str:
        # Mask the path for security
        return re.sub(r"sqlite:///.*", "sqlite:///****", self._url)

    def create_session(self) -> Session:
        return Session(self._engine)

    def initialize(self) -> None:
        """Create all tables."""
        self._import_models()
        SQLModel.metadata.create_all(self._engine)
        logger.info("SQLite database initialized")

    def health_check(self) -> bool:
        try:
            with self._engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("SQLite health check failed", error=str(e))
            return False

    def _import_models(self) -> None:
        """Import all models to register with SQLModel metadata."""
        from app.data.database.model.jobs import MatcherJob, OcrJob, OcrModel, OcrProvider  # noqa: F401
        from app.data.database.model.llm_provider_config import LlmProviderConfig  # noqa: F401
        from app.data.database.model.match_result import MatchResult  # noqa: F401
        from app.data.database.model.ocr_result import OcrResult  # noqa: F401
        from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
        from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
        from app.data.database.model.registered_voter import RegisteredVoter  # noqa: F401
        from app.data.database.model.schema import Campaign, Region  # noqa: F401
        from app.data.database.model.session import Session as SessionModel  # noqa: F401
        from app.data.database.model.user import User  # noqa: F401
```

### Step 5: Implement Supabase engine

```python
# backend/app/persistence/engines/supabase.py
"""Supabase database engine."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine
from supabase import create_client, Client
import structlog

from app.persistence.engines.base import BaseEngine

logger = structlog.get_logger(__name__)


class SupabaseEngine(BaseEngine):
    """Supabase database engine using PostgreSQL."""

    def __init__(self, project_url: str, service_key: str, database_url: str):
        self._project_url = project_url
        self._service_key = service_key
        self._database_url = database_url
        self._engine = create_engine(database_url, echo=False)
        self._client: Client | None = None

    @property
    def name(self) -> str:
        return "supabase"

    @property
    def connection_url(self) -> str:
        # Mask password in URL
        import re
        return re.sub(
            r"(postgresql://[^:]+:)[^@]+(@.*)",
            r"\1****\2",
            self._database_url,
        )

    @property
    def client(self) -> Client:
        """Get Supabase client for REST API operations."""
        if self._client is None:
            self._client = create_client(self._project_url, self._service_key)
        return self._client

    def create_session(self) -> Session:
        return Session(self._engine)

    def initialize(self) -> None:
        """Create all tables using Alembic migrations."""
        # For Supabase, we should use Alembic migrations
        # rather than create_all
        self._import_models()
        logger.info("Supabase database initialized")

    def health_check(self) -> bool:
        try:
            # Try to connect to Supabase REST API
            response = self.client.table("_health_check").select("*").limit(1).execute()
            return True
        except Exception:
            # Table might not exist, try raw query
            try:
                with self._engine.connect() as conn:
                    conn.execute("SELECT 1")
                return True
            except Exception as e:
                logger.error("Supabase health check failed", error=str(e))
                return False

    def _import_models(self) -> None:
        """Import all models to register with SQLModel metadata."""
        from app.data.database.model.jobs import MatcherJob, OcrJob, OcrModel, OcrProvider  # noqa: F401
        from app.data.database.model.llm_provider_config import LlmProviderConfig  # noqa: F401
        from app.data.database.model.match_result import MatchResult  # noqa: F401
        from app.data.database.model.ocr_result import OcrResult  # noqa: F401
        from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
        from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
        from app.data.database.model.registered_voter import RegisteredVoter  # noqa: F401
        from app.data.database.model.schema import Campaign, Region  # noqa: F401
        from app.data.database.model.session import Session as SessionModel  # noqa: F401
        from app.data.database.model.user import User  # noqa: F401
```

### Step 6: Create engines __init__.py

```python
# backend/app/persistence/engines/__init__.py
"""Database engine implementations."""

from app.persistence.engines.base import BaseEngine
from app.persistence.engines.sqlite import SqliteEngine
from app.persistence.engines.supabase import SupabaseEngine

__all__ = ["BaseEngine", "SqliteEngine", "SupabaseEngine"]
```

### Step 7: Run tests

```bash
cd backend && uv run pytest tests/unit/persistence/test_engines.py -v
```

**Expected:** PASS

### Step 8: Commit

```bash
git add backend/app/persistence/ backend/tests/unit/persistence/
git commit -m "feat(persistence): implement SQLite and Supabase engines"
```

---

## Task Group 2C: Domain Objects

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/petition.py`
- Create: `backend/app/domain/campaign.py`
- Create: `backend/app/domain/voter.py`
- Create: `backend/tests/unit/domain/test_domain.py`

### Step 1: Write failing tests for domain objects

```python
# backend/tests/unit/domain/test_domain.py
"""Tests for domain objects."""

import pytest
from uuid import UUID
from datetime import datetime


class TestCampaign:
    """Tests for Campaign domain object."""

    def test_create_campaign(self):
        """Should create campaign with required fields."""
        from app.domain.campaign import Campaign

        campaign = Campaign(
            name="Test Campaign",
            status="active",
        )
        assert campaign.name == "Test Campaign"
        assert campaign.status == "active"
        assert isinstance(campaign.id, UUID)

    def test_campaign_has_timestamps(self):
        """Campaign should have created_at timestamp."""
        from app.domain.campaign import Campaign

        campaign = Campaign(name="Test", status="active")
        assert campaign.created_at is not None
        assert isinstance(campaign.created_at, datetime)


class TestPetition:
    """Tests for Petition domain object."""

    def test_create_petition(self):
        """Should create petition with campaign reference."""
        from app.domain.petition import Petition

        petition = Petition(
            file_path="/path/to/file.pdf",
            campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
        )
        assert petition.file_path == "/path/to/file.pdf"
        assert petition.status == "pending"


class TestRegisteredVoter:
    """Tests for RegisteredVoter domain object."""

    def test_create_voter(self):
        """Should create voter with name fields."""
        from app.domain.voter import RegisteredVoter

        voter = RegisteredVoter(
            first_name="John",
            last_name="Doe",
            campaign_id=UUID("00000000-0000-0000-0000-000000000001"),
        )
        assert voter.first_name == "John"
        assert voter.last_name == "Doe"
        assert voter.full_name == "John Doe"
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/domain/test_domain.py -v
```

**Expected:** FAIL - modules not found

### Step 3: Implement domain objects

```python
# backend/app/domain/__init__.py
"""Domain objects for business logic."""

from app.domain.campaign import Campaign
from app.domain.petition import Petition
from app.domain.voter import RegisteredVoter

__all__ = ["Campaign", "Petition", "RegisteredVoter"]
```

```python
# backend/app/domain/campaign.py
"""Campaign domain object."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Campaign(BaseModel):
    """Campaign domain object for business logic."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if campaign is active."""
        return self.status == "active"
```

```python
# backend/app/domain/petition.py
"""Petition domain object."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Petition(BaseModel):
    """Petition domain object for business logic."""

    id: UUID = Field(default_factory=uuid4)
    file_path: str
    campaign_id: UUID
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_processed(self) -> bool:
        """Check if petition has been processed."""
        return self.status in ("completed", "failed")
```

```python
# backend/app/domain/voter.py
"""Registered voter domain object."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RegisteredVoter(BaseModel):
    """Registered voter domain object for business logic."""

    id: UUID = Field(default_factory=uuid4)
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    campaign_id: UUID
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)
```

### Step 4: Run tests

```bash
cd backend && uv run pytest tests/unit/domain/test_domain.py -v
```

**Expected:** PASS

### Step 5: Commit

```bash
git add backend/app/domain/ backend/tests/unit/domain/
git commit -m "feat(domain): add Campaign, Petition, RegisteredVoter domain objects"
```

---

## Task Group 2D: Repositories

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/petition_repo.py`
- Create: `backend/app/repositories/campaign_repo.py`
- Create: `backend/app/repositories/voter_repo.py`
- Create: `backend/tests/unit/repositories/test_repositories.py`

### Step 1: Write failing tests for repositories

```python
# backend/tests/unit/repositories/test_repositories.py
"""Tests for repository implementations."""

import tempfile
from pathlib import Path
from uuid import UUID

import pytest


class TestSqliteCampaignRepository:
    """Tests for Campaign repository with SQLite."""

    @pytest.fixture
    def repo(self, tmp_path: Path):
        """Create repository with SQLite engine."""
        from app.persistence.engines.sqlite import SqliteEngine
        from app.repositories.campaign_repo import CampaignRepository

        engine = SqliteEngine(url=f"sqlite:///{tmp_path}/test.db")
        engine.initialize()
        return CampaignRepository(engine)

    def test_save_campaign(self, repo):
        """Should save and retrieve campaign."""
        from app.domain.campaign import Campaign

        campaign = Campaign(name="Test Campaign", status="active")
        saved = repo.save(campaign)

        assert saved.id == campaign.id
        assert saved.name == "Test Campaign"

    def test_find_by_id(self, repo):
        """Should find campaign by ID."""
        from app.domain.campaign import Campaign

        campaign = Campaign(name="Test", status="active")
        repo.save(campaign)

        found = repo.find_by_id(campaign.id)
        assert found is not None
        assert found.name == "Test"

    def test_find_by_id_returns_none_for_missing(self, repo):
        """Should return None for missing campaign."""
        result = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000999"))
        assert result is None
```

### Step 2: Run tests to verify they fail

```bash
cd backend && uv run pytest tests/unit/repositories/test_repositories.py -v
```

**Expected:** FAIL - modules not found

### Step 3: Implement repositories

```python
# backend/app/repositories/__init__.py
"""Repository implementations."""

from app.repositories.campaign_repo import CampaignRepository
from app.repositories.petition_repo import PetitionRepository
from app.repositories.voter_repo import VoterRepository

__all__ = ["CampaignRepository", "PetitionRepository", "VoterRepository"]
```

```python
# backend/app/repositories/campaign_repo.py
"""Campaign repository implementation."""

from uuid import UUID

from sqlmodel import Session, select
import structlog

from app.domain.campaign import Campaign
from app.data.database.model.schema import Campaign as CampaignModel

logger = structlog.get_logger(__name__)


class CampaignRepository:
    """Repository for Campaign persistence."""

    def __init__(self, engine):
        self._engine = engine

    def save(self, campaign: Campaign) -> Campaign:
        """Save campaign to database."""
        with self._engine.create_session() as session:
            model = CampaignModel(
                id=campaign.id,
                name=campaign.name,
                status=campaign.status,
                created_at=campaign.created_at,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return Campaign(
                id=model.id,
                name=model.name,
                status=model.status,
                created_at=model.created_at,
            )

    def find_by_id(self, campaign_id: UUID) -> Campaign | None:
        """Find campaign by ID."""
        with self._engine.create_session() as session:
            statement = select(CampaignModel).where(CampaignModel.id == campaign_id)
            model = session.exec(statement).first()
            if model is None:
                return None
            return Campaign(
                id=model.id,
                name=model.name,
                status=model.status,
                created_at=model.created_at,
            )

    def list_active(self) -> list[Campaign]:
        """List all active campaigns."""
        with self._engine.create_session() as session:
            statement = select(CampaignModel).where(CampaignModel.status == "active")
            models = session.exec(statement).all()
            return [
                Campaign(
                    id=m.id,
                    name=m.name,
                    status=m.status,
                    created_at=m.created_at,
                )
                for m in models
            ]
```

```python
# backend/app/repositories/petition_repo.py
"""Petition repository implementation."""

from uuid import UUID

from sqlmodel import Session, select

from app.domain.petition import Petition
from app.data.database.model.petition_scan import PetitionScan


class PetitionRepository:
    """Repository for Petition persistence."""

    def __init__(self, engine):
        self._engine = engine

    def save(self, petition: Petition) -> Petition:
        """Save petition to database."""
        with self._engine.create_session() as session:
            model = PetitionScan(
                id=petition.id,
                file_path=petition.file_path,
                campaign_id=petition.campaign_id,
                status=petition.status,
                created_at=petition.created_at,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return Petition(
                id=model.id,
                file_path=model.file_path,
                campaign_id=model.campaign_id,
                status=model.status,
                created_at=model.created_at,
            )

    def find_by_id(self, petition_id: UUID) -> Petition | None:
        """Find petition by ID."""
        with self._engine.create_session() as session:
            statement = select(PetitionScan).where(PetitionScan.id == petition_id)
            model = session.exec(statement).first()
            if model is None:
                return None
            return Petition(
                id=model.id,
                file_path=model.file_path,
                campaign_id=model.campaign_id,
                status=model.status,
                created_at=model.created_at,
            )

    def find_by_campaign(self, campaign_id: UUID) -> list[Petition]:
        """Find all petitions for a campaign."""
        with self._engine.create_session() as session:
            statement = select(PetitionScan).where(PetitionScan.campaign_id == campaign_id)
            models = session.exec(statement).all()
            return [
                Petition(
                    id=m.id,
                    file_path=m.file_path,
                    campaign_id=m.campaign_id,
                    status=m.status,
                    created_at=m.created_at,
                )
                for m in models
            ]
```

```python
# backend/app/repositories/voter_repo.py
"""Voter repository implementation."""

from uuid import UUID

from sqlmodel import Session, select

from app.domain.voter import RegisteredVoter
from app.data.database.model.registered_voter import RegisteredVoter as VoterModel


class VoterRepository:
    """Repository for RegisteredVoter persistence."""

    def __init__(self, engine):
        self._engine = engine

    def save(self, voter: RegisteredVoter) -> RegisteredVoter:
        """Save voter to database."""
        with self._engine.create_session() as session:
            model = VoterModel(
                id=voter.id,
                first_name=voter.first_name,
                last_name=voter.last_name,
                middle_name=voter.middle_name,
                campaign_id=voter.campaign_id,
                address=voter.address,
                city=voter.city,
                state=voter.state,
                zip_code=voter.zip_code,
                created_at=voter.created_at,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return RegisteredVoter(
                id=model.id,
                first_name=model.first_name,
                last_name=model.last_name,
                middle_name=model.middle_name,
                campaign_id=model.campaign_id,
                address=model.address,
                city=model.city,
                state=model.state,
                zip_code=model.zip_code,
                created_at=model.created_at,
            )

    def find_by_id(self, voter_id: UUID) -> RegisteredVoter | None:
        """Find voter by ID."""
        with self._engine.create_session() as session:
            statement = select(VoterModel).where(VoterModel.id == voter_id)
            model = session.exec(statement).first()
            if model is None:
                return None
            return RegisteredVoter(
                id=model.id,
                first_name=model.first_name,
                last_name=model.last_name,
                middle_name=model.middle_name,
                campaign_id=model.campaign_id,
                address=model.address,
                city=model.city,
                state=model.state,
                zip_code=model.zip_code,
                created_at=model.created_at,
            )

    def find_by_campaign(self, campaign_id: UUID) -> list[RegisteredVoter]:
        """Find all voters for a campaign."""
        with self._engine.create_session() as session:
            statement = select(VoterModel).where(VoterModel.campaign_id == campaign_id)
            models = session.exec(statement).all()
            return [
                RegisteredVoter(
                    id=m.id,
                    first_name=m.first_name,
                    last_name=m.last_name,
                    middle_name=m.middle_name,
                    campaign_id=m.campaign_id,
                    address=m.address,
                    city=m.city,
                    state=m.state,
                    zip_code=m.zip_code,
                    created_at=m.created_at,
                )
                for m in models
            ]
```

### Step 4: Run tests

```bash
cd backend && uv run pytest tests/unit/repositories/test_repositories.py -v
```

**Expected:** PASS (may need model field adjustments)

### Step 5: Commit

```bash
git add backend/app/repositories/ backend/tests/unit/repositories/
git commit -m "feat(repositories): implement Campaign, Petition, Voter repositories"
```

---

## Task Group 2E: Session Management Integration

**Files:**
- Modify: `backend/app/data/database/session.py`
- Create: `backend/tests/integration/test_engine_selection.py`

### Step 1: Write test for engine selection

```python
# backend/tests/integration/test_engine_selection.py
"""Tests for engine selection based on configuration."""

import pytest


class TestEngineSelection:
    """Tests for get_engine function."""

    def test_returns_sqlite_by_default(self, monkeypatch):
        """Should return SQLite engine when no Supabase configured."""
        from app.persistence.session import get_engine
        from app.persistence.engines.sqlite import SqliteEngine

        # Clear any cached settings
        from app.settings import get_settings
        get_settings.cache_clear()

        # Ensure no Supabase config
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
        monkeypatch.delenv("SUPABASE_URL", raising=False)

        engine = get_engine()
        assert isinstance(engine, SqliteEngine)
        assert engine.name == "sqlite"

    def test_returns_supabase_when_configured(self, monkeypatch):
        """Should return Supabase engine when configured."""
        from app.persistence.session import get_engine
        from app.persistence.engines.supabase import SupabaseEngine

        # Clear any cached settings
        from app.settings import get_settings
        get_settings.cache_clear()

        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test_key")  # pragma: allowlist secret
        monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test_password")  # pragma: allowlist secret

        engine = get_engine()
        assert isinstance(engine, SupabaseEngine)
        assert engine.name == "supabase"
```

### Step 2: Run test to verify it fails

```bash
cd backend && uv run pytest tests/integration/test_engine_selection.py -v
```

**Expected:** FAIL - module not found

### Step 3: Implement session management

```python
# backend/app/persistence/session.py
"""Session management with engine selection."""

from functools import lru_cache

from app.settings import get_settings
from app.persistence.engines.sqlite import SqliteEngine
from app.persistence.engines.supabase import SupabaseEngine
import structlog

logger = structlog.get_logger(__name__)


@lru_cache
def get_engine():
    """Select engine based on configuration."""
    settings = get_settings()

    if settings.supabase.is_connected:
        logger.info("Using Supabase engine", project=settings.supabase.url)
        return SupabaseEngine(
            project_url=settings.supabase.url,
            service_key=settings.supabase.service_key.get_secret_value(),
            database_url=settings.supabase.database_url,
        )

    logger.info("Using SQLite/PostgreSQL engine", type=settings.database.type)
    return SqliteEngine(url=settings.database.url)


def get_db_session():
    """Get database session for dependency injection."""
    engine = get_engine()
    yield engine.create_session()
```

### Step 4: Update existing session.py to use new system

```python
# backend/app/data/database/session.py
"""Database session management - backwards compatible."""

from collections.abc import Generator

from sqlmodel import Session

# Import from new location
from app.persistence.session import get_engine, get_db_session as _get_db_session


def init_db() -> None:
    """Initialize database and create all tables."""
    engine = get_engine()
    engine.initialize()


def get_db_session() -> Generator[Session]:
    """Get database session for dependency injection."""
    yield from _get_db_session()
```

### Step 5: Run tests

```bash
cd backend && uv run pytest tests/integration/test_engine_selection.py -v
```

**Expected:** PASS

### Step 6: Run full test suite to verify no regressions

```bash
cd backend && uv run pytest tests/ -v --tb=short
```

**Expected:** All tests pass

### Step 7: Commit

```bash
git add backend/app/data/database/session.py backend/app/persistence/session.py backend/tests/integration/test_engine_selection.py
git commit -m "feat(persistence): integrate engine selection with session management"
```

---

## Phase 2 Exit Gate

**Run all validation:**

```bash
# Unit tests
cd backend && uv run pytest tests/unit/persistence/ tests/unit/domain/ tests/unit/repositories/ -v

# Integration tests
cd backend && uv run pytest tests/integration/test_engine_selection.py -v

# Type checking
cd backend && uv run basedpyright app/persistence/ app/domain/ app/repositories/

# Linting
cd backend && uv run ruff check app/persistence/ app/domain/ app/repositories/
```

**Expected Results:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No type errors
- [ ] No lint errors

---

## Reviewer Section

**Reviewer:** Code Reviewer

**Date:** 2026-03-27

**Status:** [x] Approved [ ] Needs Changes

### Findings

| ID | Severity | File | Issue | Action | Resolution |
|----|----------|------|-------|--------|------------|
| R1 | 🔴 Critical | `app/repositories/voter_repo.py:21` | Indentation error causes syntax error | Fix indentation inside `with` block | ✅ Fixed — stray `)` removed, full class implemented |
| R2 | 🔴 Critical | `app/persistence/session.py:25` | Service key extracted to plaintext via `get_secret_value()` | Pass `SecretStr` directly to `SupabaseEngine` | ✅ Already fixed — `SupabaseEngine` accepts `SecretStr`, only calls `get_secret_value()` internally when creating client |
| R3 | 🔴 Critical | `app/persistence/contracts.py:32,43,54` | Missing forward references — protocol uses `Petition`, `Campaign`, `RegisteredVoter` without import or string annotations | Add `TYPE_CHECKING` imports or string annotations | ✅ Already fixed — `from __future__ import annotations` + `TYPE_CHECKING` block with domain imports |
| R4 | 🔴 Critical | `app/repositories/voter_repo.py:19` | Session context manager body not indented — resource leak | Indent all session operations inside `with` block | ✅ Fixed — voter_repo fully reimplemented with proper `with` blocks |
| R5 | 🟠 High | `app/domain/*.py` | Domain objects deviate from plan spec (e.g. missing `status`, different field names like `unique_name`, `region_id`) | Align domain objects with plan or update plan to match reality | ✅ Resolved — domain objects correctly match actual DB schema (`unique_name`, `title`, `year`, `region_id` for Campaign; `name_data`/`address_data` dicts for Voter). Plan spec was stale; implementation is canonical. |
| R6 | 🟠 High | `app/repositories/campaign_repo.py:63` | `list_active()` returns all rows — no `WHERE status = 'active'` filter | Add filter clause or rename to `list_all()` | ✅ Already fixed — `list_active()` filters by `CampaignModel.year == current_year`, plus `list_all()` added separately |
| R7 | 🟠 High | `app/repositories/voter_repo.py:59` | `find_by_campaign()` queries `region_id` column instead of `campaign_id` | Fix column reference or add `campaign_id` to model | ✅ Resolved — VoterRepository uses `find_by_region(region_id)` matching the actual `RegisteredVoter.region_id` FK. Contract updated accordingly. |
| R8 | 🟠 High | `app/persistence/session.py:22` | Logs Supabase project URL (information disclosure) | Mask or remove project URL from log output | ✅ Already fixed — `_mask_url()` helper masks project ref to first 3 chars + `***` |
| R9 | 🟠 High | `app/repositories/*.py` | `__init__(self, engine)` missing `ProvidesEngine` type hint — defeats purpose of protocol | Add `engine: ProvidesEngine` type annotation | ✅ Fixed — all repos have `ProvidesEngine` type hint via `TYPE_CHECKING` + `from __future__ import annotations` |
| R10 | 🟡 Medium | `app/persistence/engines/sqlite.py:36` | Bare `except Exception` swallows serious errors (disk full, permissions) | Catch specific exceptions (`OperationalError`, `ProgrammingError`) | ✅ Already fixed — catches `OperationalError` first, with generic fallback only for unexpected errors |
| R11 | 🟡 Medium | `app/repositories/*.py` | Extensive model-to-domain conversion duplication across all repos | Extract to base repository class or generic helper | ✅ Partially addressed — `_to_domain()` helper extracted per-repo. Full generic base class deferred to future refactor. |
| R12 | 🟡 Medium | `tests/unit/repositories/` | Missing `PetitionRepository` and `VoterRepository` tests | Implement comprehensive tests for all repositories | ✅ Already fixed — comprehensive tests for all 3 repos in `test_repositories.py` |
| R13 | 🟡 Medium | `app/domain/*.py` | Domain objects missing business logic methods (`is_active()`, `is_processed()`) specified in plan | Implement per plan spec | ✅ Already fixed — `Campaign.is_active()`, `Petition.is_processed()`, `RegisteredVoter.is_matchable()` + `full_name` property |
| R14 | 🟢 Low | `app/persistence/session.py:4` | Unused import `collections.abc.Generator` | Remove | ✅ Not applicable — `Generator` IS used in `get_db_session()` return type annotation |
| N1 | 🟡 Medium | `app/data/database/model/registered_voter.py:15` | `id: int = Field(primary_key=True)` missing `default=None` — forced `# pyright: ignore` in voter_repo | Change to `id: int \| None = Field(default=None, primary_key=True)` | ✅ Fixed — annotation corrected, `pyright: ignore` removed |

### Exit Gate Results (2026-03-27)

```
49 tests passed, 0 errors, 24 warnings (all 3rd-party deprecation warnings)
0 type errors, 74 warnings (existing structlog/SQLModel pattern warnings)
Lint: All checks passed
```

### Second Review Findings (2026-03-27)

| ID | Severity | File | Issue | Action | Resolution |
|----|----------|------|-------|--------|------------|
| N1 | 🟡 Medium | `app/data/database/model/registered_voter.py:15` | `id: int = Field(primary_key=True)` missing `default=None` — caused `# pyright: ignore[reportCallIssue]` in voter_repo | Fix to `id: int \| None = Field(default=None, primary_key=True)` to match `PetitionScan` pattern | ✅ Fixed — annotation corrected, `pyright: ignore` removed from voter_repo |
| N2 | 🟡 Medium | `app/persistence/engines/supabase.py:65-67` | `SupabaseEngine.initialize()` is a no-op — should verify Alembic migrations are applied or warn that manual migration is required | Add Alembic migration check or explicit warning log | ➡️ Deferred to Phase 4 |
| N3 | 🟡 Medium | `app/persistence/session.py:48-49` | `get_db_session()` generator lacks try/finally — session won't close if exception occurs after yield | Wrap in try/finally for exception safety | ➡️ Deferred to Phase 4 |
| N4 | 🟢 Low | `app/persistence/engines/sqlite.py:58` | Hardcoded table list (`voter_list_uploads`) should derive from `SQLModel.metadata` | Extract to constant or derive programmatically | ➡️ Deferred to Phase 4 |
| N5 | 🟢 Low | `app/repositories/campaign_repo.py:73` | `list_all()` method not in `CampaignRepository` protocol — inconsistent interface | Add to protocol or document as CampaignRepository-specific | ➡️ Deferred to Phase 4 |
| N6 | 🟢 Low | `app/persistence/engines/supabase.py:31-32` | `_engine` typed as `Engine` but initialized as `None` — potential `AttributeError` before init | Add `assert _engine is not None` or type as `Engine \| None` | ➡️ Deferred to Phase 4 |
| N7 | 🟢 Low | `app/domain/*.py` | Domain objects are mutable — accidental modification could cause subtle bugs | Consider `frozen=True` or document mutability as intentional | ➡️ Deferred to Phase 4 |

### Remaining suggestions (non-blocking)

- Extract a generic `BaseRepository[Domain, Model]` to eliminate remaining per-repo `_to_domain` duplication (R11 follow-up)
- Add integration tests that exercise the full engine → repository → domain round-trip

### Feedback by Task Group

| Task Group | Issues | Resolution |
|------------|--------|------------|
| 2A | R3: Protocol forward references missing | ✅ Fixed — `from __future__ import annotations` + `TYPE_CHECKING` block |
| 2B | R8: Project URL logged, R10: Broad exception handling | ✅ Fixed — `_mask_url()` helper; `OperationalError`/`DBAPIError` caught specifically |
| 2C | R5: Domain objects don't match plan, R13: Missing business logic methods | ✅ Resolved — domain objects match actual DB schema; `is_active()`, `is_processed()`, `is_matchable()` implemented |
| 2D | R1/R4: voter_repo broken, R6/R7: wrong queries, R9: missing type hints, R11: duplication, R12: missing tests | ✅ R1/R4/R9 fixed in voter_repo rewrite; R6/R7 already fixed; R11 deferred; R12 already fixed |
| 2E | R2: Service key in plaintext, R14: Unused import | ✅ Fixed — `SecretStr` passed directly; unused import removed |

### Decision on R5

**Resolved:** Domain objects correctly match the actual database schema. The plan spec was stale; implementation is canonical. The `Campaign` uses `unique_name`/`title`/`year`/`region_id`; `Petition` uses `campaign_id`/`original_filename`/`stored_path`/`file_hash`; `RegisteredVoter` uses `region_id`/`name_data`/`address_data` dicts — all matching the actual SQLModel table definitions.

### Decision on N1 (RegisteredVoter id type annotation)

**Root cause:** `RegisteredVoter.id` was declared as `id: int = Field(primary_key=True)` without `| None` or `default=None`. This made pyright believe `id` was a required constructor argument, forcing a `# pyright: ignore[reportCallIssue]` suppress in voter_repo. Not a runtime bug (SQLAlchemy auto-increments), but wrong type annotation. Fixed to `id: int | None = Field(default=None, primary_key=True)` matching the `PetitionScan` pattern.

### Blocking issues

All previously blocking issues resolved. See Findings table above for details.

### Suggestions deferred to Phase 4

- N2: Add Alembic migration check to `SupabaseEngine.initialize()`
- N3: Add try/finally to `get_db_session()` generator for exception safety
- N4: Derive SQLite table list from `SQLModel.metadata` instead of hardcoding
- N5: Add `list_all()` to `CampaignRepository` protocol
- N6: Add None-check guard to `SupabaseEngine._engine`
- N7: Consider `frozen=True` for domain objects
- R11 follow-up: Extract generic `BaseRepository[Domain, Model]` to eliminate `_to_domain` duplication
- Integration tests: Full engine → repository → domain round-trip

---

## Next Phase

Once this phase passes the exit gate and reviewer approval, proceed to:

**[Phase 3: Frontend Onboarding](./03-frontend-onboarding.md)** or **[Phase 4: Backend API & CLI](./04-backend-api-cli.md)**

Both can be developed in parallel after Phase 2.
