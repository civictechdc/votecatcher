# Voter List Tracking + Dashboard Progress Design

**Date:** 2026-03-18
**Status:** Approved
**Addresses:** Issue #5, Issue #10
**Phase:** 13 (Post-MVP Enhancement)

---

## Overview

This design addresses two related issues:

1. **Issue #5**: Voter List tab has no visibility into existing uploads
2. **Issue #10**: Dashboard missing "uploads ready, no job run" state

Both issues share a common data need: knowing the status of voter list uploads for a region.

---

## Goals

1. Display existing voter list uploads in the Upload page (similar to petitions)
2. Show contextual "next action" guidance on the dashboard based on campaign state
3. Track voter list history with merge/update semantics
4. Support region-specific CSV schema mapping

---

## Non-Goals

- Real-time SSE updates for voter list uploads (polling is sufficient)
- Multi-region voter list aggregation
- Voter data versioning beyond first/last seen tracking

---

## Design Decisions

### 1. Voter List Scope

**Decision:** Voter lists are region-scoped with explicit attribution

- Each region has one active voter list
- UI shows: "50,000 voters • DC • Updated Mar 15"
- Multiple campaigns in the same region share the same voter list

### 2. Upload Behavior

**Decision:** Merge/update semantics with first/last seen tracking

When a new voter list is uploaded:
- Existing voters: update info if changed, bump `last_seen_at`
- New voters: insert with `first_seen_at` and `last_seen_at`
- Previous upload marked as `superseded`

### 3. Voter Matching

**Decision:** Hash-based matching on normalized name + address

- Compute `data_hash` from normalized fields (lowercase, trimmed)
- Match existing voters by `data_hash` + `region_id`
- Region schema defines which fields to include in hash

### 4. Dashboard Progress UX

**Decision:** Hybrid progress stepper with contextual CTAs

Show what's done + what's next:
```
☑ Voter List     50,000 voters • DC • Updated Mar 15
☑ Petitions      3 files • 120 signatures
○ Run Job        Ready to process

[Create Job]  ← Primary CTA
```

### 5. Region Schemas

**Decision:** Database table with admin UI + file upload

- Each region can have a schema mapping CSV columns to canonical fields
- Admin UI at `/workspace/settings` → Region Schemas
- Upload YAML/JSON schema files

### 6. Delete Behavior

**Decision:** Hard delete with confirmation

- "This will permanently delete X voters from this region. Continue?"
- Deletes all voters for region + marks upload as superseded

---

## Data Model

### New Table: `voter_list_uploads`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `region_id` | UUID | FK to regions |
| `original_filename` | str | Source file name |
| `file_size` | int | Bytes |
| `row_count` | int | Voters imported |
| `status` | enum | `active`, `superseded` |
| `uploaded_at` | datetime | Upload timestamp |
| `superseded_at` | datetime | When replaced by new upload |
| `superseded_by` | UUID | FK to replacement upload |

### New Table: `region_schemas`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `region_id` | UUID | FK to regions (1:1) |
| `name` | str | Display name |
| `column_mappings` | JSON | `{"VoterID": "voter_id", "FirstName": "first_name", ...}` |
| `hash_fields` | JSON array | `["first_name", "last_name", "street", "zip"]` |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### Updated `registered_voter` Table

| New Column | Type | Description |
|------------|------|-------------|
| `data_hash` | str | Hash of normalized name+address for matching |
| `first_seen_at` | datetime | First upload containing this voter |
| `last_seen_at` | datetime | Most recent upload containing this voter |
| `first_upload_id` | UUID | FK to `voter_list_uploads` |
| `last_upload_id` | UUID | FK to `voter_list_uploads` |

---

## API Endpoints

### Voter List Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/regions/{id}/voter-list` | Current voter list status |
| GET | `/api/regions/{id}/voter-list/uploads` | Upload history |
| DELETE | `/api/regions/{id}/voter-list` | Delete all voters for region |
| POST | `/api/upload/voter-list` | Upload (updated to use schema + merge) |

### Region Schema Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/regions/{id}/schemas` | Get region schema |
| PUT | `/api/regions/{id}/schemas` | Update schema |
| POST | `/api/regions/{id}/schemas/upload` | Upload schema file |

### Campaign Status Endpoint (for dashboard)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns/{id}/setup-status` | Returns voter list + petition status |

Response:
```json
{
  "voter_list": {
    "exists": true,
    "row_count": 50000,
    "uploaded_at": "2026-03-15T10:30:00Z",
    "region_name": "DC"
  },
  "petitions": {
    "exists": true,
    "file_count": 3,
    "signature_count": 120
  },
  "jobs": {
    "total": 0,
    "active": 0
  },
  "state": "ready_to_process"
}
```

---

## Frontend Components

### ProgressStepper Component

Location: `src/lib/components/dashboard/ProgressStepper.svelte`

Props:
- `voterListStatus`: object | null
- `petitionStatus`: object | null
- `hasJobs`: boolean

States:
| State | Display | CTA |
|-------|---------|-----|
| `empty` | ☐ Voter List ☐ Petitions | "Upload Voter List" |
| `voter_only` | ☑ Voter List ☐ Petitions | "Upload Petitions" |
| `petitions_only` | ☐ Voter List ☑ Petitions | "Upload Voter List" |
| `ready` | ☑ Voter List ☑ Petitions | "Create Job" |
| `has_results` | Collapsed/hidden | (Show metrics) |

### Voter List Display (Upload Page)

Add to Voter List tab in `/workspace/[id]/upload/+page.svelte`:
- Show existing voter list info (count, region, date)
- Delete button with confirmation
- Re-upload option

### Region Schema Editor

Location: `/workspace/settings` → "Region Schemas" section

Features:
- List all region schemas
- Edit column mappings (form)
- Upload schema file (YAML/JSON)
- Download schema as file
- Preview: show sample CSV with mapping applied

---

## Upload Flow (Merge/Update)

```
New voter list uploaded for region X
        │
        ▼
Load region schema → parse CSV → normalize rows
        │
        ▼
For each row:
  - Compute data_hash from hash_fields
  - Query existing voter by (region_id, data_hash)
  - If found: update last_seen_at, last_upload_id
  - If new: insert with first_seen_at, first_upload_id
        │
        ▼
Mark previous upload as superseded
```

---

## Schema File Format

```yaml
name: "Washington DC Voter Roll"
column_mappings:
  VoterID: voter_id
  FirstName: first_name
  LastName: last_name
  StreetAddr: street
  City: city
  State: state
  ZipCode: zip
hash_fields:
  - first_name
  - last_name
  - street
  - zip
```

---

## Migration Path

1. Create `voter_list_uploads` table
2. Create `region_schemas` table
3. Add columns to `registered_voter` (data_hash, first_seen_at, last_seen_at, first_upload_id, last_upload_id)
4. Backfill existing voters:
   - Set `first_seen_at = created_at`
   - Compute `data_hash` from existing name_data + address_data
5. Seed default region schemas (DC, etc.)

---

## Files Affected

| Layer | File | Changes |
|-------|------|---------|
| Model | `backend/app/data/database/model/voter_list_upload.py` | NEW table |
| Model | `backend/app/data/database/model/region_schema.py` | NEW table |
| Model | `backend/app/data/database/model/registered_voter.py` | Add tracking fields |
| Service | `backend/app/services/voter_list_service.py` | NEW - merge logic, schema parsing |
| Router | `backend/app/routers/upload_router.py` | Add GET, DELETE endpoints |
| Router | `backend/app/routers/region_router.py` | Schema CRUD endpoints |
| Router | `backend/app/routers/campaign_router.py` | Add setup-status endpoint |
| Frontend | `src/routes/workspace/[id]/+page.svelte` | Progress section |
| Frontend | `src/routes/workspace/[id]/upload/+page.svelte` | Voter list display |
| Frontend | `src/lib/components/dashboard/ProgressStepper.svelte` | NEW component |
| Frontend | `src/routes/workspace/settings/RegionSchemaEditor.svelte` | NEW admin UI |

---

## Test Requirements

### Backend Unit Tests
- Voter matching by data_hash
- Merge/update logic
- Schema parsing
- Upload history tracking

### Backend Integration Tests
- Upload voter list → verify voters created
- Upload again → verify merge behavior
- Delete voter list → verify cleanup

### Frontend E2E Tests
- Dashboard shows correct state for each campaign phase
- Voter list tab shows existing uploads
- Delete confirmation flow

---

## Estimated Scope

**Medium** (3-5 days)

| Task | Est. Hours |
|------|------------|
| Database models + migration | 4 |
| VoterListService (merge logic) | 6 |
| API endpoints | 4 |
| ProgressStepper component | 3 |
| Voter list display (upload page) | 2 |
| Region schema editor | 4 |
| Tests | 4 |
| **Total** | **27** |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Large voter lists (100k+) may be slow to hash | Batch processing, progress indicator |
| Schema migration for existing voters | Backfill script with progress logging |
| Region schema complexity | Start with simple default, iterate |

---

## Open Questions

None - all decisions captured above.
