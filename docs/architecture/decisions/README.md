# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Votecatcher project.

## What is an ADR?

An ADR is a document that captures an important architectural decision along with its context and consequences. ADRs help future developers understand why certain decisions were made.

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| 0001 | [Record Architecture Decisions](./0001-record-architecture-decisions.md) | Accepted | 2026-03-08 |
| 0002 | [Use FastAPI BackgroundTasks for Job Orchestration](./0002-use-fastapi-background-tasks.md) | Accepted | 2026-03-08 |
| 0003 | [Use SSE for Real-time Updates](./0003-use-sse-for-realtime-updates.md) | Accepted | 2026-03-08 |
| 0004 | [Python Linting and Type Checking Configuration](./0004-python-linting-and-type-checking.md) | Accepted | 2026-03-08 |
| 0005 | [Dual SSE Architecture](./0005-dual-sse-architecture.md) | Accepted | 2026-03-25 |
| 0006 | [Spec-Driven Field Configuration](./0006-spec-driven-field-configuration.md) | Accepted | 2026-04-13 |
| 0008 | [Template-Based Field Rendering](./0008-template-based-field-rendering.md) | Accepted | 2026-04-13 |

## Creating a New ADR

1. Copy `template.md` to `NNNN-short-title.md` (where NNNN is the next number)
2. Fill in the sections
3. Update this index
4. Commit with message: `docs: add ADR-NNNN short title`

## ADR Status

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion, not yet decided |
| Accepted | Decision made, should be followed |
| Deprecated | No longer applies, but kept for history |
| Superseded | Replaced by another ADR (link to it) |

## References

- [ADR GitHub](https://adr.github.io/) - ADR guidance
- [MADR](https://github.com/adr/madr) - Markdown ADR templates
