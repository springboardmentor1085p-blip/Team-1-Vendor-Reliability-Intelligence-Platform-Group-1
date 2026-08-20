# VendorIQ — Vendor Reliability Intelligence & Procurement Risk Management Platform
## 🚀 Live Deployment

[Visit VendorIQ](https://vendoriq-rho.vercel.app/)

VendorIQ is an enterprise-grade vendor reliability intelligence and procurement risk management system. This application supports vendor registration directory auditing, automated procurement workflows (requisitions to invoice settlement), transparent weighted reliability score calculation, legal contract expiration warning triggers, and analytical dashboard panels.

---

## Technical Stack

* **Frontend**: Angular 16, TypeScript, Angular Material, Bootstrap CSS, RxJS, Chart.js.
* **Backend**: Python 3.12, FastAPI modular monolith framework, SQLAlchemy 2.0 ORM, Pydantic schemas, native `bcrypt` cryptography hashing, PyJWT authentication tokens.
* **Libraries**: `openpyxl` (for formatted Excel spreadsheet creation), `reportlab` (for land-scaped PDF document printing).
* **Database**: PostgreSQL 15+, Alembic (for database schema migration tracking).
* **DevOps**: Docker, Docker Compose, Nginx.

---

## Audited Core Features

### 1. Authentication & Role-Based Access Control (RBAC)
* **Secure Auth**: Custom registration and credentials sign-in using direct `bcrypt` hashing, bypassing unmaintained passlib-bcrypt length limit bugs. Token sessions validated via JWT Bearer injection.
* **RBAC Controls**: Strict role restrictions checked on every API transaction for the 6 standard user classes: Administrator, Supply Chain Manager, Procurement Manager, Finance Officer, Auditor, and Vendor.
* **Guards & Interceptor**: Route security handled by Angular's `AuthGuard` and automated JWT token headers attached by `JwtInterceptor`.
* **Password Reset**: **PASS — Self-service reset implemented with secure time-limited token.**

### 2. Supplier & Procurement Lifecycle Workflows
* **Vendor Directory**: Listing, categories, contact cards, and search filtering.
* **Vendor Status Validation**: SCM/Admin approving and rejecting vendor profiles (`Active` / `Inactive` / `Rejected`).
* **Procurement Requisitions**: Requisitions created with priority and value, transited (Pending ➔ Approved / Rejected) by SCM.
* **Purchase Orders**: Automated unique order number generator (`PO-YYYYMMDD-XXXX`). Orders progress through state machine (`Pending Approval` ➔ `Approved` ➔ `Ordered` ➔ `Delivered` ➔ `Completed`).
* **Finance Invoice Control**: Invoicing states (Unpaid, Invoiced, Paid) modifiable by Finance.

### 3. Compliance & Risk Analytics
* **Contract Expiry Warn Engine**: Contracts automatically scanned on load. Agreement expiries (<30 days left) trigger dynamic state transitions (`Expiring Soon` / `Expired`) and post warning notices in the notifications database.
* **Reliability Weighted Score Calculation**:
  $$\text{Reliability} = 25\%\text{ Delivery} + 20\%\text{ Quality} + 15\%\text{ Communication} + 15\%\text{ Compliance} + 10\%\text{ Purchase History} + 15\%\text{ Issue Resolution}$$
  * Timeliness subtracts 10 points per delay day.
  * Purchase history evaluates completed PO counts (0 orders ➔ 60pts, 1-3 orders ➔ 80pts, 4+ orders ➔ 100pts).
  * Automated risk level classifications: LOW (80-100), MEDIUM (60-79), HIGH (40-59), and CRITICAL (0-39) risks with strategic recommendations.
* **Analytical Dashboard**: Aggregates total metrics and renders 5 interactive Chart.js canvases (spending monthly, PO status counts, vendor scores, risk distributions, timeliness).
* **Report Exports**: Downloads data tables in three distinct formats:
  * **CSV**: Raw database table dumps in comma-separated values.
  * **Excel (XLSX)**: Format-styled spreadsheets with auto-fit column dimension widths generated using `openpyxl`.
  * **PDF**: Portrait/landscape page-wrapped documents with alternating row fills and header formatting using `reportlab`.

### 4. Secure File Sharing (Attachments)
* **Status**: **PASS — Authorized communication file upload/download implemented with validation and 10 MB limit.**
* **Details**: Users can attach documents when composing communication queries.
  * **Allowed extensions**: `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX`, `CSV`, `PNG`, `JPG`, `JPEG`, `TXT`.
  * **Size limit**: Max 10 MB file uploads.
  * **Security**: Files are stored with dynamically generated safe unique server UUID names to prevent directory traversal attacks. Downloads are checked against user roles, restricting access to authorized participants (sender, recipient, admin, auditor).

### 5. Email & SMS Notifications Gateways
* **Status**: **PASS — SMTP email and SMS provider integration implemented with environment-based configuration and graceful fallback.**
* **Details**: Important system milestones automatically dispatch email templates and SMS text messages:
  - Vendor Registration Status Update (Approved / Rejected)
  - Procurement Requisitions (Approved / Rejected)
  - Delivery Delays Alert (PO Delayed Warnings)
  - Contract Expiring Alerts
  - High-Risk Vendor Warnings
  - Password Reset Token dispatches via email
  - Gracefully falls back to mock logging if SMTP/SMS settings are not defined.

---

## Architectural Layout

```
├── backend/
│   ├── alembic/               # Alembic database migration scripts
│   │   ├── env.py             # Configures migration lookup paths dynamically
│   │   └── versions/          # Version migration files (d94f089501de_add_phone_and_attachments.py)
│   ├── app/
│   │   ├── models.py          # SQLAlchemy ORM models (Users, Vendors, Contracts, etc.)
│   │   ├── schemas.py         # Pydantic validation schemas
│   │   ├── database.py        # Database connection config
│   │   ├── config.py          # Settings loader
│   │   ├── seeds.py           # Demo database seeder CLI
│   │   ├── main.py            # FastAPI entry point
│   │   ├── routes/            # Route controllers (/auth, /vendors, /reports, etc.)
│   │   ├── services/          # Email notifications and SMS providers
│   │   │   ├── email_service.py
│   │   │   └── sms_service.py
│   │   └── utils/             # RBAC controls and bcrypt helper functions
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py        # Pytest integration suite (15 tests)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # Angular components (login, forgot-password, reset-password, dashboard, reports, etc.)
│   │   │   ├── guards/        # Routing authorization guards
│   │   │   ├── interceptors/  # JWT Interceptors
│   │   │   └── services/      # Backend API services
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env.example
├── PROJECT_MILESTONE_CHECKLIST.md
└── EVALUATION_MATRIX.md
```

---

## Quick Start — Local Running

### 1. Database Configuration
Ensure a local PostgreSQL instance is running on your system (default port `5432`). Create your database and configure the root `.env` (a copy of `.env.example`) to match your local credentials.

Copy the `.env` settings into your backend folder:
```bash
cp .env backend/.env
```

### 2. Run Database Migrations
Initialize database tables using Alembic migrations:
```bash
cd backend
python -m alembic upgrade head
```

### 3. Seed Database
Populate database tables with mock datasets:
```bash
cd backend
python -m app.seeds
```

### 4. Run Backend Server
```bash
cd backend
uvicorn app.main:app --reload
```
API endpoints will run at `http://localhost:8000`. Swagger documentation is accessible at `http://localhost:8000/docs`.

### 5. Run Frontend Portal
```bash
cd frontend
npm install
npm run start
```
Web portal will run at `http://localhost:4200`.

---

## Running Integration Tests

To run the full backend testing suite:
```bash
cd backend
python -m pytest
```
All 15 tests (covering JWT auth, RBAC blocks, self-service password reset, file uploads, download permissions, and notification fallbacks) should pass successfully.

---

## Demo Accounts Credentials
The seeder loads these demo accounts with password `password123`:

* **Administrator**: `admin`
* **Supply Chain Manager**: `supplychain`
* **Procurement Manager**: `procurement`
* **Finance Officer**: `finance`
* **Auditor**: `auditor`
* **Vendor (Apex Materials)**: `vendor_apex`
* **Vendor (Titan Equipment)**: `vendor_titan`

---

## Documented Integration Notes
1. **Password Reset**: PASS — Self-service password reset implemented with secure time-limited tokens and tested.
2. **Email/SMS**: PASS — SMTP email and SMS/Twilio integrations implemented with environment-based configuration, graceful fallback, and tests. Real external delivery requires valid provider credentials.
3. **File Sharing**: PASS — Authorized communication file upload/download implemented with file-type validation, 10 MB limit, safe filenames, metadata, and access control.
4. **Docker**: PARTIAL — Docker configuration is complete, but runtime was not locally tested because Docker is unavailable.
