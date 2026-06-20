# Security Compliance & Risk Management Analyzer

> Automated cybersecurity **GRC** platform for **compliance**, **risk management**, and **NIST 800‑53 control‑mapping**.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-06B6D4?logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Portfolio-blue)

The **Security Compliance & Risk Management Analyzer** ingests technical security findings, automatically maps them to NIST SP 800‑53 controls, scores risk, maintains a risk register, tracks remediation, scores compliance, and generates audit‑ready reports — with an AI Security Analyst that translates technical findings into business language.

It is built to look and feel like a commercial GRC SaaS product (Drata / Vanta / Secureframe / Wiz style), with a dark, responsive UI.

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Quick start (Docker)](#quick-start-docker)
- [Local development](#local-development)
- [Using your own data](#using-your-own-data)
- [Optional: enable login & RBAC](#optional-enable-login--rbac)
- [API overview](#api-overview)
- [Database schema](#database-schema)
- [The mapping & risk engines](#the-mapping--risk-engines)
- [AI Security Analyst](#ai-security-analyst)
- [Security controls implemented](#security-controls-implemented)
- [Project structure](#project-structure)
- [Roadmap (future‑ready architecture)](#roadmap-future-ready-architecture)

---

## Features

| # | Module | Description |
|---|--------|-------------|
| 1 | **Asset Inventory** | CRUD, search, filtering, pagination across Workstations, Servers, Cloud Resources, Network Devices, Applications |
| 2 | **Findings Management** | Manual create + CSV/JSON import, severity/status workflow, evidence & CVE tracking |
| 3 | **NIST Control Library** | Searchable NIST 800‑53 catalog (AC‑2/3/6, IA‑2/5, AU‑2/6, SC‑7, SI‑4) with implementation status |
| 4 | **Automatic Control Mapping** | Rule‑based keyword + pattern engine with confidence scoring and multi‑control output |
| 5 | **Risk Register** | `Risk = Likelihood × Impact` (1–5), auto‑leveled, auto‑generated from findings |
| 6 | **AI Security Analyst** | Executive summary, business impact, technical explanation, remediation (OpenAI + offline fallback) |
| 7 | **Executive Dashboard** | KPI widgets + Recharts: severity, risk distribution, controls by family, remediation, monthly trend |
| 8 | **Compliance Scoring** | Weighted implemented/total %, letter grade (A–F), gauges, per‑family breakdown |
| 9 | **Audit Report Generator** | Branded multi‑section PDF (ReportLab) with one‑click export |
| 10 | **Remediation Tracking** | Kanban board (Not Started / In Progress / Blocked / Completed) |
| 11 | **RBAC** | Admin, Security Analyst, Auditor, Executive with a permission matrix |
| 12 | **Audit Logging** | Security‑relevant events recorded with actor, action, entity, IP |

---

## Tech stack

**Frontend:** Next.js 15 (App Router) · TypeScript · Tailwind CSS · shadcn‑style components · Recharts · lucide‑react
**Backend:** Python · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · ReportLab
**Database:** PostgreSQL 16
**Auth:** JWT (OAuth2 password flow) · bcrypt · role‑based access control
**Infra:** Docker · Docker Compose

---

## Architecture

```mermaid
flowchart LR
    subgraph Client
      U[User Browser]
    end

    subgraph Frontend["Next.js 15 (Frontend)"]
      UI[App Router Pages]
      AC[Auth Context + API Client]
    end

    subgraph Backend["FastAPI (Backend)"]
      API[REST API /api/v1]
      SEC[JWT Auth + RBAC + Secure Headers + Rate Limit]
      subgraph Services
        MAP[Mapping Engine]
        RISK[Risk Engine]
        COMP[Compliance Engine]
        AI[AI Analyst]
        RPT[PDF Report Generator]
        AUD[Audit Logger]
      end
    end

    DB[(PostgreSQL)]
    OAI[(OpenAI API - optional)]

    U --> UI --> AC -->|Bearer JWT| API
    API --> SEC --> Services
    Services --> DB
    AI -.optional.-> OAI
```

Request lifecycle: the browser calls the FastAPI backend directly (no login by default). Business logic lives in `app/services/`, keeping routers thin.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the data model and engine diagrams.

---

## Quick start (Docker)

**Prerequisites:** Docker Desktop (Docker + Docker Compose).

```bash
# 1. Copy environment defaults
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env

# 2. Build and start everything (Postgres + FastAPI + Next.js)
docker compose up --build
```

Then open:

| Service | URL |
|---------|-----|
| Frontend (app) | http://localhost:3000 |
| Backend API docs (Swagger) | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/api/v1/openapi.json |
| Health check | http://localhost:8000/health |

On first boot the backend **creates the schema and seeds the NIST 800-53 control library** (required for automatic mapping). Demo assets/findings are **off by default** — import your own CSV instead. Set `SEED_DEMO_DATA=true` in `.env` to load sample data.

> The AI Security Analyst works **without** an API key using a deterministic local fallback. To use real OpenAI output, set `OPENAI_API_KEY` in `.env`.

---

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Point at a running Postgres (or use docker compose up db)
set DATABASE_URL=postgresql+psycopg://controlmap:controlmap@localhost:5432/controlmap
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
# create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## Using your own data

The app opens straight to the dashboard — no login required.

1. **(Optional) Add assets** on the Assets page (servers, apps, databases, etc.).
2. Go to **Findings → Import CSV** (or Import JSON).
3. Use a CSV with these columns (see `samples/findings_sample.csv`):

| Column | Required | Notes |
|--------|:--------:|-------|
| `title` | ✅ | Finding title |
| `description` | | Technical detail |
| `severity` | | `Critical`, `High`, `Medium`, `Low`, `Info` |
| `status` | | `Open`, `In Progress`, `Resolved`, `Accepted` |
| `source` | | e.g. Nessus, Qualys, manual review |
| `cve` | | CVE ID if applicable |
| `asset` | | Matched by name to an existing asset (optional) |
| `detection_date` | | `YYYY-MM-DD` |
| `evidence` | | Audit evidence text |

Imported findings are **automatically mapped to NIST 800-53 controls** and get AI analysis (local fallback if no OpenAI key). Use **Mapping Engine** to re-run mapping, **Risk Register** for scored risks, and **Reports** to download a PDF audit pack.

---

## Optional: enable login & RBAC

By default `AUTH_ENABLED=false` for a simpler single-user experience. To restore multi-user login with Admin / Analyst / Auditor / Executive roles, set in `.env`:

```env
AUTH_ENABLED=true
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=YourSecurePassword
```

Then re-enable the login flow in the frontend (see git history). The backend RBAC permission matrix remains available when auth is enabled:

| Capability | Admin | Analyst | Auditor | Executive |
|------------|:-----:|:-------:|:-------:|:---------:|
| Assets read / write | ✅ / ✅ | ✅ / ✅ | ✅ / ❌ | ❌ / ❌ |
| Findings read / write | ✅ / ✅ | ✅ / ✅ | ✅ / ❌ | ❌ / ❌ |
| Controls read / write | ✅ / ✅ | ✅ / ❌ | ✅ / ❌ | ❌ / ❌ |
| Risks read / write | ✅ / ✅ | ✅ / ✅ | ✅ / ❌ | ❌ / ❌ |
| Remediation read / write | ✅ / ✅ | ✅ / ✅ | ✅ / ❌ | ❌ / ❌ |
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Reports read / generate | ✅ / ✅ | ✅ / ✅ | ✅ / ❌ | ✅ / ✅ |
| Users management | ✅ | ❌ | ❌ | ❌ |
| Audit logs | ✅ | ❌ | ✅ | ❌ |

---

## API overview

Base path: `/api/v1`. Full interactive docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Obtain JWT (OAuth2 password form) |
| `GET` | `/auth/me` | Current user + permissions |
| `GET/POST` | `/assets` | List (search/filter/paginate) / create |
| `GET/PATCH/DELETE` | `/assets/{id}` | Retrieve / update / soft‑delete |
| `GET/POST` | `/findings` | List / create (auto‑maps + AI analysis) |
| `POST` | `/findings/import/csv` · `/findings/import/json` | Bulk import |
| `POST` | `/findings/{id}/remap` · `/findings/{id}/analyze` | Re‑run mapping / AI |
| `GET/POST` | `/controls` | NIST control library |
| `POST` | `/mapping` | Test the mapping engine on arbitrary text |
| `GET/POST` | `/risks` | Risk register |
| `POST` | `/risks/generate-from-findings` | Auto‑create risks |
| `GET/POST/PATCH/DELETE` | `/remediations` | Kanban tasks |
| `GET` | `/dashboard` | Executive dashboard data |
| `GET` | `/compliance` | Compliance score + grade |
| `GET/POST` | `/reports` | List / generate PDF |
| `GET` | `/audit-logs` | Audit trail (Admin/Auditor) |
| `GET/POST/PATCH/DELETE` | `/users` | User management (Admin) |

Example mapping response:

```json
{ "finding": "Firewall Disabled", "controls": ["SC-7"], "confidence": 88 }
```

---

## Database schema

Tables: `users`, `roles`, `assets`, `findings`, `controls`, `finding_controls`, `risks`, `remediations`, `reports`, `audit_logs`.

Every table includes timestamps (`created_at`, `updated_at`), and primary entities support **soft delete** (`deleted_at`). Foreign keys and indexes are defined on all relationships and common filter columns. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the ER diagram.

---

## The mapping & risk engines

**Mapping engine** (`app/services/mapping_engine.py`) — a transparent, rule‑based engine combining keyword and regex pattern matching. Pattern hits score higher than keyword hits; scores aggregate per control, support multiple controls per finding, and normalize to a 0–100 confidence. Example rules:

| Finding text | Maps to |
|--------------|---------|
| "Firewall Disabled" | `SC-7` |
| "Weak Password Policy" | `IA-5` |
| "Excessive Administrator Privileges" | `AC-6` |
| "Missing Security Logging" | `AU-6` |
| "MFA not enforced" | `IA-2` |

**Risk engine** (`app/services/risk_engine.py`) — `Risk Score = Likelihood × Impact` (each 1–5). Score → level: `1–4 Low`, `5–9 Medium`, `10–16 High`, `17–25 Critical`. When generating risks from findings, likelihood/impact are derived from finding severity and asset criticality.

**Compliance engine** (`app/services/compliance.py`) — weighted score (Implemented = 1.0, Partial = 0.5, Planned = 0.25), excluding *Not Applicable* controls, mapped to letter grades A–F.

---

## AI Security Analyst

For each finding the platform produces an **Executive Summary**, **Business Impact**, **Technical Explanation**, and **Recommended Remediation**, cached on the finding record.

- With `OPENAI_API_KEY` set, it calls the OpenAI Chat Completions API (model configurable via `OPENAI_MODEL`) with strict JSON output.
- Without a key, a deterministic local fallback generates sensible business language so the platform is fully demoable offline.

---

## Security controls implemented

- **JWT authentication** (OAuth2 password flow) with expiring access tokens
- **Password hashing** with bcrypt (passlib)
- **Role‑based authorization** enforced per endpoint via a capability matrix
- **Input validation** via Pydantic schemas
- **Rate limiting** (SlowAPI) with configurable limits
- **Audit logging** of logins (success/failure) and entity mutations
- **Secure HTTP headers** (CSP, HSTS, X‑Frame‑Options, X‑Content‑Type‑Options, Referrer‑Policy)
- **CORS** restricted to configured origins
- **Secrets via environment variables** (no secrets in code)
- **Soft deletes** to preserve audit history

---

## Project structure

```
security-grc-analyzer/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   └── ARCHITECTURE.md
├── samples/
│   ├── findings_sample.csv
│   └── findings_sample.json
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/          # config, db, security, deps, permissions
│       ├── models/        # SQLAlchemy ORM + enums
│       ├── schemas/       # Pydantic schemas
│       ├── services/      # mapping, risk, compliance, AI, reports, audit
│       ├── api/           # routers
│       └── seed/          # seed data + seeder
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── app/               # App Router pages ((app) group — no login)
    ├── components/        # sidebar, ui primitives, charts
    └── lib/               # api client, auth context, types
```

---

## Roadmap (future‑ready architecture)

The codebase is structured for **Version 2+**: the service layer and rule engine are pluggable, and findings carry source/evidence metadata ready for scanner ingestion.

- Agent‑based endpoint monitoring
- CIS Benchmark scanning · Nessus / OpenVAS importers
- Cloud compliance (SOC 2, ISO 27001, FedRAMP) frameworks
- AI risk scoring · attack‑path analysis · MITRE ATT&CK mapping

---

### License

Provided as a portfolio / demonstration project.
