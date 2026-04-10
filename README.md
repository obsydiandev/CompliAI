# CompliAI

**Automate EU AI Act (Annex IV) Technical File lifecycle management.**

CompliAI is a modular SaaS platform that helps ML teams and compliance officers create, maintain, and export audit-ready Technical Files for high-risk AI systems under the EU AI Act. The core "Evidence-First" data model links every section of the Technical File directly to real MLOps artifacts — not static text.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CompliAI Platform                   │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  annex_iv_   │  │  ai_assistant│  │  integrations│  │
│  │  core        │  │  (Copilot,   │  │  (Git, CI,   │  │
│  │  (schema,    │  │  Q&A, diff)  │  │  MLOps)      │  │
│  │  revisions,  │  └──────────────┘  └──────────────┘  │
│  │  evidence)   │                                       │
│  └──────────────┘  ┌──────────────┐  ┌──────────────┐  │
│                    │  policy_     │  │  exports     │  │
│  ┌──────────────┐  │  engine      │  │  (PDF, MD,   │  │
│  │  auth_billing│  │  (rules,     │  │  JSON-LD)    │  │
│  │  (JWT,       │  │  alerts,     │  └──────────────┘  │
│  │  Stripe)     │  │  checks)     │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2 · Alembic |
| Database | PostgreSQL 16 + pgvector |
| Frontend | Next.js 14 (App Router) · TypeScript · TailwindCSS |
| State | Zustand · TanStack Query |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Storage | S3-compatible (MinIO in dev, AWS S3 in prod) |
| Export | WeasyPrint (PDF) · Jinja2 |
| AI | OpenAI gpt-4o (Phase 2) |
| Billing | Stripe (Phase 1 Month 2) |
| Background | Celery + Redis (Phase 4) |
| Infra | Docker Compose (dev) · Railway/Render (prod) |

---

## Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone and configure

```bash
git clone https://github.com/obsydiandev/CompliAI.git
cd CompliAI
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a strong random value
```

### 2. Start all services

```bash
docker compose up --build
```

Services will start at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (user: minioadmin / pass: minioadmin)

### 3. Verify

```bash
curl http://localhost:8000/health
# -> {"status": "ok", "version": "0.1.0"}
```

---

## Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start just the infrastructure
docker compose up postgres redis minio minio-setup -d

# Copy and configure env
cp ../.env.example .env

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
# -> http://localhost:3000
```

---

## Testing

### Backend

```bash
cd backend

# Unit tests only (no DB required)
pytest tests/test_completeness.py tests/test_validator.py -v

# All tests (requires Docker for testcontainers)
pytest -v --cov=app
```

### Frontend

```bash
cd frontend
npm run type-check
npm run lint
```

---

## Project Structure

```
CompliAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── deps.py              # Auth + tenant isolation dependencies
│   │   │   ├── router.py            # Route aggregation
│   │   │   └── endpoints/           # auth, organizations, ai_systems, sections, exports
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── modules/
│   │   │   ├── annex_iv_core/       # Annex IV schemas, completeness, validator
│   │   │   ├── ai_assistant/        # LLM prompts, draft generation (Phase 2)
│   │   │   ├── exports/             # PDF + Markdown generation
│   │   │   ├── auth_billing/        # JWT utils, Stripe (Phase 1 M2)
│   │   │   ├── policy_engine/       # Compliance rules + scheduler (Phase 4)
│   │   │   └── integrations/        # MLflow, W&B, GitHub connectors (Phase 3)
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/                     # DB migrations
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router pages
│   │   │   ├── auth/                # login, register
│   │   │   ├── dashboard/           # org dashboard
│   │   │   └── systems/             # AI system CRUD + Annex IV editors
│   │   ├── components/
│   │   │   ├── ui/                  # base UI components
│   │   │   ├── layout/              # sidebar, header
│   │   │   ├── annex-iv/            # completeness bars, section cards
│   │   │   ├── evidence/            # upload, list
│   │   │   └── systems/             # system cards
│   │   ├── lib/                     # API client, auth store, utils, metadata
│   │   └── types/                   # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── .env.example
└── .github/workflows/               # backend.yml, frontend.yml
```

---

## API Reference

Full OpenAPI docs: `http://localhost:8000/docs`

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login, get JWT |
| GET | /api/v1/auth/me | Current user |
| POST | /api/v1/organizations/ | Create organization |
| GET | /api/v1/systems/?org_id= | List AI systems |
| POST | /api/v1/systems/ | Create AI system (auto-creates TF + 9 sections) |
| POST | /api/v1/systems/validate-purpose | High-risk intent classifier |
| GET | /api/v1/systems/{id}/technical-file | Get Technical File |
| POST | /api/v1/systems/{id}/technical-file/revisions | Create new revision |
| PUT | /api/v1/systems/{id}/technical-file/revisions/{rev}/sections/{n} | Update section |
| GET | /api/v1/systems/{id}/technical-file/revisions/{rev}/sections/completeness | Completeness |
| GET | /api/v1/systems/{id}/technical-file/revisions/{rev}/export/pdf | Export PDF |
| GET | /api/v1/systems/{id}/technical-file/revisions/{rev}/export/markdown | Export Markdown |

---

## Annex IV Sections

| # | Section | Required Fields |
|---|---------|----------------|
| 1 | General Description | intended_purpose, use_cases |
| 2 | Design & Development | architecture_description, algorithms_used |
| 3 | Training Data | training_data_description, data_sources, data_quality_measures |
| 4 | Validation & Testing | validation_methodology, performance_metrics, test_results, known_limitations |
| 5 | Risk Management | risk_register, risk_assessment_methodology, control_measures |
| 6 | Lifecycle Changes | change_management_plan, changelog |
| 7 | Standards & Norms | applicable_standards |
| 8 | Human Oversight | human_oversight_measures, hitl_procedures, transparency_measures |
| 9 | Post-Market Monitoring | pmm_plan, monitoring_metrics, incident_reporting_procedure |

---

## Roadmap

| Phase | Timeline | Features |
|-------|----------|---------|
| 0 | Done | Repository skeleton, Docker Compose, CI/CD |
| 1 | M1-M3 | Core MVP: auth, Annex IV editor, PDF export, billing |
| 2 | M3-M5 | AI Copilot: LLM draft generation, Q&A (RAG), doc diff |
| 3 | M4-M6 | MLOps integrations: MLflow, W&B, GitHub, CI webhooks |
| 4 | M6-M8 | Continuous Compliance: policy engine, bias audit, PMM |
| 5 | M9-M12 | Enterprise: SSO, portfolio dashboard, ISO 42001 crosswalk |
| 6 | M12-M18 | Connector SDK, NIST AI RMF, public API, marketplace |

---

## License

Proprietary — All rights reserved.
