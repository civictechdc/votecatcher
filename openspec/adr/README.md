# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Votecatcher project.

## What is an ADR?

An ADR captures a significant architectural decision along with its context and consequences. They help future developers (including future you) understand why certain choices were made.

## When to Create an ADR

Create an ADR when making decisions that:
- Change something from the SPEC
- Introduce new patterns or approaches
- Have significant trade-offs
- Affect multiple phases or future work
- Modify data model or API contracts

## ADR Index

| ADR | Title | Status | Date | Phase |
|-----|-------|--------|------|-------|
| (None yet) | - | - | - | - |

## Template

Use the template from `openspec/SPEC.md` §6 (Progress Reporting → ADR Requirements).

Quick reference:

```markdown
# ADR-NNNN: [Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed / Accepted / Deprecated / Superseded]
**Decision Makers:** [Who was involved]

## Context
[What is the issue being addressed?]

## Decision
[What is the change being made?]

## Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|

## Consequences
**Positive:** [Benefits]
**Negative:** [Drawbacks]
**Risks:** [Potential issues]

## References
- SPEC section: §X.X
- Requirements: [IDs]
```

## Naming Convention

- Number sequentially: `0001`, `0002`, etc.
- Use kebab-case title: `0001-sse-for-job-updates.md`
- File location: `openspec/adr/NNNN-title.md`

## Related Documents

- [SPEC.md](../SPEC.md) - Technical specification
- [PROGRESS.md](../PROGRESS.md) - Implementation progress
