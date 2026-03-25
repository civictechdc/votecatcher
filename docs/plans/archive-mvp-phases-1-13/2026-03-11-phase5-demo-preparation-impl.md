# Phase 5 Part E: Demo Preparation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement real pre-baked session loading with minimal synthetic data for fast demo resets.

**Architecture:** Create a `DemoDataService` that populates the database with a complete demo workflow: region → campaign → voters → petition → crops → OCR results → match results. Reset clears all related tables.

**Tech Stack:** Python 3.12, SQLModel, FastAPI, structlog

---

## Overview

Currently `demo_router.py` has stub implementations. We need to:
1. Create `DemoDataService` with methods for loading/resetting demo data
2. Wire it into the router endpoints
3. Add tests for the full flow

**Minimal Demo Data (10 entries):**
- 1 Region (DC)
- 1 Campaign (DC Demo 2024)
- 10 synthetic voters
- 1 PetitionScan (no actual PDF needed)
- 10 PetitionCrops (no actual images)
- 1 MatcherJob (MATCHING_COMPLETED)
- 1 OcrJob (OCR_COMPLETED)
- 10 OcrResults (synthetic extracted text)
- 50 MatchResults (top 5 per OCR result with confidence levels)

---

## Task 1: Create DemoDataService

**Files:**
- Create: `backend/app/demo/demo_service.py`
- Create: `backend/app/demo/__init__.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/demo/test_demo_service.py
"""Unit tests for DemoDataService."""

import pytest
from sqlmodel import Session, select

from app.demo.demo_service import DemoDataService
from app.data.database.model.schema import Region, Campaign
from app.data.database.model.jobs import MatcherJob, JobStatus


class TestDemoDataService:
    """Tests for demo data service."""

    def test_load_minimal_session_creates_region(self, session: Session):
        """Test that loading creates a region."""
        service = DemoDataService(session)
        service.load_minimal_session()

        regions = session.exec(select(Region)).all()
        assert len(regions) == 1
        assert regions[0].region_key == "dc"

    def test_load_minimal_session_creates_campaign(self, session: Session):
        """Test that loading creates a campaign."""
        service = DemoDataService(session)
        service.load_minimal_session()

        campaigns = session.exec(select(Campaign)).all()
        assert len(campaigns) == 1
        assert campaigns[0].title == "DC Demo 2024"

    def test_load_minimal_session_creates_voters(self, session: Session):
        """Test that loading creates 10 voters."""
        from app.data.database.model.registered_voter import RegisteredVoter

        service = DemoDataService(session)
        service.load_minimal_session()

        voters = session.exec(select(RegisteredVoter)).all()
        assert len(voters) == 10

    def test_load_minimal_session_creates_matcher_job(self, session: Session):
        """Test that loading creates a completed matcher job."""
        service = DemoDataService(session)
        service.load_minimal_session()

        jobs = session.exec(select(MatcherJob)).all()
        assert len(jobs) == 1
        assert jobs[0].current_status == JobStatus.MATCHING_COMPLETED

    def test_reset_clears_all_data(self, session: Session):
        """Test that reset clears all demo data."""
        service = DemoDataService(session)
        service.load_minimal_session()

        # Verify data exists
        assert len(session.exec(select(Region)).all()) == 1

        # Reset
        service.reset()

        # Verify data is cleared
        assert len(session.exec(select(Region)).all()) == 0
        assert len(session.exec(select(Campaign)).all()) == 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/unit/demo/test_demo_service.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'app.demo'"

**Step 3: Write implementation**

```python
# backend/app/demo/__init__.py
"""Demo mode package for pre-baked sessions and data reset."""

from app.demo.demo_service import DemoDataService

__all__ = ["DemoDataService"]
```

```python
# backend/app/demo/demo_service.py
"""Service for loading and resetting demo data."""

import structlog
from sqlmodel import Session, delete

from app.data.database.model.schema import Region, Campaign
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.match_result import MatchResult, ConfidenceLevel
from app.data.database.model.jobs import MatcherJob, OcrJob, JobStatus
from app.data.database.model.registered_voter import RegisteredVoter

logger = structlog.get_logger(__name__)

# Minimal synthetic voters for demo
DEMO_VOTERS = [
    {"first_name": "John", "last_name": "Smith", "zip_code": "20001", "address": "123 Main St NW"},
    {"first_name": "Maria", "last_name": "Garcia", "zip_code": "20002", "address": "456 Oak Ave NE"},
    {"first_name": "Robert", "last_name": "Johnson", "zip_code": "20003", "address": "789 Pine St SW"},
    {"first_name": "Sarah", "last_name": "Williams", "zip_code": "20004", "address": "321 Elm Blvd SE"},
    {"first_name": "David", "last_name": "Brown", "zip_code": "20005", "address": "654 Cedar Ln NW"},
    {"first_name": "Jennifer", "last_name": "Davis", "zip_code": "20006", "address": "987 Maple Dr NE"},
    {"first_name": "Michael", "last_name": "Miller", "zip_code": "20007", "address": "147 Birch Ave SW"},
    {"first_name": "Lisa", "last_name": "Wilson", "zip_code": "20008", "address": "258 Walnut Way SE"},
    {"first_name": "James", "last_name": "Taylor", "zip_code": "20009", "address": "369 Cherry Ct NW"},
    {"first_name": "Emily", "last_name": "Anderson", "zip_code": "20010", "address": "741 Spruce Pl NE"},
]

# Simulated OCR results (matching voter names with slight variations)
DEMO_OCR_RESULTS = [
    {"extracted_name": "Jon Smith", "extracted_address": "123 Main St"},
    {"extracted_name": "Maria Garca", "extracted_address": "456 Oak Ave"},
    {"extracted_name": "Rob Johnson", "extracted_address": "789 Pine St"},
    {"extracted_name": "S. Williams", "extracted_address": "321 Elm Blvd"},
    {"extracted_name": "Dave Brown", "extracted_address": "654 Cedar Ln"},
    {"extracted_name": "J. Davis", "extracted_address": "987 Maple Dr"},
    {"extracted_name": "Mike Miller", "extracted_address": "147 Birch Ave"},
    {"extracted_name": "L Wilson", "extracted_address": "258 Walnut Way"},
    {"extracted_name": "Jms Taylor", "extracted_address": "369 Cherry Ct"},
    {"extracted_name": "E Anderson", "extracted_address": "741 Spruce Pl"},
]


class DemoDataService:
    """Service for loading and resetting demo data."""

    def __init__(self, session: Session):
        self.session = session

    def load_minimal_session(self) -> dict:
        """Load minimal demo session with 10 entries."""
        logger.info("Loading minimal demo session")

        # 1. Create Region
        region = Region(
            region_key="dc",
            region_name="Washington, DC",
            country_code="US",
        )
        self.session.add(region)
        self.session.flush()

        # 2. Create Campaign
        campaign = Campaign(
            unique_name="dc-demo-2024",
            title="DC Demo 2024",
            description="Minimal demo session with 10 entries",
            year="2024",
            region_id=region.id,
        )
        self.session.add(campaign)
        self.session.flush()

        # 3. Create Voters
        voters = []
        for i, voter_data in enumerate(DEMO_VOTERS):
            voter = RegisteredVoter(
                first_name=voter_data["first_name"],
                last_name=voter_data["last_name"],
                zip_code=voter_data["zip_code"],
                address=voter_data["address"],
                region_id=region.id,
            )
            self.session.add(voter)
            voters.append(voter)
        self.session.flush()

        # 4. Create PetitionScan
        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="demo_petition.pdf",
            stored_path=f"/data/campaigns/{campaign.id}/petitions/demo_petition.pdf",
            file_hash="demo_hash_" + str(campaign.id),
            page_count=1,
        )
        self.session.add(scan)
        self.session.flush()

        # 5. Create PetitionCrops
        crops = []
        for i in range(10):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/data/campaigns/{campaign.id}/crops/crop_{i}.png",
                crop_coordinates={"top": i * 0.1, "bottom": (i + 1) * 0.1},
                page_number=1,
            )
            self.session.add(crop)
            crops.append(crop)
        self.session.flush()

        # 6. Create MatcherJob
        matcher_job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
        )
        self.session.add(matcher_job)
        self.session.flush()

        # 7. Create OcrJob
        ocr_job = OcrJob(
            matcher_job_id=matcher_job.id,
            status=JobStatus.OCR_COMPLETED,
        )
        self.session.add(ocr_job)
        self.session.flush()

        # 8. Create OcrResults and MatchResults
        for i, (crop, ocr_data) in enumerate(zip(crops, DEMO_OCR_RESULTS)):
            ocr_result = OcrResult(
                crop_id=crop.id,
                ocr_job_id=ocr_job.id,
                extracted_text={
                    "name": ocr_data["extracted_name"],
                    "address": ocr_data["extracted_address"],
                },
                confidence_score=0.85,
            )
            self.session.add(ocr_result)
            self.session.flush()

            # Create top 5 match results per OCR result
            for rank, voter in enumerate(voters[:5], start=1):
                # First match is the correct one (high confidence)
                if rank == 1:
                    confidence = ConfidenceLevel.HIGH
                    score = 0.92
                elif rank == 2:
                    confidence = ConfidenceLevel.MEDIUM
                    score = 0.75
                else:
                    confidence = ConfidenceLevel.LOW
                    score = 0.50 - (rank * 0.05)

                match_result = MatchResult(
                    ocr_result_id=ocr_result.id,
                    matcher_job_id=matcher_job.id,
                    rank=rank,
                    voter_id=voter.id if rank <= len(voters) else None,
                    similarity_score=score,
                    confidence_level=confidence,
                    field_scores={"name": score, "address": score - 0.1},
                )
                self.session.add(match_result)

        self.session.commit()
        logger.info("Demo session loaded successfully")

        return {
            "success": True,
            "campaign_id": str(campaign.id),
            "voters_count": 10,
            "crops_count": 10,
            "match_results_count": 50,
        }

    def reset(self) -> None:
        """Reset all demo data."""
        logger.info("Resetting demo data")

        # Delete in reverse dependency order
        self.session.exec(delete(MatchResult))
        self.session.exec(delete(OcrResult))
        self.session.exec(delete(OcrJob))
        self.session.exec(delete(MatcherJob))
        self.session.exec(delete(PetitionCrop))
        self.session.exec(delete(PetitionScan))
        self.session.exec(delete(RegisteredVoter))
        self.session.exec(delete(Campaign))
        self.session.exec(delete(Region))

        self.session.commit()
        logger.info("Demo data reset complete")
```

**Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/unit/demo/test_demo_service.py -v
```
Expected: 5 passed

**Step 5: Commit**

```bash
git add backend/app/demo/ backend/tests/unit/demo/
git commit -m "feat(demo): add DemoDataService for pre-baked sessions"
```

---

## Task 2: Wire DemoDataService into Router

**Files:**
- Modify: `backend/app/routers/demo_router.py`
- Modify: `backend/tests/integration/api/test_demo.py`

**Step 1: Add integration test**

```python
# Add to backend/tests/integration/api/test_demo.py

class TestDemoDataLoading:
    """Tests for actual demo data loading."""

    def test_load_dc_petition_2024_creates_data(
        self, client: TestClient, session: Session, monkeypatch
    ):
        """Test that loading dc-petition-2024 creates all entities."""
        # Enable demo mode
        from app.settings.env_settings import AppSettings
        monkeypatch.setattr(
            AppSettings,
            "demo_mode",
            True,
        )

        response = client.post("/api/demo/sessions/dc-petition-2024/load")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "campaign_id" in data
        assert data["voters_count"] == 10
        assert data["match_results_count"] == 50

    def test_reset_clears_data(
        self, client: TestClient, session: Session, monkeypatch
    ):
        """Test that reset clears all demo data."""
        from app.settings.env_settings import AppSettings
        from sqlmodel import select
        from app.data.database.model.schema import Region

        # Enable demo mode and reset
        monkeypatch.setattr(AppSettings, "demo_mode", True)
        monkeypatch.setattr(AppSettings, "demo_reset", True)

        # Load data first
        client.post("/api/demo/sessions/dc-petition-2024/load")
        assert len(session.exec(select(Region)).all()) == 1

        # Reset
        response = client.post("/api/demo/reset")
        assert response.status_code == 204
        assert len(session.exec(select(Region)).all()) == 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/integration/api/test_demo.py -v
```
Expected: New tests fail with "success" not in response

**Step 3: Update router to use DemoDataService**

```python
# backend/app/routers/demo_router.py
"""Demo mode endpoints for reset and pre-baked session loading."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.dependencies import get_session
from app.demo.demo_service import DemoDataService
from app.settings.env_settings import AppSettings, get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class PrebakedSession(BaseModel):
    """Pre-baked demo session metadata."""

    id: str
    name: str
    description: str


class PrebakedSessionList(BaseModel):
    """List of pre-baked sessions."""

    sessions: list[PrebakedSession]


PREBAKED_SESSIONS = [
    PrebakedSession(
        id="dc-petition-2024",
        name="DC Petition Demo 2024",
        description="Minimal demo session with 10 entries",
    ),
]


def check_demo_mode(settings: AppSettings) -> None:
    """Check if demo mode is enabled."""
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode not enabled",
        )


def check_demo_reset(settings: AppSettings) -> None:
    """Check if demo mode and reset are enabled."""
    check_demo_mode(settings)
    if not settings.demo_reset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset not enabled",
        )


@router.get("/sessions", response_model=PrebakedSessionList)
def list_prebaked_sessions(
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> PrebakedSessionList:
    """List available pre-baked demo sessions."""
    check_demo_mode(settings)
    return PrebakedSessionList(sessions=PREBAKED_SESSIONS)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_demo_data(
    db_session: Annotated[Session, Depends(get_session)],
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> None:
    """Reset all demo data to initial state."""
    check_demo_reset(settings)

    service = DemoDataService(db_session)
    service.reset()
    logger.info("Demo data reset complete")


@router.post("/sessions/{session_id}/load", status_code=status.HTTP_200_OK)
def load_prebaked_session(
    session_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> dict:
    """Load a pre-baked demo session."""
    check_demo_mode(settings)

    session_metadata = next(
        (s for s in PREBAKED_SESSIONS if s.id == session_id),
        None,
    )

    if not session_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pre-baked session '{session_id}' not found",
        )

    service = DemoDataService(db_session)
    result = service.load_minimal_session()

    logger.info(
        "Loaded pre-baked session",
        session_id=session_id,
        campaign_id=result.get("campaign_id"),
    )

    return {
        "success": True,
        "session_id": session_id,
        "message": f"Loaded demo session: {session_metadata.name}",
        **result,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/integration/api/test_demo.py -v
```
Expected: All tests pass (10+)

**Step 5: Commit**

```bash
git add backend/app/routers/demo_router.py backend/tests/integration/api/test_demo.py
git commit -m "feat(demo): wire DemoDataService into router endpoints"
```

---

## Task 3: Update Frontend Demo Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/demo/+page.svelte`

**Step 1: Check current demo page**

```bash
cat frontend-svelt/src/routes/workspace/demo/+page.svelte
```

**Step 2: Verify it shows loaded session info**

The demo page should already use the `demo` store. If it doesn't show the result details, update it to display:
- Campaign ID
- Voters count
- Match results count

**Step 3: Run E2E test**

```bash
cd frontend-svelt && bun run test:e2e tests/e2e/demo.spec.ts
```

**Step 4: Commit (if changes made)**

```bash
git add frontend-svelt/src/routes/workspace/demo/
git commit -m "feat(frontend): show demo session loading details"
```

---

## Task 4: E2E Demo Flow Test

**Files:**
- Create: `frontend-svelt/tests/e2e/demo-flow.spec.ts`

**Step 1: Write E2E test**

```typescript
// frontend-svelt/tests/e2e/demo-flow.spec.ts
import { expect, test } from '@playwright/test';

test.describe('Demo Flow', () => {
  test('complete demo workflow', async ({ page }) => {
    // Navigate to demo page
    await page.goto('/workspace/demo');

    // Load pre-baked session
    await page.click('button:has-text("Load DC Petition Demo")');

    // Wait for success
    await expect(page.locator('text=Loaded demo session')).toBeVisible({ timeout: 10000 });

    // Verify campaign was created
    await page.goto('/workspace/campaigns');
    await expect(page.locator('text=DC Demo 2024')).toBeVisible();

    // Verify results exist
    await page.goto('/workspace/results');
    await expect(page.locator('table')).toBeVisible();

    // Reset demo
    await page.goto('/workspace/demo');
    await page.click('button:has-text("Reset Demo")');
    await page.click('button:has-text("Confirm")');

    // Verify reset
    await page.goto('/workspace/campaigns');
    await expect(page.locator('text=DC Demo 2024')).not.toBeVisible();
  });
});
```

**Step 2: Run test**

```bash
cd frontend-svelt && bun run test:e2e tests/e2e/demo-flow.spec.ts
```

**Step 3: Commit**

```bash
git add frontend-svelt/tests/e2e/demo-flow.spec.ts
git commit -m "test(e2e): add demo flow E2E test"
```

---

## Task 5: Verification

**Step 1: Run full backend test suite**

```bash
cd backend && uv run pytest tests/ -v --ignore=tests/routers/test_ocr_simulate.py
```
Expected: 160+ tests passing

**Step 2: Run full frontend test suite**

```bash
cd frontend-svelt && bun run test
bun run test:e2e
```

**Step 3: Manual demo walkthrough**

1. Start backend: `cd backend && uv run fastapi dev`
2. Start frontend: `cd frontend-svelt && bun run dev`
3. Navigate to `http://localhost:5173/workspace/demo`
4. Click "Load DC Petition Demo 2024"
5. Verify campaign appears in /workspace/campaigns
6. Verify results appear in /workspace/results
7. Click "Reset Demo" and verify data cleared

---

## Sign-off Checklist

- [ ] DemoDataService creates all entities (region, campaign, voters, crops, jobs, results)
- [ ] Reset clears all data
- [ ] Router endpoints use DemoDataService
- [ ] Frontend demo page shows loading results
- [ ] E2E test covers full demo flow
- [ ] All existing tests still pass
- [ ] Manual demo walkthrough successful
