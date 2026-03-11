# Votecatcher OpenSpec

Implementation specification and progress tracking for Votecatcher MVP.

## Documents

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Technical specification v1.2 - architecture, data model, API, implementation plan |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Requirements update 2026-03-11 - user stories, BDD scenarios, decisions |
| [PROGRESS.md](PROGRESS.md) | Active progress tracking - phase status, issues, deviations |
| [diagrams/](diagrams/) | Architecture and UI diagrams |

## Getting Started

1. Read [SPEC.md](SPEC.md) for the full technical specification
2. Check [PROGRESS.md](PROGRESS.md) for current status
3. Reference [REQUIREMENTS.md](REQUIREMENTS.md) for user stories and BDD scenarios

## Phase Gates

Each phase has entrance/exit criteria defined in SPEC.md §6. No phase may proceed without meeting exit criteria.

### Critical Path

```
Phase 1 (Stability) ────────┐
                             ├──▶ Phase 2 (Polish) ──▶ MVP Ready
Phase 3 (Page Hierarchy) ───┘
```

Phase 1 and Phase 3 can run in parallel.

## Validation Requirements

- All tasks validated through BDD/TDD
- Tests must pass before marking tasks complete
- PROGRESS.md updated at each milestone

## Archive

Previous specifications archived in `archive-2026-03-11/`
