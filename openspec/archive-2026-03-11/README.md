# OpenSpec Integration

This directory contains the technical specification and generated implementation tasks for Votecatcher.

## Files

| File | Purpose |
|------|---------|
| `SPEC.md` | Technical specification (source of truth for implementation) |
| `TODO.md` | Generated task list with phase breakdown |
| `PROGRESS.md` | Track completed tasks and blockers |

## Usage

### Generate Tasks from Spec

```bash
# If you have openspec CLI installed
npx openspec generate TODO.md

# Or manually: Open the SPEC.md and create tasks based on Phase Verification Gates
```

### Workflow

1. **Read SPEC.md** - Understand the full architecture and approach
2. **Check TODO.md** - See current phase and tasks
3. **Pick a task** - Mark as "in_progress" in TODO.md
4. **Implement with TDD** - Write test first, then code
5. **Run exit criteria** - Verify before marking complete
6. **Mark complete** - Update TODO.md and PROGRESS.md
7. **Next task** - Continue until phase complete

### Phase Gates

Each phase has entry/exit criteria in SPEC.md §7.3. **Do not skip these.**

```
Phase 0 → verify exit criteria → Phase 1 → verify → Phase 2 → ...
```

### Referencing Supporting Docs

When implementing, reference the detailed docs as needed:

- Phase 1 (Data): `../.agent-workspace/design-session/data-model.md`
- Phase 2 (Backend): `../.agent-workspace/design-session/architecture.md`
- Phase 2 (API): `../.agent-workspace/design-session/api-spec.md`
- Phase 3 (Frontend): `../.agent-workspace/design-session/frontend-architecture.md`

## Task Status Convention

In TODO.md, use these markers:

- `[ ]` - Not started
- `[~]` - In progress
- `[x]` - Complete
- `[!]` - Blocked (note reason)

## Syncing with SPEC.md

If SPEC.md is updated (architecture changes, new decisions):

1. Review changes in SPEC.md
2. Update TODO.md tasks if needed
3. Note any completed work that needs rework
