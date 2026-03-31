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
1. Read: docs/plans/supabase-integration/00-INDEX.md  ← Start here
2. Find: First task group with status "Not Started"
3. Run: Entrance gate command
4. Work: Follow task steps sequentially
5. Run: Exit gate command
6. Update: Phase status table
```

---

## Current Phase

> **Update this section when starting/completing task groups**

| Phase | Status | Current Task Group |
|-------|--------|-------------------|
| 1. Configuration | Complete | All task groups (1A-1D) done + reviewer feedback (R1-R5, R10) addressed |
| 2. Persistence | Complete | All task groups (2A-2E) done + adaptations for actual DB schemas, mismatched in domain objects andrepos |
| 3. Frontend | Not Started | - |
| 4. Backend API | Not Started | - |
| 5. Docker/CI | Not Started | - |

**Last Updated:** 2026-03-27

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

| Phase | Document |
|-------|----------|
| Index | `docs/plans/supabase-integration/00-INDEX.md` |
| Phase 1 | `docs/plans/supabase-integration/01-configuration-architecture.md` |
| Phase 2 | `docs/plans/supabase-integration/02-persistence-layer.md` |
| Phase 3 | `docs/plans/supabase-integration/03-frontend-onboarding-v2.md` |
| Phase 4 | `docs/plans/supabase-integration/04-backend-api-cli.md` |
| Phase 5 | `docs/plans/supabase-integration/05-docker-cicd.md` |

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
- Schema docs regenerate on model changes

### Manual Triggers
- `make schema-docs` - Regenerate DB diagrams
- `python -m app.scripts.supabase status` - Check DB config

---

**Remember: Evidence before assertions. Exit gates before completion. Trust automations. Update phase status regularly.**
