# Votecatcher OpenSpec

Implementation specification and progress tracking for Votecatcher.

**Current Version:** Post-MVP Iteration (Phases 7-12)
**MVP Status:** ✅ Complete (2026-03-12)

## Documents

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Technical specification v1.5 - MVP complete, Post-MVP phases 7-12 planned |
| [adr/](adr/) | Architecture Decision Records |
| [DEVELOPER.md](DEVELOPER.md) | Developer agent instructions |
| [diagrams/](diagrams/) | Architecture and UI diagrams |
| [.skills/](.skills/) | Agent skill definitions |

## Post-MVP Documents (Active)

| File | Location | Purpose |
|------|----------|---------|
| PROGRESS.md | `.agent-workspace/problem/PROGRESS.md` | Active progress tracking - phases 7-12 |
| Requirements | `.agent-workspace/problem/REQUIREMENTS-NEXT-ITERATION-2026-03-12.md` | Post-MVP requirements (40 items) |

## Getting Started

1. Read [SPEC.md](SPEC.md) for the full technical specification
2. Check `.agent-workspace/problem/PROGRESS.md` for current status
3. Review `.agent-workspace/problem/REQUIREMENTS-NEXT-ITERATION-2026-03-12.md` for post-MVP scope

## Phase Gates

Each phase has entrance/exit criteria defined in SPEC.md §6. No phase may proceed without meeting exit criteria.

### Critical Path (Post-MVP)

```
Phase 1-6 (MVP) ──────────────────────────────────────────► ✅ COMPLETE
                                                              │
                                                              ▼
Phase 7 (Quick Fixes) ──► Phase 8 (Campaign UI) ──► Phase 9 (Job Creation)
                                                              │
                                                              ▼
Phase 10 (Jobs List) ──► Phase 11 (Upload) ──► Phase 12 (Polish)
```

## Validation Requirements

- All tasks validated through BDD/TDD
- Tests must pass before marking tasks complete
- PROGRESS.md updated at each milestone
- ADRs created for notable decisions

## Archives

| Archive | Contents |
|---------|----------|
| [archive-mvp-complete-2026-03-12/](archive-mvp-complete-2026-03-12/) | MVP-era PROGRESS.md, REQUIREMENTS.md, earlier archives |
