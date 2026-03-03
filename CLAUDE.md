# MedBase Backend - Agent Guide

## Your Role

You are the Backend Agent for MedBase, a clinic management system. Your responsibility is to build and maintain the FastAPI backend that powers this application.

---

## Tech Stack

- **Frontend**: Angular
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic, Pydantic, Conda
- **Database**: PostgreSQL (Amazon RDS)
- **File Storage**: Amazon Lightsail Bucket (S3-compatible)
- **Containerization**: Docker (backend)
- **Deployment**: AWS
- **Dev API**: `https://dev-api.medbaseclinic.com/api/v1`

---

## Project Structure

```
MedBase-API/
├── docs/                    # Documentation (read-only, except Postman collection)
│   ├── database.dbml        # Database schema
│   ├── endpoints.md         # API endpoint specifications
│   ├── pages.md             # Frontend pages (for context)
│   ├── plan.md              # Development plan and phases
│   └── MedBase API.postman_collection.json  # Postman collection (edit here, sync to Planner + WEB)
├── BE.PROGRESS.md           # Your progress tracker (update this!)
└── CLAUDE.md                # This file
```

---

## How to Work

### 1. Check Your Progress
Always start by reading `BE.PROGRESS.md` to see:
- Current phase
- Completed features
- Feature in progress

### 2. Follow the Plan
Work through features in order as defined in `docs/plan.md`. Do not skip ahead or work on multiple features simultaneously.

### 3. For Each Feature
Follow this order strictly:
1. **Endpoints** — Implement the API endpoints
2. **Test** — Write and run tests to verify it works
3. **Postman** — Create/update Postman request examples
4. **Dummy Data** — Add seed script in `scripts/` folder
5. **Push** — Run all tests again, push to GitHub only after all tests pass

### 4. Update Progress
Before finishing any feature, update `BE.PROGRESS.md`:
- Move feature from "In Progress" to "Completed"
- Add completion date and any notes

### 5. PR Workflow
- Each phase requires a Pull Request (PR)
- Open a PR when all features in the phase are complete
- Phase ends only when the PR is merged
- PR will be merged after owner approval

---

## Code Style

- **All imports at the top of the file** — no inline or mid-file imports

---

## Backend Standards

### Architecture (4-Layer Pattern)
- `router/` — Endpoints, auth, validation
- `service/` — Business logic
- `model/` — SQLAlchemy ORM models
- `schema/` — Pydantic input/output validation

### Layer Separation
- **No model or query code in routers** — routers handle HTTP concerns only (request/response, auth, validation). All database queries and model operations belong in the service layer.

### Project Structure
- `main.py` at root
- General app utilities in `utility/` folder

### Database Rules
- All tables need: `created_by`, `created_at`, `updated_by`, `updated_at`, `is_deleted`
- Use soft deletes (`is_deleted = True`)
- Follow schema in `docs/database.dbml`

| Column | Required | Notes |
|--------|----------|-------|
| `created_by` | Yes | Set on creation |
| `created_at` | Yes | Set on creation |
| `updated_by` | Yes | Set on creation, updated on edit |
| `updated_at` | Yes | Set on creation, updated on edit |
| `is_deleted` | Yes | Soft delete flag |
| `is_active` | Optional | For resources that can be deactivated (e.g., doctors) |

### Unique Names
- Entity names should be unique across the system
- Add unique constraints on name fields in models
- Validate uniqueness in the service layer when creating or updating

### Third Parties
- A `third_parties` table serves as the base identity record for all persons/entities
- Every user, doctor, patient, and partner has a corresponding `third_party` record
- When creating a doctor, patient, or partner: if no `third_party_id` is provided, the system auto-creates one; if provided, it links to the existing one
- `inventory_transactions` links to `third_party_id`:
  - **Donations**: must point to a donor (partner with `partner_type` of `donor` or `both`)
  - **Prescriptions**: must point to a doctor
  - **Other types** (purchase, loss, breakage, expiration, destruction): set to the logged-in user's `third_party_id`

### Business Rules
- Only doctors can make prescriptions
- Only donors (partners with `partner_type` of `donor` or `both`) can make donations
- For non-donation/non-prescription transactions, the system automatically uses the current user's `third_party_id`

### SQLAlchemy
- NO `selectinload()` or lazy loading
- Always use explicit `outerjoin()` + `contains_eager()`

```python
result = await self.db.execute(
    select(Donation)
    .outerjoin(
        DonationMedicineItem,
        and_(Donation.id == DonationMedicineItem.donation_id,
             DonationMedicineItem.is_deleted == False)
    )
    .options(contains_eager(Donation.medicine_items))
    .where(Donation.id == donation_id, Donation.is_deleted == False)
)
```

### Enums
- Fields with limited options stored as `String` in the database model
- Create a corresponding `StrEnum` class for allowed values
- Each enum defined in its relative resource's file (e.g., `AppointmentType` in `appointment.py`)

```python
from enum import StrEnum

class AppointmentType(StrEnum):
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"

class Appointment(Base):
    __tablename__ = "appointments"
    type = Column(String, nullable=False)  # Stores enum values as strings
```

### API Endpoints
- Pagination: `page` and `size` parameters
- Sorting: sortable fields as specified
- Filtering: exact match filters
- Searching: text search where applicable
- **Count queries**: In `get_all` functions, derive the count query from the main query (reuse it with `.with_only_columns()`) instead of building a separate count query with duplicated filters

### Authentication
- JWT Bearer tokens
- 1-hour expiry

### Docker & Environment
- Base image: Miniconda slim
- Dependency files: `environment.yml` + `requirements.txt`
- Single Docker setup with hot reload for development
- Database hosted on Amazon RDS (no local PostgreSQL containers)
- File storage via Amazon Lightsail Bucket (S3-compatible, using `aioboto3`)
- All environment variables loaded from `.env` (`DATABASE_URL`, `TEST_DATABASE_URL`, `LIGHTSAIL_*`, etc.)
- Makefile for common commands (build, run, test, migrate, etc.)

### Environment Variables
- Reference `.env.example` in the project root to see required environment variables
- If you are missing any environment variables during development, **ask the user for them** — do not guess or hardcode values

### Database Migrations
- **Always create a new migration** when database changes are needed — never modify existing migrations
- **Autogenerate first, then manually edit** — use `make migrate-create` to autogenerate as much as possible, then manually adjust the migration if custom logic is needed

### Testing
- Separate test database on Amazon RDS (`TEST_DATABASE_URL` from `.env`)
- Clean/empty before each test run
- Endpoint tests: validate API responses AND query the database directly to verify data

### Logging
- Python standard `logging` module
- Middleware logs every request (method, URL, body) and response (status, duration)
- Sensitive fields (`password`, `access_token`) are masked in body logs
- Router layer: `info` for actions and outcomes, `warning` for failures (not found, duplicates, auth failures)
- Service layer: `info` for writes (create, update, delete), `debug` for reads and auth details
- Logger names follow `medbase.<layer>.<module>` convention (e.g. `medbase.router.auth`)
- Log level controlled by `DEBUG` env var (`DEBUG=true` → DEBUG level, otherwise INFO)

### API Documentation
- **ReDoc**: Browsable API reference at `/redoc` (auto-generated by FastAPI)
- **Swagger UI**: Interactive testing at `/docs`
- **Postman**: Collection with request examples for each endpoint

---

## CLI Tools

- **Always use CLI tools to autogenerate files when possible** (e.g. `alembic` for migrations, `make` commands, etc.). Only write files manually when no CLI tool can do it for you.

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/database.dbml` | Database schema (import to dbdiagram.io to visualize) |
| `docs/endpoints.md` | All API endpoints with filters, validations, notes |
| `docs/plan.md` | Development phases and feature sequence |
| `docs/pages.md` | Frontend page layouts and functionality specs |
| `docs/MedBase API.postman_collection.json` | Postman collection with request examples |

---

## Development Flow

**Approach**
- Features developed independently in sequential order
- Frontend and Backend developed separately
- Backend order per feature: Endpoints → Tests → Postman → Dummy Data → Push

**Progress Tracking**
- `BE.PROGRESS.md` — backend progress
- `FE.PROGRESS.md` — frontend progress
- `plan.md` — feature list and development sequence
- **Rule**: Update progress file before finishing each feature

**Documentation Files**
- `database.dbml` — database schema (Backend)
- `endpoints.md` — API endpoints list (Backend, copied to Frontend)
- `MedBase API.postman_collection.json` — Postman collection (originates in API, synced to Planner + Frontend)
- `openapi.json` — OpenAPI spec (generated from the running API, synced to Frontend)
- `pages.md` — page layouts and functionality (Frontend)
- `README.md` — project description, setup instructions, and how to run (in each repo root)

**Syncing to Frontend**
- After any BE changes that affect endpoints, sync these files to `MedBase-WEB/docs/`:
  1. `MedBase API.postman_collection.json` — copy from `MedBase-API/docs/`
  2. `openapi.json` — fetch from the running dev API at `https://dev-api.medbaseclinic.com/api/v1/openapi.json` and save to `MedBase-WEB/docs/openapi.json`

**PR Workflow**
- Each phase requires a Pull Request (PR)
- Open a PR when all features in the phase are complete
- Phase ends only when the PR is merged
- PR will be merged after owner approval
- **Always run tests before pushing to GitHub** — never push code that fails tests

---

## User Stories

### Inventory Management
- Define inventory types: Medicines, Equipment, Medical Devices
- Track inventory with a simple inventory system
- Categorize inventory items by type
- Record inventory transactions (prescribing, loss, breakage, destruction, expiration, etc.)
- Record inventory purchases

### Patient Management
- Store patient data
- Save patient documents

### Appointments & Medical Records
- Store appointments and the medical record for each appointment
- Save vital signs for each appointment
- Appointment types: scheduled, walk-in
- Appointment location: internal (at clinic) or external (with partner)
- Appointment flow page: begin → vitals + medical record (optional) → treatment (optional) → complete
  - Usually: vitals + medical record, treatment optional
  - Sometimes: treatment only (no vitals/record)

### Prescriptions
- Prescriptions are handled as inventory transactions with `transaction_type = prescription`
- Only doctors can make prescriptions (third_party_id must point to a doctor)
- Prescribing automatically decreases inventory

### Partners
- Track partners (NGO, organization, individual, hospital, medical center)
- Partner types: donor, referral, or both
- **Donations**: Handled as inventory transactions with type `donation` — only donors can make donations
- **Treatments**: Track treatments/operations sent to referral partners

### Doctors
- Track doctors (clinic staff, external, or provided by donors)

### Users & Authentication
- User system for data entry staff
- Admin role to manage users (CRUD)
- Each user has a `third_party` record used to track their involvement in transactions

### Statistics
- Summary statistics: inventory, appointments, transactions, partners

### Treatments
- Track treatments provided to patients through external partners

---

## Important Rules

1. **Never skip features** — Complete in order
2. **Always update progress** — Before finishing each feature
3. **Follow the docs** — They are your source of truth
4. **Test everything** — No feature is complete without tests
5. **Document in Postman** — Create requests for every endpoint
6. **Develop → Test → Postman → Dummy Data → Push** — Follow this order strictly for every feature
7. **CLAUDE.md changes must be applied across all 3 repos** — When adding or updating any rule, setting, or section in any CLAUDE.md, apply the change to all three: `Planner/CLAUDE.md`, `MedBase-API/CLAUDE.md`, and `MedBase-WEB/CLAUDE.md`
