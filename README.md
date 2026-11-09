# RailBlockSetu: Intelligent Railway Maintenance Planning & Optimization Platform
**NOVEX 2026 Hackathon • Category: AI / Smart Infrastructure**

---

## 🚆 Overview

Railway maintenance planning has historically been fragmented across departmental silos:
- **Engineering (P-Way):** Track packing, geometry tamping, ballast cleaning, rail defect renewals.
- **TRD (Traction Distribution):** 25kV OHE contact wire tensioning, cantilever adjustments, substation maintenance.
- **S&T (Signal & Telecommunication):** Point machines, electronic interlocking cabinets, SSDAC axle counters, KAVACH ATP transponders.

When these departments submit maintenance block requirements independently, severe operational problems emerge:
1. **Inter-departmental conflicts:** Engineering track work blocking TRD power isolation access.
2. **Train timetable clashes:** Blocks colliding with high-speed passenger corridors (e.g., Vande Bharat, Rajdhani).
3. **Resource deficits:** Work granted without certified staff gangs, heavy track machines (e.g. Plasser CSM-952, BCM-12, Tower Wagons), or critical permanent-way spares.
4. **Disruption chaos:** When a train delay or OHE breakdown occurs, manual re-planning creates extensive network-wide cascading delays and erases previously approved schedules.

**RailBlockSetu ("Setu" = The Bridge)** solves these challenges through an integrated decision-support platform that transforms fragmented requisitions into conflict-free, resource-validated, disruption-resilient maintenance block schedules.

> **Crucial Architecture Principle:** RailBlockSetu is a **decision-support platform**. Railway Operations Officers retain complete authority over reviewing, modifying, approving, and executing maintenance blocks.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   RailBlockSetu Frontend (React + TS + Tailwind)       │
│  - Interactive Command Center      - 5-Pillar Explainable Readiness    │
│  - Multi-Dept Requisition CRUD     - Weekly Corridor Gantt Timeline    │
│  - Decision-Support Review Center  - Disruption Simulator & Replanner  │
│  - Demo Role Switcher (RBAC)       - NetworkX Topology Visualizer      │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ REST APIs / JWT Auth
┌────────────────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend Core (Python 3.12)                   │
├────────────────────────────────┬───────────────────────────────────────┤
│ Optimization Engine            │ AI / Machine Learning Engine          │
│ • Google OR-Tools CP-SAT       │ • Scikit-Learn RandomForest + GB      │
│ • Multi-objective solver       │ • Priority Score (0-100) & Risk Tier  │
│ • Track non-overlap constraint │ • Feature importance explainability   │
│ • Machine & Gang capacity limits                                       │
│ • Headway curfew protection    │ Network Analysis Engine               │
│ • Pinned block preservation    │ • NetworkX Railway Graph (Nodes/Edges)│
├────────────────────────────────┴───────────────────────────────────────┤
│ Data Layer: SQLAlchemy ORM + SQLite (PostgreSQL compatible)            │
│ Models: Users, Sections, Resources, Requests, Blocks, Trains, Audits   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Role-Based Access Control (RBAC) & Demo Credentials

RailBlockSetu features one-click demo role switching directly in the navigation bar:

| Role | Username | Password | Persona | Operational Authority |
|---|---|---|---|---|
| **RAILWAY OPERATIONS OFFICER** | `ops_officer` | `ops123` | Amitabh Verma (Sr. DOM) | Reviews CP-SAT optimization results, authorizes/rejects proposed maintenance blocks, pins approved blocks, triggers disruption-aware replanning. |
| **DEPARTMENT OFFICER (Engg)** | `engg_officer` | `engg123` | Suresh Chandra (Sr. DEN/Track) | Submits track geometry tamping, ballast cleaning requisitions; audits Gang and BCM/CSM machine readiness. |
| **DEPARTMENT OFFICER (TRD)** | `trd_officer` | `trd123` | Deepak Khurana (DEE/TRD) | Submits 25kV OHE tensioning, cantilever, substation requisitions; tracks Tower Wagon allocations. |
| **DEPARTMENT OFFICER (S&T)** | `st_officer` | `st123` | Pooja Singhania (Sr. DSTE) | Submits Point Machine overhaul, KAVACH RFID calibration; validates interlocking disconnection notices. |
| **ADMINISTRATOR** | `admin` | `admin123` | Rajesh Sharma (COM) | User administration, section configuration, system parameter tuning, and 1-click database reset. |

---

## ⚡ Core Capabilities

### 1. Unified Maintenance Request Management
- Full lifecycle management (`DRAFT` ➔ `SUBMITTED` ➔ `VALIDATED` ➔ `OPTIMIZED` ➔ `APPROVED` ➔ `IN_PROGRESS` ➔ `COMPLETED` / `REJECTED`).
- Captures department, railway division, section, asset ID, duration, gang staff, heavy machinery, materials, safety protocols, and task dependencies.

### 2. AI-Assisted Priority Assessment (Scikit-Learn)
- Predicts continuous priority score ($10 - 99$) and categorical risk tier (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`).
- Factors: Asset Criticality, Urgency, Line Speed ($130-160$ km/h), Traffic Density, Degradation Index, Gross Million Tonnes (GMT), and Deadline proximity.
- Generates human-readable, explainable driver weights for railway officers.

### 3. 5-Pillar Explainable Block Readiness Audit
Before granting track possession, the engine executes an audit across 5 essential pillars:
1. **Staff Gang Readiness:** Required headcount vs available Gang personnel in depot.
2. **Machinery Allocation:** Specific heavy track machine (e.g. `CSM-952`, `TW-04`, `BCM-12`) confirmation.
3. **Materials Stock:** Critical permanent-way spares (60kg Sleepers, Contact Wire, Relays) availability.
4. **Traffic Window Feasibility:** Headway clearance without regulating passenger trains.
5. **Safety Isolation Clearance:** 25kV OHE power block permits and S&T disconnection notices.

### 4. Mathematical Block Optimization (Google OR-Tools CP-SAT)
- Multi-objective constraint solver enforcing:
  - Track possession non-overlap (no collision on same line/section).
  - Cumulative resource limits for heavy machinery ($capacity = 1$) and Gang squads.
  - Hard headway buffers around high-priority trains (Vande Bharat, Rajdhani).
  - DAG task dependency ordering with safety buffer.
- Produces conflict-free proposed block schedules.

### 5. Disruption-Aware Resilient Replanning
- When operational disruptions strike (e.g. freight hot-axle breakdown, OHE contact wire sag):
  1. Isolates collided blocks on the affected section.
  2. **Pins all unaffected and previously approved blocks** (`is_pinned = True`).
  3. Re-runs CP-SAT to reschedule only the impacted activities to the next safe window, protecting unaffected operations from schedule chaos.

---

## 🚀 Quickstart & Execution

### Prerequisites
- Node.js v18+ and npm
- Python 3.12+ (or via `uv`)

### 1. Backend Server
```powershell
cd backend
# Using the installed Python virtual environment:
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Interactive API Swagger Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### 2. Frontend Server
```powershell
cd frontend
npm run dev
```
- Open your browser at: **`http://localhost:5173/`**

---

## 🧪 Verification & Testing
- **Backend automated initialization:** `python backend/test_init.py` verifies SQLite DB creation, schema migration, ML model loading, and CP-SAT initial optimization.
- **Frontend TypeScript build:** `npm run build` in `frontend` compiles cleanly in $<2$ seconds.
- **Live Proxy:** Vite proxies all `/api/*` calls directly to the FastAPI server at `http://127.0.0.1:8000`.

---
*Developed for NOVEX 2026 Hackathon under the AI / Smart Infrastructure Category.*
