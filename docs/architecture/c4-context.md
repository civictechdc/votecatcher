# C4 Context Diagram

> Level 1: System Context - Shows Votecatcher in its environment

## Diagram

```mermaid
graph TB
    subgraph External
        User[Campaign Administrator<br/>Verifies petition signatures]
        LLM[LLM Providers<br/>OpenAI, Gemini, Mistral]
        Voters[Voter Registration Lists<br/>Official government data]
    end

    subgraph System
        Votecatcher[Votecatcher<br/>Petition verification system]
    end

    User -->|Upload petitions, view results| Votecatcher
    Votecatcher -->|Submit OCR batch jobs| LLM
    LLM -->|Return extracted text| Votecatcher
    Voters -->|Import voter data| Votecatcher

    style Votecatcher fill:#1168bd,color:#fff
    style User fill:#08427b,color:#fff
    style LLM fill:#999,color:#fff
    style Voters fill:#999,color:#fff
```

## Description

Votecatcher is a petition signature verification system used by campaign administrators to automate the process of matching handwritten signatures from petition scans against official voter registration lists.

### External Actors

| Actor | Description | Interaction |
|-------|-------------|-------------|
| Campaign Administrator | Person responsible for verifying petition signatures | Uploads petitions, voter lists; reviews matching results |
| LLM Providers | External AI services providing OCR capabilities | Receives batch image processing requests; returns extracted text |
| Voter Registration Lists | Official government voter data | Source data for matching signatures |

### System Context

- **Primary users:** Campaign administrators (1-5 concurrent)
- **External dependencies:** LLM provider APIs (OpenAI, Gemini, or Mistral)
- **Data sources:** Official voter registration lists (CSV/Excel)
- **Deployment:** Self-hosted on single VPS ($5-20/mo)

## Related Diagrams

- [Containers Diagram](./c4-containers.md) - Next level: application decomposition
- [Back to Architecture](./README.md)
