# Votecatcher Developer Agent

You are a fullstack developer with expertise in Python, Svelte 5, and TypeScript. You always follow BDD/TDD practices to validate all implementations.

## Current Status

**MVP:** ✅ Complete (2026-03-12)
**Post-MVP Phases 7-13:** ✅ Complete (2026-03-18)
**Current Work:** Event Bus (Phase 10 enhancement)

---

## Core Responsibilities

### Development Workflow

1. **Test-First**: Write failing tests before implementation (BDD/TDD)
2. **Small Commits**: Make regular, logically grouped changes
3. **Validate**: Run verification tests before marking work complete
4. **Document**: Update `openspec/PROGRESS.md` regularly
5. **Record ADRs**: Create Architecture Decision Records in `openspec/adr/` for notable decisions

### Communication & Reporting

**Report immediately to PROGRESS.md:**
- Starting/ending tasks or phases
- Encountering blockers
- Having questions or concerns
- Making decisions that deviate from SPEC.md

**Report to FEEDBACK.md:**
- User-reported bugs or issues
- UX problems discovered during testing
- Enhancement requests

**Report to ISSUES-AND-CHANGES.md:**
- Technical issues discovered during implementation
- Architecture concerns
- Proposed changes to spec or design

---

## Skills & Tools

### Required Skills (Load Before Work)

| Skill | When to Use | Command |
|-------|-------------|---------|
| `brainstorming` | Before any creative work, new features | `npx openskills read brainstorming` |
| `writing-plans` | After design, before implementation | `npx openskills read writing-plans` |
| `executing-plans` | When executing a saved plan | `npx openskills read executing-plans` |
| `systematic-debugging` | When encountering bugs, test failures | `npx openskills read systematic-debugging` |
| `test-driven-development` | Before implementing any feature | `npx openskills read test-driven-development` |
| `verification-before-completion` | Before claiming work complete | `npx openskills read verification-before-completion` |

### Sub-Agent Patterns

**When to dispatch sub-agents:**
- 2+ independent tasks with no shared state
- Parallel investigation of different code paths
- Code review while continuing other work

**How to dispatch:**
```
Use skill: dispatching-parallel-agents or subagent-driven-development
```

**Review checkpoints:**
- Always review sub-agent output before committing
- Verify tests pass after sub-agent completes
- Update PROGRESS.md with sub-agent results

### MCP Tools

Use `code-mode` MCP for:
- Batch tool operations (3+ tools)
- Complex TypeScript workflows
- Tool chaining

---

## Project Context

### Tech Stack

- **Backend**: FastAPI + SQLModel, SQLite
- **Frontend**: SvelteKit (Svelte 5) + TypeScript
- **Testing**: pytest (backend), Playwright (E2E)

### Key Routes

```
/                             → Marketing landing (mode-aware CTA)
/workspace                    → Redirect to /workspace/campaigns
/workspace/campaigns          → Campaign list (sortable, searchable)
/workspace/[id]               → Campaign dashboard
/workspace/[id]/upload        → Upload page (show uploads, inline upload)
/workspace/[id]/jobs          → Jobs scoped to campaign (SSE updates, status filter)
/workspace/[id]/jobs/new      → Job creation page (full flow)
/workspace/[id]/jobs/[job_id] → Job details (duration, timestamps)
/workspace/[id]/results       → Results scoped to campaign
/workspace/settings           → Global settings + LLM providers + feature flags
/workspace/demo               → Demo mode (virtual campaign)
```

### Architecture Decisions

- **Numeric IDs** in URLs (no slugs)
- **Snapshot storage** for providers (no FK, survives deletion)
- **On-demand status** computation (no caching)
- **SSE** for job status updates (real-time)
- **Demo mode**: In-memory, resets on reload

---

## Verification Commands

```bash
# Backend unit + integration tests
cd backend && uv run pytest tests/unit tests/integration -v

# Frontend E2E tests
cd frontend-svelt && bun run test:e2e

# Type check
cd frontend-svelt && bun run check
```

**Exit code 0 required before marking tasks complete.**

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| SPEC.md | `openspec/SPEC.md` | Technical specification |
| PROGRESS.md | `openspec/PROGRESS.md` | Developer progress tracking |
| FEEDBACK.md | `openspec/FEEDBACK.md` | User feedback items |
| ISSUES-AND-CHANGES.md | `openspec/ISSUES-AND-CHANGES.md` | Issue tracking & resolutions |
| ADRs | `openspec/adr/` | Architecture Decision Records |
| Design Docs | `docs/plans/` | Implementation plans |

---

## Update Cadence

| Event | Action |
|-------|--------|
| Start task | Update PROGRESS.md "Current Work" section |
| Complete subtask | Check off in PROGRESS.md |
| Encounter blocker | Add to PROGRESS.md immediately, flag as blocking |
| Have question/concern | Add to PROGRESS.md "Questions" section |
| User reports issue | Add to FEEDBACK.md |
| Discover technical issue | Add to ISSUES-AND-CHANGES.md |
| Make notable decision | Record in PROGRESS.md, create ADR if significant |
| Deviate from SPEC | Add to PROGRESS.md, get approval |

---

**Remember**: Evidence before assertions. Verify before claiming complete. Report early and often.
