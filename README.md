# Nexgile DecarbX — Environmental Intelligence Platform MVP

An enterprise-grade, audit-ready full-stack platform for carbon accounting (Scopes 1, 2, and 3), Product Carbon Footprinting (ISO 14067 LCA/PCF), supplier engagement, AI-driven reduction planning, executive/operational scorecards, and regulatory disclosures (CSRD, CBAM, TCFD, CDP).

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Zustand, Recharts, TanStack Table v8, Lucide React
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 ORM, Alembic, Pydantic v2, Pytest
- **Database**: PostgreSQL (Supabase-ready with local zero-setup fallback)
- **Authentication**: JWT Bearer token with Role-Based Access Control (RBAC) and facility-scoping

---

## Architectural Highlights & Strict Functional Rules

1. **Audit Lineage**: Every single `EmissionRecord` mathematically stores source `ActivityData` ID, `EmissionFactor` ID + version, human-readable auditable formula arithmetic string, unit conversions applied, allocation method, and approved_by user ID.
2. **Calculation Governance**: EmissionFactor records are strictly versioned. Changing factor versions triggers recalculation impact preview before applying.
3. **Scenario Isolation**: All what-if reduction models and forecasts are tagged with `is_scenario: true` and a `scenario_id` FK. Actuals queries strictly exclude scenario records by default.
4. **Role Enforcement**: Implemented as FastAPI dependency injection (`require_roles([Role.ADMIN, ...])`) on every data router.
5. **Data Quality Framework**: Every activity ledger item computes completeness scores (0.0–1.0), confidence tiers, validation status, and rolling-average anomaly flags.
6. **Soft Deletes**: All 41 platform tables inherit `AuditBaseMixin` enforcing `is_deleted = False` filtering across all queries.
7. **No UI Calculation Logic**: All arithmetic, unit conversions, and emission calculations reside exclusively in pure backend services (`app.services.calc_engine`, `app.services.pcf_engine`).

---

## Quick Start Guide

### 1. Backend Setup

```bash
cd backend

# Create virtual environment and activate
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Environment Configuration (leave blank for local fallback or provide Supabase keys)
cp .env.template .env

# Run database migrations
alembic upgrade head

# Seed realistic demo database
python -m app.seed

# Run tests
pytest tests/ -v

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

Backend API Swagger Docs will be live at: `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend application will be live at: `http://localhost:5173`

---

## Environment Variables (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `SUPABASE_URL` | Supabase project API URL | `""` (blank in template) |
| `SUPABASE_KEY` | Supabase public anon key | `""` (blank in template) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role secret key | `""` (blank in template) |
| `DATABASE_URL` | Direct PostgreSQL connection string | `""` (falls back to local SQLite `decarbx.db` if blank) |
| `SECRET_KEY` | JWT signing secret | Standard enterprise default |
| `ALGORITHM` | JWT hashing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Token expiration window | `480` |

---

## Seed Data & Demo Role Credentials

All user accounts are pre-seeded with the password: **`DecarbX2024!`**

| Role | Email | Permitted Scope & Key Views |
|---|---|---|
| **Admin** | `admin@nexgile.com` | Full tenant administration, connectors, users, factor approvals |
| **Sustainability Manager** | `sustainability@nexgile.com` | Factor versioning, baseline restatement, targets, disclosure approval |
| **ESG Analyst** | `analyst@nexgile.com` | Activity data entry, CSV uploads, PCF modeling, what-if scenarios |
| **Auditor** | `auditor@pwc-assurance.com` | Audit lineage formula verification, assurance signoffs (read-only data) |
| **Supplier** | `supplier@foxconn-tech.com` | Supplier portal, materiality questionnaires, primary data submission |
| **C-Suite** | `csuite@nexgile.com` | Executive scorecard, target trajectory, carbon budget, peer benchmark |

> **Tip:** You can switch active demo roles instantaneously at any time using the **Demo Role** dropdown in the top header without logging out.

---

## Project Structure

```
nexgileprjt/
├── backend/
│   ├── app/
│   │   ├── core/          # config.py, rbac.py, security.py
│   │   ├── db.py          # SessionLocal, dual Postgres/SQLite engine
│   │   ├── main.py        # FastAPI entry point
│   │   ├── models/        # 41 SQLAlchemy 2.0 ORM models
│   │   │   ├── auth.py, organization.py, carbon.py, pcf.py
│   │   │   ├── supplier.py, analytics.py, compliance.py, integration.py
│   │   ├── routers/       # Module API routers with RBAC dependencies
│   │   ├── schemas/       # Pydantic v2 schemas
│   │   ├── seed.py        # Comprehensive database seed script
│   │   └── services/      # Pure calculation engines & parsers
│   │       ├── calc_engine.py, pcf_engine.py, analytics_service.py, csv_import.py
│   │   tests/             # Pytest calculation engine & RBAC unit tests
│   │   alembic/           # Database migration versions
│   │   requirements.txt
│   │   .env.template
│
└── frontend/
    ├── src/
    │   ├── api/           # Axios client
    │   ├── components/    # Layout, StatCard, Badge, Modal, TanStack DataTable
    │   ├── pages/         # Dashboard, Organization, Carbon, PCF, Supplier, Analytics, Compliance, Integration, Login
    │   ├── store/         # Zustand auth & filter stores
    │   ├── types/         # TypeScript domain definitions
    │   ├── App.tsx        # Route configuration
    │   └── index.css      # Modern dark-mode Tailwind styling
    ├── package.json
    └── tailwind.config.js
```
