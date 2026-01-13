# CLAUDE.md - AI Assistant Context Document

## Project Overview

**MedBase-API** is a FastAPI backend for a **free clinic management system**. This clinic:
- Does **not charge patients** (no billing/invoicing/payments)
- Relies heavily on **donations** (medicine, equipment, medical devices)
- Does **not have an in-house laboratory** (patients bring external lab results as documents)
- All system users are **admins with full access** (no role-based permissions)

## Technology Stack

- **Backend Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 (async with asyncpg)
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Containerization**: Docker & Docker Compose

## Development Setup

Use `make help` to see all available commands.

### Option A: Docker (Recommended)
```bash
make docker-up      # Start API + PostgreSQL
make docker-logs    # View logs
make docker-down    # Stop services
make docker-clean   # Remove everything (containers, images, volumes)
```

### Option B: Local with Conda
```bash
make install        # Create/update conda environment
conda activate medbase-api
cp env.example .env # Configure environment
make db-up          # Start PostgreSQL container
make migrate        # Run database migrations
make run            # Start API server
```

### Connect to Production Database
```bash
cp env.prod.example .env.prod   # Create prod env file
# Edit .env.prod with production DATABASE_URL
make run-prod                    # Run with production DB
```

### Make Commands Reference
| Command | Description |
|---------|-------------|
| `make run` | Run API locally (uses `.env`) |
| `make run-prod` | Run with production DB (uses `.env.prod`) |
| `make db-up` / `db-down` | Start/stop local PostgreSQL |
| `make docker-up` / `docker-down` | Start/stop all Docker services |
| `make docker-build` | Build Docker image |
| `make docker-clean` | Remove all containers, images, volumes |
| `make migrate` | Run database migrations |
| `make migrate-create msg="..."` | Create new migration |

**Note**: `requirements.txt` is for Docker (pip), `environment.yaml` is for local (Conda).

## What Has Been Done

### Database Schema (`sql scripts/medbase_initial.sql`)

A comprehensive PostgreSQL schema has been created with the following structure:

#### Core Enums
| Enum | Values |
|------|--------|
| `gender_type` | male, female |
| `blood_type` | A+, A-, B+, B-, AB+, AB-, O+, O-, unknown |
| `appointment_status` | scheduled, completed, cancelled, no_show, rescheduled |
| `appointment_type` | consultation, follow_up, emergency, checkup |
| `prescription_status` | pending, dispensed, cancelled |
| `marital_status` | single, married, divorced, widowed |
| `donor_type` | individual, organization, government, ngo, pharmaceutical_company |
| `donation_type` | medicine, equipment, medical_device, mixed |
| `equipment_condition` | new, excellent, good, fair, needs_repair, out_of_service |
| `document_type` | lab_result, imaging, prescription, referral, consent_form, insurance_document, identification, medical_history, discharge_summary, other |
| `severity` | mild, moderate, severe, life_threatening |
| `dosage_form` | tablet, capsule, syrup, injection, cream, ointment, drops, inhaler, patch, suppository, powder, solution, suspension, gel, spray, other |
| `inventory_transaction_type` | perscribed, donated, expired, damaged, returned, purchased, lost, stolen |
| `reference_type` | prescription, donation, adjustment, transfer, disposal |

#### Tables Created

**User Management:**
- `users` - System users (all admins, simplified fields)

**Patient Management:**
- `patients` - Patient demographics and contact info
- `patient_allergies` - Patient allergy records with severity
- `patient_medical_history` - Past/current medical conditions with ICD codes
- `patient_documents` - Uploaded files including external lab results

**Clinical:**
- `doctors` - Doctor info, can optionally be linked to a donor
- `appointments` - Patient appointments with doctors
- `vital_signs` - Patient vital measurements
- `medical_records` - Visit/encounter documentation
- `prescriptions` - Medicine prescriptions
- `prescription_items` - Individual items in a prescription
- `prescribed_devices` - Medical devices issued to patients

**Inventory - Medicines:**
- `medicine_categories` - Hierarchical medicine categories
- `medicines` - Medicine catalog
- `medicine_inventory` - Current stock levels
- `medicine_expiry` - Batch-level expiry tracking

**Inventory - Medical Devices (Prescribable):**
- `medical_device_categories` - Device categories
- `medical_devices` - Devices like wheelchairs, walkers, braces
- `medical_device_inventory` - Device stock with condition tracking

**Inventory - Equipment (Clinic Use):**
- `equipment_categories` - Equipment categories
- `equipment` - Clinic equipment (not prescribed to patients)

**Donations:**
- `donors` - Donor organizations/individuals
- `donations` - Donation records
- `donation_medicine_items` - Medicine donation details
- `donation_equipment_items` - Equipment donation details
- `donation_medical_device_items` - Medical device donation details

**System:**
- `inventory_transactions` - Track all inventory movements
- `system_settings` - Configurable system settings

#### Key Design Decisions

1. **Audit Columns**: All tables have `id` (UUID), `created_at` (TIMESTAMP), `created_by` (VARCHAR - username), `updated_at`, `updated_by`

2. **No Billing**: Removed all invoice, payment, and pricing fields (except for tracking donation values)

3. **No Lab**: Removed lab_tests, lab_orders, lab_results tables. External lab results stored as patient_documents with `document_type = 'lab_result'`

4. **No Roles**: Removed user_role enum. All users have full admin access.

5. **No Complex Scheduling**: Removed departments, rooms, doctor_schedules tables

6. **Doctors from Donors**: Doctors can optionally be sponsored/provided by a donor organization

7. **Medical Devices vs Equipment**: 
   - `medical_devices` = Prescribable to patients (wheelchairs, braces)
   - `equipment` = Clinic use only (monitors, surgical tools)

## User's Working Style

Based on our interaction:
- Prefers **simplified schemas** - removes unnecessary columns
- Values **enums over VARCHAR** for constrained values
- Iterative refinement - makes many small changes
- Focuses on **practical needs** for a free clinic context
- Removes features not needed (maintenance logs, audit logs, notifications, etc.)

## What Has Been Implemented

### ✅ Completed

1. **FastAPI Project Setup**
   - Project structure with app/, routers/, models/, schemas/, services/, utils/
   - `requirements.txt` for Docker, `environment.yaml` for Conda
   - Async SQLAlchemy database connection
   - Alembic configured for migrations
   - Docker & Docker Compose setup

2. **Database Migrations**
   - Initial migration created with full schema
   - **Default admin user**: username `admin`, password `admin`
   - Run `make migrate` to apply

3. **Service Layer Architecture**
   - **Routers (Controllers)**: Handle HTTP, auth, validation, responses
   - **Services**: Handle business logic and all DB operations

4. **Authentication & Users**
   - JWT token-based authentication
   - Password hashing with bcrypt
   - Login endpoint (`POST /api/v1/auth/login`)
   - User CRUD (create, read, update, delete)
   - **No public registration** - users created by authenticated users only

5. **User Endpoints**
   - `POST /api/v1/users/` - Create user (requires auth)
   - `GET /api/v1/users/me` - Current user profile
   - `PATCH /api/v1/users/me` - Update own profile
   - `POST /api/v1/users/me/change-password` - Change password
   - `GET /api/v1/users/` - List all users (paginated)
   - `GET /api/v1/users/{id}` - Get user by ID
   - `PATCH /api/v1/users/{id}` - Update user
   - `DELETE /api/v1/users/{id}` - Delete user

### 🔜 Next Steps (Priority Order)

1. **Patients CRUD** - Patient management endpoints
2. **Doctors CRUD** - Doctor management
3. **Appointments CRUD** - Scheduling
4. **Prescriptions & Items** - Medicine/device prescriptions
5. **Medicine & Inventory** - Stock management
6. **Medical Devices** - Device catalog & inventory
7. **Donations** - Donor and donation tracking
8. **Document uploads** - Patient document handling

### Future Considerations

- File upload handling for patient documents
- Reporting/analytics endpoints
- Search/filter functionality
- Bulk operations for inventory
- Export functionality (CSV, PDF)

## Current File Structure

```
MedBase-API/
├── .cursorrules           # AI assistant rules
├── CLAUDE.md              # This file
├── README.md
├── Makefile               # Development commands (make help)
├── requirements.txt       # Python deps for Docker (pip)
├── environment.yaml       # Python deps for local (Conda)
├── env.example            # Local environment template
├── env.prod.example       # Production environment template
├── Dockerfile             # API container definition
├── docker-compose.yml     # Docker services (API + PostgreSQL)
├── .dockerignore
├── alembic.ini            # Alembic configuration
├── sql scripts/
│   └── medbase_initial.sql  # Full database schema
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Settings from environment
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py        # User SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py        # Auth schemas (Token, TokenData)
│   │   └── user.py        # User Pydantic schemas
│   ├── routers/           # Thin controllers - HTTP & validation only
│   │   ├── __init__.py
│   │   ├── auth.py        # Login endpoint
│   │   └── users.py       # User CRUD endpoints
│   ├── services/          # Business logic & DB operations
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Authentication logic
│   │   └── user_service.py   # User CRUD operations
│   └── utils/
│       ├── __init__.py
│       ├── database.py    # DB engine, session, Base class
│       ├── dependencies.py # get_current_user dependency
│       └── security.py    # JWT & password utilities
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/          # Migration files
└── tests/                 # (empty - for tests)
```

## Service Layer Pattern

The project follows a **service layer architecture**:

### Routers (Controllers)
- Handle HTTP request/response
- Authentication via dependencies
- Input validation (Pydantic)
- Raise HTTPException for errors
- **DO NOT** contain business logic or direct DB queries

### Services
- All business logic
- All database operations (queries, inserts, updates, deletes)
- Return domain objects or None
- **DO NOT** raise HTTPException (leave that to routers)
- **DO NOT** create methods that aren't used - only add what routers need

### Example Flow
```
Request → Router (auth + validation) → Service (business logic + DB) → Response
```

## Testing Guidelines

### Test Philosophy
- **Never modify production code to accommodate tests** - tests should test the code as-is
- Only modify production code if there is an actual bug discovered during testing
- Tests should be self-contained and not require special handling in the application

### Test Structure
- Tests are in the `tests/` directory
- Use `pytest` with `pytest-asyncio` for async tests
- Test database: `medbase_clinic_test` (PostgreSQL)
- Tests create data via API calls, not direct database manipulation
- Use fixtures for common setup (client, auth headers, test users)

### Running Tests
```bash
make test  # Runs tests and saves results to tests/test_results.log
```

### Test Fixtures
- `client`: AsyncClient for making API requests
- `admin_headers`: Auth headers for the default admin user
- `test_user`: Creates a test user via API and returns user dict with password
- `auth_headers`: Auth headers for the test user

## Important Notes for AI Assistants

1. **This is a FREE clinic** - never add billing/payment features
2. **No lab functionality** - lab results are document uploads only
3. **All users are admins** - no role-based access control
4. **No public registration** - users are created by other authenticated users
5. **Default admin user** - username `admin`, password `admin` (created by initial migration)
6. **Donations are critical** - medicine, equipment, and medical devices can all come from donors
7. **Medical devices are prescribable** - unlike equipment which is for clinic use
8. **Keep it simple** - user prefers minimal, practical implementations
9. **Service layer pattern** - routers handle HTTP/validation, services handle business logic/DB
10. **Utils folder** - database.py, dependencies.py, and security.py are in `app/utils/`
11. **Two dependency files** - `requirements.txt` for Docker, `environment.yaml` for local Conda dev
12. **Keep docs in sync** - When updating `.cursorrules`, also update `CLAUDE.md`
13. **Test philosophy** - Never modify production code to accommodate tests; only fix actual bugs

