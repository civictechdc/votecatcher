# Votecatcher Architecture Documentation

This directory contains architecture documentation following industry best practices scaled to MVP project size.

## Contents

### C4 Model Diagrams

The C4 model provides a simple, hierarchical way to visualize software architecture.

| Document | Level | Description |
|----------|-------|-------------|
| [c4-context.md](./c4-context.md) | 1 | System Context - Votecatcher in its environment |
| [c4-containers.md](./c4-containers.md) | 2 | Containers - Applications and data stores |
| [c4-components.md](./c4-components.md) | 3 | Components - Backend service decomposition |

### Project Structure

| Document | Description |
|----------|-------------|
| [project-structure.md](./project-structure.md) | Directory layout and module overview |

### Architecture Decision Records (ADRs)

ADRs capture important architectural decisions along with their context and consequences.

- [ADR Index](./decisions/README.md)
- [ADR Template](./decisions/template.md)

## Quick Reference

### Key Architectural Decisions

| Decision | ADR | Status |
|----------|-----|--------|
| Use FastAPI BackgroundTasks for job orchestration | [ADR-0002](./decisions/0002-use-fastapi-background-tasks.md) | Accepted |
| Use SSE for real-time updates | [ADR-0003](./decisions/0003-use-sse-for-realtime-updates.md) | Accepted |
| Hybrid matching: DB pre-filter + RapidFuzz | [ADR-0004](./decisions/0004-hybrid-matching-strategy.md) | Accepted |

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | FastAPI + SQLModel | Async, type-safe, rapid development |
| Frontend | SvelteKit + TypeScript | Fast, compiled, type-safe |
| Database | PostgreSQL | Reliable, feature-rich, well-supported |
| OCR | LLM Batch APIs (OpenAI, Gemini, Mistral) | Cost-effective, async processing |
| Matching | RapidFuzz | Fast fuzzy string matching |

## External References

- [C4 Model](https://c4model.com/) - Official C4 model documentation
- [Architecture Decision Records](https://adr.github.io/) - ADR guidance
- [Mermaid Documentation](https://mermaid.js.org/) - Diagram syntax reference
