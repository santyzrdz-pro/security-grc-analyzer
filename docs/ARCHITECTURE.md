# Security Compliance & Risk Management Analyzer — Architecture

## System context

```mermaid
flowchart TB
    user([Security / GRC User])
    subgraph fe[Next.js 15 Frontend :3000]
      pages[App Router Pages]
      apiClient[API Client + Auth Context]
    end
    subgraph be[FastAPI Backend :8000]
      mw[Middleware: CORS, Secure Headers, Rate Limit]
      auth[JWT Auth + RBAC]
      routers[REST Routers /api/v1]
      services[Service Layer]
    end
    db[(PostgreSQL :5432)]
    openai[(OpenAI API — optional)]

    user --> pages --> apiClient -->|Bearer JWT| mw --> auth --> routers --> services --> db
    services -.optional.-> openai
```

## Component layering (backend)

```mermaid
flowchart LR
    R[Routers] --> S[Services]
    S --> M[Models / SQLAlchemy]
    M --> DB[(PostgreSQL)]
    R --> SC[Schemas / Pydantic]
    S --> SC
    subgraph Cross-cutting
      CFG[Config]
      SECU[Security / JWT]
      PERM[Permissions matrix]
      DEPS[Deps / RBAC guards]
    end
    R --> DEPS --> PERM
    DEPS --> SECU
```

## Entity‑relationship diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : has
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ REPORTS : generates
    ASSETS ||--o{ FINDINGS : "has"
    ASSETS ||--o{ RISKS : "has"
    FINDINGS ||--o{ FINDING_CONTROLS : "maps via"
    CONTROLS ||--o{ FINDING_CONTROLS : "mapped by"
    FINDINGS ||--o{ RISKS : "drives"
    FINDINGS ||--o{ REMEDIATIONS : "tracked by"
    RISKS ||--o{ REMEDIATIONS : "tracked by"

    ROLES {
      int id PK
      string name
      string description
    }
    USERS {
      int id PK
      string email
      string full_name
      string hashed_password
      bool is_active
      int role_id FK
    }
    ASSETS {
      int id PK
      string name
      string asset_type
      string criticality
      string environment
      string status
    }
    FINDINGS {
      int id PK
      string title
      string severity
      string status
      string cve
      int asset_id FK
      text ai_executive_summary
    }
    CONTROLS {
      int id PK
      string control_id
      string family
      string title
      string implementation_status
    }
    FINDING_CONTROLS {
      int id PK
      int finding_id FK
      int control_id FK
      int confidence
      string method
    }
    RISKS {
      int id PK
      string title
      int likelihood
      int impact
      int risk_score
      string risk_level
      int asset_id FK
      int finding_id FK
    }
    REMEDIATIONS {
      int id PK
      string task
      string status
      string priority
      int finding_id FK
      int risk_id FK
    }
    REPORTS {
      int id PK
      string title
      int compliance_score
      int generated_by_id FK
    }
    AUDIT_LOGS {
      int id PK
      int user_id FK
      string action
      string entity_type
      int entity_id
    }
```

## Finding ingestion → mapping → risk flow

```mermaid
sequenceDiagram
    participant U as User / Importer
    participant API as Findings API
    participant ME as Mapping Engine
    participant AI as AI Analyst
    participant DB as PostgreSQL

    U->>API: POST /findings (or CSV/JSON import)
    API->>ME: map_finding(title + description)
    ME-->>API: controls + confidence
    API->>DB: persist finding_controls
    API->>AI: analyze_finding(...)
    AI-->>API: summary / impact / explanation / remediation
    API->>DB: cache AI output on finding
    Note over U,DB: POST /risks/generate-from-findings
    U->>API: generate risks
    API->>DB: create risks (Likelihood × Impact)
```

## Deployment topology

```mermaid
flowchart LR
    subgraph compose[Docker Compose Network]
      direction LR
      fe[frontend container]
      be[backend container]
      pg[(db container - postgres:16)]
    end
    fe -->|NEXT_PUBLIC_API_URL| be
    be -->|DATABASE_URL| pg
    host1[localhost:3000] --> fe
    host2[localhost:8000] --> be
```
