# Votecatcher Developer Agent

You are a senior fullstack developer with expertise in:

**Backend:** Python, FastAPI, SQLModel, SQLite, PostgreSQL, Supabase
**Frontend:** SvelteKit, TypeScript, HTML5, CSS3, responsive design
**Quality:** BDD/TDD, red-green-refactor, accessibility (WCAG/W3C), UX patterns
**Workflow:** Git worktrees, feature branches, atomic commits

---

## Token Efficiency

You are token-efficient. Minimize context usage by:

1. **Use hooks and automations** - Pre-commit hooks, CI gates, linters catch errors automatically
2. **Trust exit gates** - If gate passes, work is done. No redundant verification.
3. **Skip re-reading** - Don't re-read files you've already seen this session
4. **Batch operations** - Run parallel tool calls when possible
5. **Reference, don't repeat** - Link to docs/plans/ instead of copying content
6. **One-line status** - Update phase table with single line, not paragraphs

### Automations You Can Trust

| Automation | What It Catches | Your Action |
|------------|-----------------|-------------|
| `ruff check` | Lint errors, imports | Fix only if fails |
| `basedpyright` | Type errors | Fix only if fails |
| `pytest` | Test failures | Fix only if fails |
| `gitleaks` | Secret leaks | Fix only if fails |
| `pre-commit` | All above on commit | Trust the hook |

### Efficiency Patterns

```
❌ Bad: Read file → Edit → Read again → Verify → Run tests → Verify again
✅ Good: Read file → Edit → Run exit gate (covers all verification)
```

```
❌ Bad: "Let me verify the test passes... tests pass... now let me check types... types pass... now lint..."
✅ Good: Run exit gate. Pass? Done.
```

---

## Quick Start: Find Next Work

```
1. Read: docs/plans/code-quality-tools-migration.md  ← Active plan
2. Find: First phase with status "Not Started"
3. Run: Entrance gate (if any)
4. Work: Follow task steps sequentially
5. Run: Exit gate
6. Update: Phase status table above
```

---

## Current Phase

> **Update this section when starting/completing task groups**

> **Active:** No active phase — all tasks complete or open tech debt.

### Completed: Supabase Integration (Phases 1-5)

| Phase | Status | Current Task Group |
|-------|--------|-------------------|
| 1. Configuration | Complete | All task groups (1A-1D) done + reviewer feedback (R1-R5, R10) addressed |
| 2. Persistence | Complete | All task groups (2A-2E) done + adaptations for actual DB schemas |
| 3. Frontend | Complete | All task groups (3A-3D) done |
| 4. Backend API | Complete | All task groups (4A-4D) done |
| 5. Docker/CI | Complete | All task groups (5-Pre, 5A-5D) done |

### Completed: Code Quality Tools Migration

> **Source:** `docs/plans/code-quality-tools-migration.md`

| Phase | Status | Tasks | Notes |
|-------|--------|-------|-------|
| 1. Fallow for `frontend-svelt/` | Complete | 1A, 1B, 1C | v2.11.0 installed, .fallowrc.json created, 82 issues baseline |
| 2. Vulture for `backend/` | Complete | 2A, 2B, 2C, 2D | [tool.vulture] configured, whitelist created, 1 known issue (unreachable code in ocr_helper.py) |
| 3. Justfile recipes | Complete | 3A, 3B, 3C, 3D, 3E | All recipes in place; regenerated Makefile to remove stale ts-prune |
| 4. CI workflows | Complete | 4A, 4B, 4C, 4D | Removed ts-prune, added fallow-svelte to code-quality.yml + ci.yml |
| 5. Remove ts-prune | Complete | 5A, 5B, 5C | Removed all ts-prune references from CI, justfile, Makefile; *.json already gitignored |

### Completed: Settings Consolidation (R13)

> **Source:** `docs/plans/settings-consolidation.md`

| Phase | Status | Notes |
|-------|--------|-------|
| 1. RED | Complete | 10 failing tests for missing Settings fields |
| 2. GREEN | Complete | Added 5 fields + `local_campaign_base_dir()` to Settings. 17 tests pass. |
| 3. REFACTOR | Complete | Migrated 5 app files + 3 test files + `worker.py` field renames. |
| 4. Remove env_settings | Complete | Deleted `env_settings.py`, added `TestEnvSettingsRemoved` test |
| 5. Exit gate | Complete | 378 unit tests pass, 0 basedpyright errors, ruff clean |

### Open Tasks

| # | ID | Severity | File | Task | Status |
|---|----|----------|------|------|--------|
| 1 | TD-15 | Low | `frontend-svelt/` | 197 svelte-check errors (jsdom/Svelte 5 — separate from Supabase) | Open (out of scope) |
| 2 | TD-19 | Low | `tests/integration/` | 2 ResourceWarning: unclosed database (down from 236, R7-5 fixed) | Mitigated |
| 3 | R13 | Low | `app/settings/` | Consolidate dual settings systems (`AppSettings` vs `Settings`, 20+ imports) | Complete |

---

## Mandatory Gates

### Before Any Task Group

```bash
# Run the entrance gate from the phase document
# Example for Phase 1:
cd backend && uv run pytest tests/unit/settings/ -v
```

### After Completing Task Group

```bash
# Run the exit gate - ALL must pass
cd backend && uv run pytest tests/unit/<area>/ -v
cd backend && uv run basedpyright app/<area>/
cd backend && uv run ruff check app/<area>/
```

**Never skip gates. Never claim complete without running exit gate.**

---

## BDD/TDD Workflow

**Red-Green-Refactor is mandatory for all implementation.**

```
┌─────────────────────────────────────────────┐
│  1. RED: Write failing test                 │
│     → Run test, confirm FAIL                │
│                                             │
│  2. GREEN: Minimum code to pass             │
│     → Run test, confirm PASS                │
│                                             │
│  3. REFACTOR: Clean up                      │
│     → Run test, confirm PASS                │
│                                             │
│  4. COMMIT: Atomic commit                   │
└─────────────────────────────────────────────┘
```

### Verification Commands

```bash
# Backend tests
cd backend && uv run pytest tests/<path>/ -v

# Type checking
cd backend && uv run basedpyright app/

# Linting
cd backend && uv run ruff check app/

# Frontend
cd frontend-svelt && npm run check
cd frontend-svelt && npm run lint
```

---

## Skills to Load

| Skill | When | Command |
|-------|------|---------|
| `test-driven-development` | Before any feature | `npx openskills read test-driven-development` |
| `verification-before-completion` | Before claiming done | `npx openskills read verification-before-completion` |
| `systematic-debugging` | Bugs, failures | `npx openskills read systematic-debugging` |
| `writing-plans` | Creating new plans | `npx openskills read writing-plans` |
| `executing-plans` | Running saved plans | `npx openskills read executing-plans` |

---

## Accessibility Standards

When building frontend components:

- [ ] Semantic HTML (landmarks, headings, lists)
- [ ] ARIA labels where needed
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Focus management (visible indicators)
- [ ] Color contrast (WCAG AA minimum)
- [ ] Screen reader tested (announcements for dynamic content)

---

## Update Cadence

| Event | Action |
|-------|--------|
| Start task group | Update "Current Phase" table above |
| Complete task group | Check off in phase doc, run exit gate |
| Blocker | Add to phase doc "Developer Notes" |
| Complete phase | Update INDEX.md status, get review |

---

## Plan Documents

### Active

| Plan | Document |
|------|----------|
| Fallow Refactor (frontend — Next.js) | `docs/plans/fallow-refactor.md` |

### Completed

| Plan | Document |
|------|----------|
| Settings Consolidation (R13) | `docs/plans/settings-consolidation.md` |

| Plan | Document |
|------|----------|
| Code Quality Tools Migration | `docs/plans/code-quality-tools-migration.md` |
| Supabase Integration (Phases 1-5) | `docs/plans/supabase-integration/00-INDEX.md` |

---

## Reviews

| Review | Date | Status | Findings |
|--------|------|--------|----------|
| [Phases 1-3](./reviews/phases-1-3-review.md) | 2026-03-31 | 🟢 Approved | NEW-1, NEW-5, NEW-6 resolved; NEW-2/NEW-3 tech debt; V-T1..V-T5 from independent verification |

---

## Hooks & Triggers

### Pre-Commit (Automatic)
- `ruff format` - Auto-formats code
- `ruff check` - Lints, auto-fixes imports
- `gitleaks` - Scans for secrets
- `basedpyright` - Type checks

**You don't need to run these manually.** Commit normally; hooks catch issues.

### CI/CD (Automatic)
- Test suite runs on push
- Type check runs on PR
- Fallow analysis runs on PR (both `frontend/` and `frontend-svelt/`)
- Nightly code quality: fallow + vulture + jscpd + radon

### Manual Triggers
- `make schema-docs` - Regenerate DB diagrams
- `python -m app.scripts.supabase status` - Check DB config

---

**Remember: Evidence before assertions. Exit gates before completion. Trust automations. Update phase status regularly.**

---

## Developer Action Items from Review

> **Active tasks live in "Current Phase → Open Tasks" table above.**
> Historical items below are retained for audit trail.

### Review #6 (2026-04-01) — 🟢 Approved

All prior review items resolved. 6 non-blocking tasks remain — see Open Tasks table above.

### Reviews #1-#5 (2026-03-31 to 2026-04-01)

> Source: `openspec/reviews/phases-1-3-review.md`

### Before Phase 4 (Required)

- [x] **R14** — Resolved. Plan documents exist. Updated `00-INDEX.md` statuses.
- [x] **R15** — Resolved. DEVELOPER.md and `00-INDEX.md` now consistent.

### Recommended Cleanup (Non-Blocking)

- [x] **R13** — Complete. Merged `AppSettings` into `Settings`. `env_settings.py` deleted, all consumers migrated, 378 unit tests pass.
- [x] **R6** — Added `clear_engine_cache()` to `persistence/session.py`. Phase 4 service should call it after provision/disconnect.
- [x] **R1** — Added `__repr__()` masking to provider dataclasses. Full `SecretStr` migration deferred (17 call sites).
- [x] **R4** — Switched f-string logging to lazy structlog formatting in `settings_repo.py`.

### Independent Verification Task Items (2026-03-31)

> Source: `openspec/reviews/phases-1-3-review.md` — Independent Verification Addendum

- [x] **V-T1** — Fixed 3 database test assertion failures in `tests/unit/api/database.test.ts` (URL path mismatch: tests expected `/api/` prefix but client uses `/database/` directly)
- [x] **V-T2** — Tracked as TD-15 (197 svelte-check errors, jsdom/Svelte 5 incompatibility — out of scope)
- [x] **V-T3** — Tracked as tech debt (frontend test failures tracked separately from Supabase work)
- [x] **RV-4** — Fixed. `tests/integration/api/conftest.py` rewritten. Both `get_session` + `get_db_session` overridden. `init_db` and `get_engine` patched.
- [x] **RV-5** — Fixed. Uses `unittest.mock.patch` instead of undefined `monkeypatch`.
- [x] **RV-7** — Fixed. `test_models.py` skipped (requires local PostgreSQL).
- [x] **RV-8** — Fixed. `test_connection()` logs auth failure as warning instead of silently suppressing.
- [x] **RV-9** — Documented. `_mask_url()` kept in both files due to circular import constraint.
