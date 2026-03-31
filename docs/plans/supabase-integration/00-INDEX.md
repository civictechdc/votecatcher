# Supabase Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Design and implement a unified system for connecting Votecatcher to Supabase with reorganized configuration architecture and abstracted persistence layer.

**Architecture:** Layered approach with Settings providers at top, Persistence engines at bottom. Business logic remains database-agnostic through repository pattern and domain objects.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, Pydantic-settings, Supabase Python client, Alembic, SvelteKit

---

## Plan Documents

| Phase | Document | Description | Status |
|-------|----------|-------------|--------|
| 0 | [00-INDEX.md](./00-INDEX.md) | This file - overview and dependencies | N/A |
| 1 | [01-configuration-architecture.md](./01-configuration-architecture.md) | Settings reorganization, contracts, providers | Complete |
| 2 | [02-persistence-layer.md](./02-persistence-layer.md) | Engine contracts, domain objects, repositories | Complete |
| 3 | [03-frontend-onboarding-v2.md](./03-frontend-onboarding-v2.md) | Svelte 5 wizard, database selector, settings page (replaces original) | Not Started |
| 3 | ~~[03-frontend-onboarding.md](./03-frontend-onboarding.md)~~ | ~~Original (Svelte 4 — superseded by v2)~~ | ~~Superseded~~ |
| 4 | [04-backend-api-cli.md](./04-backend-api-cli.md) | Database endpoints, Supabase CLI script | Not Started |
| 5 | [05-docker-cicd.md](./05-docker-cicd.md) | Docker compose, gitleaks, schema docs | Not Started |

---

## Prerequisites

Before starting any phase:

- [ ] **Python 3.12+** installed
- [ ] **uv** package manager installed
- [ ] **Node.js 18+** for frontend
- [ ] Access to Supabase dashboard for testing

---

## Execution Order

Phases must be completed in order due to dependencies:

```
Phase 1 (Config) ──► Phase 2 (Persistence) ──► Phase 4 (Backend API)
                              │
                              ▼
                    Phase 3 (Frontend) ───────► Phase 5 (Docker/CI)
```

**Note:** Phase 3 and 4 can run in parallel after Phase 2. Phase 5 requires Phase 4.

---

## Global Exit Gate

All phases must pass these checks before considering the implementation complete:

```bash
# Run all tests
cd backend && uv run pytest tests/ -v

# Type checking
cd backend && uv run basedpyright app/

# Linting
cd backend && uv run ruff check app/

# Frontend type check
cd frontend-svelt && npm run check
```

---

## Developer Notes

_Use this section to track overall progress, blockers, and decisions:_

| Date | Note |
|------|------|
| YYYY-MM-DD | Initial plan created |

---

## Reviewer Notes

_For code review feedback and approvals:_

| Phase | Reviewer | Status | Date | Notes |
|-------|----------|--------|------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
