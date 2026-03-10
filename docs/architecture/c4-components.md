# C4 Components Diagram (Backend)

> Level 3: Components - Shows the internal structure of the FastAPI Backend container

## Diagram

```mermaid
graph TB
    subgraph API Layer
        CampaignRoutes[Campaign Routes]
        JobRoutes[Job Routes]
        FileRoutes[File Routes]
        ConfigRoutes[Config Routes]
        SessionRoutes[Session Routes]
    end

    subgraph Service Layer
        CampaignService[Campaign Service]
        JobService[Job Service]
        FileService[File Service]
        OCRService[OCR Service]
        MatchingService[Matching Service]
        SessionService[Session Service]
    end

    subgraph Infrastructure
        JobOrchestrator[Job Orchestrator<br/>State Machine]
        SSEManager[SSE Connection Manager]
    end

    subgraph External Clients
        OpenAIClient[OpenAI Client]
        GeminiClient[Gemini Client]
        MistralClient[Mistral Client]
    end

    subgraph Data Layer
        CampaignRepo[Campaign Repository]
        JobRepo[Job Repository]
        FileRepo[File Repository]
        VoterRepo[Voter Repository]
    end

    subgraph Matching
        PreFilter[DB Pre-Filter]
        FuzzyMatcher[Fuzzy Matcher<br/>RapidFuzz]
    end

    CampaignRoutes --> CampaignService
    JobRoutes --> JobService
    FileRoutes --> FileService
    ConfigRoutes --> OCRService
    SessionRoutes --> SessionService

    JobService --> JobOrchestrator
    JobOrchestrator --> OCRService
    JobOrchestrator --> MatchingService

    OCRService --> OpenAIClient
    OCRService --> GeminiClient
    OCRService --> MistralClient

    MatchingService --> PreFilter
    MatchingService --> FuzzyMatcher

    CampaignService --> CampaignRepo
    JobService --> JobRepo
    FileService --> FileRepo
    OCRService --> FileRepo
    MatchingService --> VoterRepo

    JobService --> SSEManager

    style CampaignService fill:#1168bd,color:#fff
    style JobService fill:#1168bd,color:#fff
    style FileService fill:#1168bd,color:#fff
    style OCRService fill:#1168bd,color:#fff
    style MatchingService fill:#1168bd,color:#fff
    style JobOrchestrator fill:#6c3f00,color:#fff
```

## Component Descriptions

### API Layer (Routes)

| Component | Responsibility |
|-----------|----------------|
| Campaign Routes | Handle campaign CRUD operations |
| Job Routes | Handle job creation, status, cancellation |
| File Routes | Handle file uploads (petitions, voter lists) |
| Config Routes | Handle OCR provider configuration |
| Session Routes | Handle session save/load/export |

### Service Layer

| Component | Responsibility |
|-----------|----------------|
| Campaign Service | Business logic for campaign management |
| Job Service | Job lifecycle management, status updates |
| File Service | File upload, PDF cropping, storage |
| OCR Service | OCR job creation, batch submission, polling |
| Matching Service | Fuzzy matching execution, result storage |
| Session Service | Session persistence, export/import |

### Infrastructure

| Component | Responsibility |
|-----------|----------------|
| Job Orchestrator | State machine for job phases (OCR → Matching) |
| SSE Manager | Manage real-time connections, broadcast updates |

### External Clients

| Component | Responsibility |
|-----------|----------------|
| OpenAI Client | OpenAI batch API integration |
| Gemini Client | Gemini batch API integration |
| Mistral Client | Mistral batch API integration |

### Data Layer (Repositories)

| Component | Responsibility |
|-----------|----------------|
| Campaign Repository | Database operations for campaigns |
| Job Repository | Database operations for jobs |
| File Repository | Database operations for files, crops |
| Voter Repository | Database operations for voter lists |

### Matching Components

| Component | Responsibility |
|-----------|----------------|
| DB Pre-Filter | Filter voter list by region, zipcode |
| Fuzzy Matcher | RapidFuzz-based name/address matching |

## Key Interactions

### End-to-End Job Flow

```mermaid
sequenceDiagram
    participant User
    participant JobRoutes
    participant JobService
    participant Orchestrator
    participant OCRService
    participant LLM as LLM Provider
    participant MatchingService
    participant SSE

    User->>JobRoutes: POST /api/jobs
    JobRoutes->>JobService: create_job()
    JobService->>Orchestrator: start()
    Orchestrator->>OCRService: start_ocr_phase()
    OCRService->>LLM: submit_batch()
    OCRService-->>SSE: status_update (OCR_STARTED)

    loop Poll until complete
        OCRService->>LLM: check_status()
        OCRService-->>SSE: status_update
    end

    OCRService->>Orchestrator: ocr_complete()
    Orchestrator->>MatchingService: start_matching()
    MatchingService-->>SSE: status_update (MATCHING)
    MatchingService->>MatchingService: execute_matching()
    MatchingService->>Orchestrator: matching_complete()
    Orchestrator-->>SSE: job_complete
```

## Related Diagrams

- [Containers Diagram](./c4-containers.md) - Previous level: system containers
- [Back to Architecture](./README.md)
