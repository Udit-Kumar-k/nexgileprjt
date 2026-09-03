# Nexgile DecarbX — Environmental Intelligence Platform MVP Walkthrough

A full-stack, enterprise-grade, audit-ready platform for corporate carbon accounting, Product Carbon Footprinting (ISO 14067 LCA/PCF), supplier engagement, AI-driven reduction planning, and regulatory compliance (CSRD, CBAM, TCFD, CDP).

---

## 1. Executive Summary & Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Zustand, Recharts, TanStack Table v8, Lucide React
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 ORM, Alembic, Pydantic v2, Pytest
- **Database Layer**: Supabase PostgreSQL architecture with transparent zero-setup SQLite fallback (`sqlite:///./decarbx.db`) when `DATABASE_URL` is blank.
- **Security & RBAC**: JWT Bearer authentication with dependency-injected Role-Based Access Control and tenant/facility scoping across 6 enterprise roles.
- **Pure Calculation Engine**: Strict separation of concerns — zero business/arithmetic logic in the UI. All unit conversions, GHG Protocol formulas, and uncertainty calculations execute purely on the backend.

---

## 2. Core Modules Implemented

### Module 1: Authentication & Role-Based Access Control (RBAC)
- JWT access tokens with 480-minute lifespan and password hashing via native `bcrypt`.
- 6 distinct enterprise roles with strict permission gating:
  - **Admin**: Full tenant administration, connectors, factor version approvals.
  - **Sustainability Manager**: Factor governance, baseline restatements, targets, disclosure signoffs.
  - **ESG Analyst**: Activity data ledger entry, CSV batch ingestion, PCF modeling, what-if scenarios.
  - **Auditor**: Assurance sign-offs, read-only lineage inspection, evidence validation.
  - **Supplier**: Scoped exclusively to primary data questionnaires, scorecard rankings, and action plans.
  - **C-Suite**: Executive scorecards, target trajectories, carbon budget burn rate, and peer benchmarking (read-only).
- **Demo Quick-Switcher**: Top-header dropdown allowing instant role switching without re-logging.

### Module 2: Organization Hierarchy & Reporting Boundary Model
- Full organizational model with foreign-key tree relationships:
  `Organization` → `Entity` → `Facility` → `Department` → `CostCenter`
- Interactive expandable tree view showing legal consolidation methods (`Operational Control`, `Financial Control`, `Equity Share`) and facility ownership percentages.
- Reporting boundary configuration specifying GHG Protocol operational control approach per reporting year.

### Module 3: Enterprise Carbon Accounting (Scopes 1, 2, 3)
- **Activity Data Ledger**: TanStack Table v8 grid with data quality scores (0–100%), confidence tiers (`high`, `medium`, `low`, `estimated`), and anomaly flags.
- **Versioned Emission Factor Library**: 30 pre-seeded factors (EPA, ecoinvent, DEFRA) with version tags (`2024.1`).
- **Calculation Governance**: Factor version changes trigger impact analysis preview calculating affected records and delta tCO2e prior to applying updates.
- **Audit Lineage Inspection (Strict Rule 1)**: Every `EmissionRecord` stores source Activity ID, Factor version, unit conversion applied, allocation %, and the exact deterministic arithmetic formula string:
  ```
  (2544.0 liters * 1.0000 [Direct unit match] * 0.00268 tCO2e/liters) * 100.0% allocation = 6.817920 tCO2e
  ```
- **Baselines & Targets**: Locked 2021 base year (11,901 tCO2e) with restatement justification workflow, and SBTi 1.5°C validated target (42% reduction by 2030).

### Module 4: Product LCA & Carbon Footprint (ISO 14067)
- **Product & SKU Registry**: Registry with functional units (e.g. `1 Server Unit`, `1 Gateway Router`) and net product weights.
- **Multi-Level BOM & Process Modeler**: Component mapping with scrap rates, energy inputs, and packaging recyclability offsets.
- **Boundary Selection**: Seamlessly toggle between `cradle-to-gate`, `gate-to-gate`, and `cradle-to-grave`.
- **ISO 14067 Report Declaration**: Printable/exportable audit-ready declaration breaking down footprints across Raw Materials, Manufacturing, Packaging, Logistics, Use Phase, and End-of-Life.
- **SKU Comparison View**: Side-by-side comparative carbon intensity view across the product portfolio.

### Module 5: Supplier Engagement & Scope 3
- **Supplier Directory & Onboarding**: Onboarding pipeline with status tags (`invited`, `in_progress`, `submitted`, `verified`).
- **Materiality Questionnaire & Primary Data Portal**: Guided form capturing Scope 1 & 2 emissions, renewable electricity %, and digital attestation signatures.
- **Supplier Scorecards**: Maturity scores (0–100), A/B/C/D ratings, YoY change %, and CDP/SBTi commitment indicators.
- **Joint Decarbonization Action Plans**: Assignable reduction initiatives with target tCO2e reductions and due dates.

### Module 6: AI Analytics & Reduction Planning
- **Hotspot Pareto Chart**: Composed chart ranking top emissions contributors descending with an 80/20 cumulative % curve.
- **What-If Scenario Simulator (Strict Rule 3)**: Interactive sliders for Scope 1 fleet electrification, Scope 2 renewable PPAs, and Scope 3 circular materials. Projected emissions are computed dynamically and stored with `is_scenario = True` to guarantee actuals isolation.
- **Statistical Anomaly Alert Center**: Automatically flags data points deviating > 30% from the 3-month rolling facility average with resolution workflows.
- **Reduction Initiative Tracker**: Capex, Opex, payback periods, and verified vs projected reductions.

### Module 7: Executive & Operational Dashboards
- **Executive Scorecard**: Total Gross Emissions (4,873.28 tCO2e), Scope 1 Direct, Scope 2 Market Net (with RECs deduction), and Scope 3 Value Chain.
- **SBTi Target Trajectory**: Area chart showing actual historical trajectory against the 1.5°C pathway.
- **Carbon Budget Tracker**: Progress bar indicating percentage of annual carbon budget consumed.
- **Sector Peer Benchmark Card**: Placeholder comparing company carbon intensity against industry median and top decile peers.
- **Operational Drill-Down**: Interactive multi-select filters (Entity, Facility, Scope, Period) dynamically updating charts and aggregations.

### Module 8: Regulatory Compliance & Disclosure
- **Framework Checklists**: Full disclosure data points for **CSRD / ESRS E1** (E1-1, E1-4, E1-6.1 to E1-6.4, E1-9) and **CDP Climate Change**.
- **Approval Workflow**: Multi-stage governance (`draft` → `in_review` → `verified` → `approved`).
- **EU CBAM Quarterly Registry**: Imported product CN codes, direct/indirect embedded emissions, and carbon price liability.
- **Export**: One-click CSV disclosure table export.

### Module 9: Integrations & Data Ingestion
- **Connector Hub**: Status monitoring, sync frequency, and data volume counters for SAP S/4HANA, Schneider IoT Smart Meters, EDF Energy EDI, and Geotab Fleet.
- **Working CSV Batch Activity Importer**: Real multi-facility CSV file upload parsing rows, validating columns, computing data quality, and inserting into the calculation engine.
- **Inbound Webhook Live Stream**: Event logs with payload inspection.

---

## 3. Verification & Validation Results

### Backend Automated Unit Tests (Pytest)
```
tests/test_calc_engine.py::test_unit_conversion PASSED                   [ 11%]
tests/test_calc_engine.py::test_scope1_stationary_combustion PASSED      [ 22%]
tests/test_calc_engine.py::test_scope1_stationary_with_unit_conversion PASSED [ 33%]
tests/test_calc_engine.py::test_scope1_fugitive PASSED                   [ 44%]
tests/test_calc_engine.py::test_scope2_location_vs_market PASSED         [ 55%]
tests/test_calc_engine.py::test_scope3_spend_based PASSED                [ 66%]
tests/test_rbac.py::test_password_hashing PASSED                         [ 77%]
tests/test_rbac.py::test_jwt_token_generation_and_payload PASSED         [ 88%]
tests/test_rbac.py::test_role_enum_values PASSED                         [100%]

============================== 9 passed in 2.37s ==============================
```

### Frontend Production Build
```
vite v5.4.21 building for production...
✓ 2373 modules transformed.
dist/index.html                   1.13 kB
dist/assets/index-2jU7yhoJ.css   28.61 kB
dist/assets/index-C3jpU9m8.js   818.29 kB
✓ built in 31.54s with 0 errors
```

---

## 4. Repository Cleanliness & Gitignore
A root `.gitignore` is active, excluding `node_modules`, `.venv`, `dist`, `__pycache__`, and SQLite database files (`decarbx.db`). Git tracking is strictly restricted to clean source files.
