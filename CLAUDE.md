# MedBase Backend - Agent Guide

## Your Role

You are the Backend Agent for MedBase, a clinic management system for small medical clinics. Your responsibility is to maintain and extend the FastAPI backend that powers this application.

**This guide covers only the backend repo (`MedBase-API`).** You do not need to worry about the other repos.

---

## Project Context

MedBase is split across three directories:

| Directory | Purpose | Your concern? |
|-----------|---------|---------------|
| `MedBase-API/` | FastAPI backend (this repo) | **Yes — this is your repo** |
| `MedBase-WEB/` | Angular frontend | No — handled by the Frontend Agent |
| `Planner/` | Shared docs (database.dbml, pages.md, Postman collection) | No |

Each repo has its own `CLAUDE.md`. You only need to follow this one.

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Language |
| FastAPI | 0.109.2 | Web framework |
| SQLAlchemy | 2.0.25 (async) | ORM |
| Alembic | 1.13.1 | Database migrations |
| Pydantic | 2.6.1 | Request/response validation |
| PostgreSQL | (Amazon RDS) | Database |
| python-jose | 3.3.0 | JWT authentication |
| passlib + bcrypt | 1.7.4 / 4.0.1 | Password hashing |
| aioboto3 | 13.4.0 | S3-compatible file storage (Lightsail) |
| slowapi | 0.1.9 | Rate limiting |
| pytest | 8.0.0 | Testing |
| pytest-asyncio | 0.23.5 | Async test support |
| httpx | 0.26.0 | Test HTTP client |
| Docker + Conda | — | Containerization & environment |

- **Dev API**: `https://dev-api.medbaseclinic.com/api/v1`
- **OpenAPI Spec**: `https://dev-api.medbaseclinic.com/openapi.json`

---

## Project Structure

```
MedBase-API/
├── main.py                 # Application entry point (FastAPI app, middleware, CORS, routes)
├── app/
│   ├── model/              # 22 SQLAlchemy ORM models
│   ├── router/             # 19 route handlers (HTTP endpoints)
│   ├── schema/             # 22 Pydantic request/response schemas
│   ├── service/            # 19 business logic services
│   └── utility/            # 9 utility modules (auth, config, database, security, logging, rate_limit, storage, token_blacklist, sorting)
├── alembic/                # Database migrations (4 migration files)
│   ├── versions/           # Migration scripts
│   └── env.py              # Alembic async configuration
├── docs/                   # Documentation and Postman collection
│   ├── database.dbml       # Database schema (for dbdiagram.io)
│   ├── pages.md            # Frontend pages (for context)
│   └── MedBase API.postman_collection.json  # Postman collection
├── scripts/                # Setup/seed/populate scripts
│   ├── seed.py             # Creates default admin user
│   ├── populate_dummy_data.py  # Fills DB with test data
│   └── reset_db.py         # Clears database
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures (db_session, client, tokens)
│   └── endpoint/           # 15+ test files (one per resource)
├── docker-compose.yml      # Local dev Docker setup
├── Dockerfile              # Container image (Miniconda base)
├── Makefile                # Common commands
├── environment.yml         # Conda environment
├── requirements.txt        # Python dependencies
└── CLAUDE.md               # This file
```

---

## Architecture

### 4-Layer Pattern

```
Request → Router → Service → Model/DB
                ↕
              Schema (validation)
```

1. **Router** (`app/router/`) — HTTP endpoints, auth guards, request validation, response formatting
2. **Service** (`app/service/`) — Business logic, database queries, validation rules
3. **Model** (`app/model/`) — SQLAlchemy ORM models (table definitions)
4. **Schema** (`app/schema/`) — Pydantic request/response schemas

### Layer Rules

- **No model or query code in routers** — routers handle HTTP concerns only (request/response, auth). All database queries and model operations belong in the service layer.
- **Always use Pydantic models for router response types** — never use `dict` or other raw types in `response_model`. Every endpoint must have a dedicated Pydantic schema.
- **Services receive `db: AsyncSession`** — injected via FastAPI dependency `get_db()`.
- **Services return model objects or raise `ValueError`** — routers catch `ValueError` and convert to `HTTPException`.
- **Service instantiation**: Create service instances inside each endpoint function: `service = SomeService(db)`.
- **No cross-service imports in routers** — if validation needs another entity (e.g., checking patient exists), do it through the primary service or instantiate the needed service separately.

---

## Database Schema & Models

### 22 Tables

**Core Identity:**
- `third_parties` — Base identity for all persons/entities (code, name, phone, email, is_active)
- `users` — Login accounts (username, password_hash, role, third_party_id FK)

**Inventory:**
- `items` — Parent table for all inventory item types (item_type: medicine/equipment/medical_device, name)
- `medicines` — (code, name, category_id FK, description, unit, is_active, item_id FK)
- `equipment` — (code, name, category_id FK, condition, is_active, item_id FK)
- `medical_devices` — (code, name, category_id FK, serial_number, is_active, item_id FK)
- `medicine_categories`, `equipment_categories`, `medical_device_categories` — (name, description, is_active)
- `inventory` — (item_id FK, quantity)

**Transactions:**
- `inventory_transactions` — (transaction_type, third_party_id FK, appointment_id FK, transaction_date, notes)
- `inventory_transaction_items` — (transaction_id FK, item_id FK, quantity)

**Patient Management:**
- `patients` — (third_party_id FK, date_of_birth, gender, address, emergency_contact, is_active)
- `patient_documents` — (patient_id FK, file_key, document_type, is_active)
- `doctors` — (third_party_id FK, specialization, type, partner_id FK, is_active)
- `partners` — (third_party_id FK, partner_type, organization_type, contact_person, address, is_active)

**Appointments & Records:**
- `appointments` — (code, patient_id FK, doctor_id FK, partner_id FK, appointment_date, status, type, location, notes)
- `vital_signs` — (appointment_id FK, blood_pressure_systolic/diastolic, heart_rate, temperature, respiratory_rate, weight, height, notes)
- `medical_records` — (appointment_id FK, chief_complaint, diagnosis, treatment_notes, follow_up_date)
- `treatments` — (patient_id FK, appointment_id FK, partner_id FK, treatment_type, description, treatment_date, status, cost, notes)

### Database Rules

| Column | Required | Notes |
|--------|----------|-------|
| `id` | Yes | Auto-increment primary key |
| `created_by` | Yes | Set on creation (user ID) |
| `created_at` | Yes | Set on creation (timestamp) |
| `updated_by` | Yes | Set on creation, updated on edit |
| `updated_at` | Yes | Set on creation, updated on edit |
| `is_deleted` | Yes | Soft delete flag (default: False) |
| `is_active` | Optional | For resources that can be deactivated |

### Key Design Patterns

- **Soft deletes**: All records use `is_deleted = True` instead of actual deletion
- **Third Party base identity**: Every user, doctor, patient, and partner has a corresponding `third_party` record. When creating any of these, if no `third_party_id` is provided, one is auto-created.
- **Item parent table**: Medicines, Equipment, and Medical Devices each have a parent `items` record. Creating any inventory item auto-creates the `items` and `inventory` records.
- **Unique names**: Entity names have unique constraints (medicines, equipment, devices, categories, partners)
- **Enum values stored as strings**: DB columns are `String` type, with Python `StrEnum` classes for validation

---

## Authentication & Authorization

### JWT Token System

- **Access token**: 1 hour expiry, includes `sub` (user_id), `username`, `role`, `jti`, `type` ("access")
- **Refresh token**: 7 days expiry, same claims, `type` ("refresh")
- **Storage**: Client-side (frontend uses localStorage)
- **Blacklist**: Server-side in-memory `TokenBlacklist` (thread-safe dict, auto-cleans expired entries)

### Role-Based Access

- **Admin**: User CRUD, password reset
- **User**: All other endpoints
- **Dependency injection**: `get_current_user()`, `get_current_active_user()`, `get_current_admin_user()`

### Password Rules

- 8+ characters, 1 uppercase, 1 lowercase, 1 digit, 1 special character
- Hashed with bcrypt via passlib

### Docs Protection

- `/docs` and `/redoc` are password-protected in non-LOCAL environments (HTTP Basic auth via `DOCS_USERNAME`/`DOCS_PASSWORD`)

### Rate Limiting

- Global default: 200/minute (slowapi)
- Login: 10/minute
- Token refresh: 20/minute
- Admin password reset: 5/minute

---

## Coding Conventions

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Files | snake_case | `patient_service.py`, `vital_sign.py` |
| Classes | PascalCase | `PatientService`, `AppointmentResponse` |
| Functions/methods | snake_case | `get_by_id`, `create_user` |
| Variables | snake_case | `patient_id`, `transaction_type` |
| Constants | UPPER_CASE | `PASSWORD_PATTERN`, `ALLOWED_SORT` |
| Enum members | UPPER_CASE | `AppointmentStatus.SCHEDULED` |
| Logger names | `medbase.<layer>.<module>` | `medbase.router.auth` |

### Import Ordering

```python
# 1. Standard library
import logging
from datetime import datetime

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func

# 3. Application modules
from app.model.user import User
from app.service.user_service import UserService
from app.schema.user import UserCreate, UserResponse
```

### Enum Pattern

```python
from enum import StrEnum

class AppointmentType(StrEnum):
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"

# DB column: String type (not Enum type)
class Appointment(Base):
    __tablename__ = "appointments"
    type = Column(String, nullable=False)
```

### SQLAlchemy Query Patterns

**Explicit joins only — NO `selectinload()` or lazy loading:**

```python
# Correct: explicit outerjoin + contains_eager
result = await self.db.execute(
    select(Appointment)
    .outerjoin(VitalSign, and_(
        Appointment.id == VitalSign.appointment_id,
        VitalSign.is_deleted == False
    ))
    .options(contains_eager(Appointment.vital_sign))
    .where(Appointment.id == id, Appointment.is_deleted == False)
)
```

**Relationships use `lazy="noload"`:**
```python
vital_sign = relationship("VitalSign", back_populates="appointment", lazy="noload")
```

**Count queries derived from main query:**
```python
# Reuse the main query for counts — don't duplicate filters
count_query = select(func.count()).select_from(query.subquery())
total_result = await self.db.execute(count_query)
total = total_result.scalar()
```

**Multi-join queries with aliased ThirdParty:**
```python
# When multiple entities reference third_parties, use aliased()
PatientTP = aliased(ThirdParty)
DoctorTP = aliased(ThirdParty)

query = (
    select(Appointment, PatientTP.name.label("patient_name"), DoctorTP.name.label("doctor_name"))
    .outerjoin(Patient, Appointment.patient_id == Patient.id)
    .outerjoin(PatientTP, Patient.third_party_id == PatientTP.id)
    .outerjoin(Doctor, Appointment.doctor_id == Doctor.id)
    .outerjoin(DoctorTP, Doctor.third_party_id == DoctorTP.id)
    .where(Appointment.is_deleted == False)
)
```

**Incremental filter building:**
```python
if patient_id is not None:
    query = query.where(Appointment.patient_id == patient_id)
if status is not None:
    query = query.where(Appointment.status == status)
if search:
    search_term = f"%{search}%"
    query = query.where(or_(
        Appointment.code.ilike(search_term),
        PatientTP.name.ilike(search_term),
    ))
```

**Flush vs Commit:**
```python
# Use flush() + refresh() for intermediate state within a transaction
await self.db.flush()       # Write to DB buffer
await self.db.refresh(obj)  # Reload to get server-generated values (id, timestamps)
# The session's get_db() dependency handles final commit/rollback
```

### Response Patterns

- **List endpoints**: Return `PaginatedResponse[ItemType]` with `items`, `total`, `page`, `size`
- **Single entity**: Return Pydantic schema directly
- **Success messages**: Return `MessageResponse` with `message` field
- **Errors**: `HTTPException` with `detail` string → `{"detail": "error message"}`
- **Validation errors**: Pydantic auto-returns 422 with field-level errors

### Pagination

- Query params: `page` (1-based, default 1), `size` (1-100, default 10)
- Offset formula: `(page - 1) * size`
- Response includes: `total`, `page`, `size`

### Filtering & Searching

- **Filters**: Exact match on enums/booleans/FKs (`is_active`, `status`, `type`, `category_id`, `partner_id`)
- **Search**: Case-insensitive LIKE on string fields (`name`, `username`, `email`, `notes`)
- **Date filters**: ISO format `YYYY-MM-DD`

### Sorting

- Query params: `sort` (field name), `order` ("asc"/"desc")
- Allowed fields validated per endpoint (via `validate_sort_field()`)
- Default: `id` ascending

### Error Handling

| Code | Usage |
|------|-------|
| 400 | Invalid input, uniqueness violations, FK errors |
| 401 | Invalid credentials, expired token |
| 403 | Insufficient permissions, deactivated account |
| 404 | Resource not found |
| 409 | Business logic violation (e.g., edit completed appointment) |
| 422 | Pydantic validation errors (auto) |
| 500 | Unhandled exception (global handler logs + generic message) |

### Logging

- **Request logging**: Middleware logs every request/response with duration
- **Sensitive field masking**: `password`, `password_hash`, `secret_key`, `access_token` → `"***"`
- **Router layer**: `info` for actions, `warning` for failures
- **Service layer**: `info` for writes, `debug` for reads
- **Log level**: Controlled by `DEBUG` env var

---

## Service Layer Patterns

### Constructor

```python
class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
```

### Standard Method Signatures

```python
# Read
async def get_by_id(self, id: int) -> Optional[Model]
async def get_all(self, page, size, filters..., sort, order) -> Tuple[List[dict], int]

# Write
async def create(self, data: CreateSchema, created_by: str = None) -> Model
async def update(self, id: int, data_or_kwargs, updated_by: str = None) -> Optional[Model]
async def delete(self, id: int, deleted_by: str = None) -> bool  # Soft delete
```

### Error Flow (Service → Router)

Services raise `ValueError` for business rule violations. Routers catch and convert:

```python
# In service:
if inventory.quantity < quantity:
    raise ValueError(f"Insufficient inventory for item_id={item_id}")

# In router:
try:
    result = await service.create(data, created_by=current_user.username)
except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

### Sorting Validation

Each service defines `ALLOWED_SORT` fields and falls back to `"id"`:

```python
ALLOWED_SORT = {"id", "code", "name", "appointment_date", "status"}
if sort not in ALLOWED_SORT:
    sort = "id"
sort_column = getattr(Model, sort, Model.id)
query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
```

### Response Building (from_row classmethod)

When list queries return tuples (model + joined data), schemas use `from_row()`:

```python
class AppointmentListResponse(BaseModel):
    @classmethod
    def from_row(cls, row) -> "AppointmentListResponse":
        appt = row[0]
        return cls.model_validate({
            "id": appt.id,
            "patient_name": row[1],  # from aliased join
            "doctor_name": row[2],
            # ...
        })
```

### Soft Delete with Cascade Reversal

When deleting transactions, all related items are also soft-deleted and their inventory impact reversed:

```python
async def delete(self, transaction_id, deleted_by=None):
    items = await self._get_transaction_items(transaction_id)
    for item in items:
        await self._reverse_inventory(item.item_id, item.quantity, transaction.transaction_type)
        item.is_deleted = True
        item.updated_by = deleted_by
    transaction.is_deleted = True
    transaction.updated_by = deleted_by
    await self.db.flush()
```

---

## Schema Layer Patterns

### CRUD Schema Set

Every entity follows: `{Entity}Create`, `{Entity}Update`, `{Entity}Response`

```python
class EntityCreate(BaseModel):
    name: str                           # Required
    description: Optional[str] = None   # Optional

class EntityUpdate(BaseModel):
    name: Optional[str] = None          # All optional for partial updates
    description: Optional[str] = None

class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    # ... + audit fields (created_by/at, updated_by/at, is_deleted)
```

### Partial Updates with `exclude_unset`

```python
update_fields = data.model_dump(exclude_unset=True)
# Only fields explicitly sent by the client are included
```

### Field Validation

```python
quantity: int = Field(..., gt=0)           # Must be > 0
name: Optional[str] = Field(None, min_length=1, max_length=255)
```

### Generic Pagination

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
```

---

## Router Layer Patterns

### Standard CRUD Endpoint Set

Each resource typically has:
- `GET /resources` → `PaginatedResponse[ListSchema]` (with Query params for filters/sort/pagination)
- `GET /resources/{id}` → `DetailSchema`
- `POST /resources` → `DetailSchema` (status 201)
- `PUT /resources/{id}` → `DetailSchema`
- `DELETE /resources/{id}` → `MessageResponse`

### Auth Dependency Variants

```python
current_user: User = Depends(get_current_user)     # Any authenticated user
admin: User = Depends(get_current_admin_user)       # Admin only
```

### Query Parameter Pattern

```python
page: int = Query(1, ge=1, description="Page number"),
size: int = Query(10, ge=1, le=100, description="Page size"),
sort: str = Query("id", description="Sort field"),
order: str = Query("asc", description="Sort order (asc/desc)"),
```

---

## Business Rules

### Inventory Transactions

| Transaction Type | third_party_id | Inventory Effect |
|-----------------|----------------|------------------|
| `purchase` | Auto-set to current user | +quantity |
| `donation` | Must be a donor partner (partner_type: donor/both) | +quantity |
| `prescription` | Must be a doctor | -quantity |
| `loss` | Auto-set to current user | -quantity |
| `breakage` | Auto-set to current user | -quantity |
| `expiration` | Auto-set to current user | -quantity |
| `destruction` | Auto-set to current user | -quantity |

- Equipment cannot be prescribed
- Cannot decrease inventory below 0
- Deleting a transaction reverses its inventory impact
- Items reference `item_id` from the `items` table (not the entity table ID)

### Appointments

- Status flow: `scheduled` → `in_progress` → `completed` (or `cancelled` from any state)
- External appointments require `partner_id`
- Cannot edit completed appointments
- One vital signs record per appointment
- One medical record per appointment

### Partners

- `donor`: Can make donation transactions
- `referral`: Can receive treatments
- `both`: Can do both

### Doctors

- `internal`: Clinic staff
- `external`: External doctor
- `partner_provided`: Must have `partner_id`

### Deletion Rules

- Items (medicines/equipment/devices): Can only delete if inventory quantity = 0
- Categories: Cannot delete if items are linked
- Admin cannot delete themselves

---

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/medbase
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/medbase_test

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256                          # default
ACCESS_TOKEN_EXPIRE_MINUTES=60           # default

# Application
DEBUG=false                              # default
ENV=LOCAL                                # LOCAL, DEV, PROD
CORS_ORIGINS=*                           # comma-separated, default * for LOCAL
API_V1_PREFIX=/api/v1                    # default
PROJECT_NAME=MedBase API                 # default

# File Storage (Lightsail/S3)
LIGHTSAIL_BUCKET_NAME=your-bucket
LIGHTSAIL_ACCESS_KEY=your-key
LIGHTSAIL_SECRET_KEY=your-secret
LIGHTSAIL_ENDPOINT=bucket.s3.region.amazonaws.com
LIGHTSAIL_REGION=your-region

# Docs Auth (non-LOCAL only)
DOCS_USERNAME=admin                      # default
DOCS_PASSWORD=your-password
```

### Settings Management

- `app/utility/config.py` — `Settings` class (Pydantic BaseSettings)
- Singleton via `@lru_cache()` on `get_settings()`
- If missing env vars during development, **ask the user** — do not guess

---

## Middleware Stack

Applied in order (outermost → innermost):
1. **SecurityHeadersMiddleware** — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
2. **RequestLoggingMiddleware** — Logs method, path, body (masked), status, duration in ms
3. **CORS Middleware** — LOCAL: `allow_origins=["*"]`, `allow_credentials=False`; DEV/PROD: origins from `CORS_ORIGINS`, `allow_credentials=True`
4. **Rate Limiter** — slowapi (200/minute global, endpoint-specific overrides)

---

## Utility Modules

| Module | Purpose |
|--------|---------|
| `auth.py` | JWT dependency injection (`get_current_user`, `get_current_admin_user`) |
| `config.py` | Settings class with env var loading |
| `database.py` | Async engine, session factory, `get_db()` dependency, `Base` class |
| `security.py` | Password hashing, JWT creation/validation, password strength check |
| `logging.py` | Logger setup, request logging middleware, sensitive field masking |
| `rate_limit.py` | slowapi limiter singleton |
| `storage.py` | S3/Lightsail file operations (upload, delete, presigned URL) |
| `token_blacklist.py` | In-memory token revocation (add, check, cleanup) |
| `sorting.py` | Sort field validation |

---

## Testing

### Structure

- Framework: pytest + pytest-asyncio
- Test DB: `TEST_DATABASE_URL` (separate database, fresh schema per test)
- Test files: `tests/endpoint/test_*.py` (15+ files, 200+ tests)

### Fixtures (conftest.py)

- `db_session()` — Fresh async DB session
- `client()` — AsyncClient with DB override
- `admin_user()`, `regular_user()` — Pre-created users
- `admin_token()`, `user_token()` — JWT tokens
- `admin_headers()`, `user_headers()` — Authorization headers

### Running Tests

```bash
make test                    # All tests
make test-one TEST=tests/endpoint/test_users.py::TestCreateUser::test_create_user_success
make test-cov                # With coverage report
```

### Test Patterns

- Each endpoint tests: success, not found, validation errors, auth required, business rules
- Tests validate both response data AND query database directly
- Rate limiter and token blacklist reset between tests
- Use `KEEP_DB=1` env var to inspect test data after run

---

## Database Migrations

### Alembic Commands

```bash
make migrate                           # Run all pending migrations
make migrate-create MSG="description"  # Autogenerate migration
make migrate-down                      # Downgrade one
make db-reset                          # Drop all + migrate up
```

### Rules

- **Always create a new migration** when DB changes are needed — never modify existing ones
- **Autogenerate first, then manually edit** — use `make migrate-create`
- If no `DATABASE_URL`, start a local PostgreSQL, apply migrations, then autogenerate

### Existing Migrations (4)

1. `20260307_initial.py` — Full initial schema
2. `20260308_remove_patient_names.py` — Moved names to ThirdParty
3. `20260310_add_appointment_short_code_and_transaction_appointment_id.py`
4. `20260315_add_items_table_and_refactor_inventory.py` — Item parent table

---

## Seed & Dummy Data

- `make seed` — Creates default admin (admin/admin123)
- `make populate` — Fills DB with test data from `scripts/dummy_data.json`
- `make db-reset` → `make migrate` → `make seed` → `make populate` for full reset

---

## File Storage

- **Patient documents** stored in Lightsail bucket (S3-compatible)
- Upload: `POST /patients/{id}/documents` (multipart/form-data)
- Retrieval: `GET /patient-documents/{id}` returns presigned URL (5 min expiry)
- Key format: `patient-documents/{patient_id}/{uuid}.{ext}`
- Operations: `upload_file()`, `delete_file()`, `generate_presigned_url()`

---

## API Documentation

Router docstrings are the **single source of truth** for endpoint documentation. They auto-generate:

- **Swagger UI**: `/docs` (interactive testing)
- **ReDoc**: `/redoc` (browsable reference)
- **OpenAPI JSON**: `/openapi.json` (machine-readable spec)
- **Production**: `https://dev-api.medbaseclinic.com/openapi.json`
- **Postman**: Collection in `docs/MedBase API.postman_collection.json`

There is no separate `endpoints.md` — keep all endpoint details in the router docstrings so they stay in sync automatically.

---

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Build Docker image |
| `make up` | Start API (detached) |
| `make up-logs` | Start API (with logs) |
| `make down` | Stop API |
| `make logs` | View logs |
| `make shell` | Shell in container |
| `make test` | Run all tests |
| `make test-one TEST=path` | Run specific test |
| `make test-cov` | Tests with coverage |
| `make migrate` | Run migrations |
| `make migrate-create MSG="msg"` | Create migration |
| `make migrate-down` | Downgrade one |
| `make db-reset` | Reset database |
| `make seed` | Seed admin user |
| `make populate` | Populate dummy data |
| `make clean` | Remove containers/volumes |
| `make clean-pyc` | Remove __pycache__ |
| `make dev` | Run locally (no Docker) |
| `make lint` | Run linter |
| `make format` | Format code |

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/database.dbml` | Database schema (import to dbdiagram.io) |
| `docs/pages.md` | Frontend page layouts and functionality specs |
| `docs/MedBase API.postman_collection.json` | Postman collection with request examples |
| OpenAPI JSON (`/openapi.json`) | Auto-generated from router docstrings — the single source of truth for all endpoint details |

---

## Database Connection Pool

```python
engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,          # SQL logging in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,   # 30 minutes
)
```

Session uses `expire_on_commit=False` and `autoflush=False` for explicit control.

The `get_db()` dependency handles commit on success and rollback on exception automatically.

---

## Anti-Patterns to Avoid

1. **No `selectinload()` or `lazy="select"`** — always use explicit joins + `contains_eager()`
2. **No raw `dict` in `response_model`** — always use Pydantic schemas
3. **No PostgreSQL `Enum` column type** — use `String` + `StrEnum` validation
4. **No query logic in routers** — all queries belong in services
5. **No `refresh()` without `flush()` first** — flush writes to buffer, refresh reloads
6. **No unmasked sensitive data in logs** — use the masking utility
7. **No duplicate filter logic** — build filters incrementally on a single query object
8. **No mixing atomic operations across methods** — keep transaction boundaries together
9. **No forgetting `is_deleted == False`** — every query must exclude soft-deleted records
10. **No hardcoding env values** — use `Settings` class from `config.py`

---

## Development Workflow

Follow this sequence for every change — no exceptions:

### 1. Understand
- Read the relevant router, service, model, and schema files
- Check business rules in this guide and the OpenAPI spec (`/openapi.json` or Swagger/ReDoc)
- Review existing tests for the affected endpoints
- If adding a new feature, read similar existing implementations first
- If you need env variables to run or test the app, **ask the user** — never guess, hardcode, or use placeholder values. See `.env.example` for the full list.

### 2. Develop
- Follow the 4-layer architecture (router → service → model/schema)
- Match existing patterns exactly (naming, imports, error handling, logging)
- Add comprehensive docstrings to any new/modified router endpoints
- Create Alembic migration if DB schema changes (`make migrate-create MSG="description"`)

### 3. Test
- Run `make test` for all tests, or `make test-one TEST=path` for specific tests
- Write tests for: success case, not found, validation errors, auth required, business rules
- Fix any failures before proceeding — never push failing tests
- Use `KEEP_DB=1` to inspect test data if debugging

### 4. Update Docs & Postman
- Update router docstrings — they are the single source of truth and auto-generate Swagger/ReDoc and the OpenAPI spec
- Update the Postman collection (`docs/MedBase API.postman_collection.json`) with request examples
- Update this CLAUDE.md if new patterns, conventions, or business rules are introduced

### 5. Commit & Push
- Stage only the files you changed — don't use `git add .`
- Write a clear commit message describing what changed and why
- Push to the remote branch

---

## Code Style Rules

1. **All imports at the top** — no inline or mid-file imports
2. **Always use CLI tools** when available (alembic for migrations, make commands)
3. **Always run tests before pushing** — never push failing code
4. **Any code change must include updated tests and Postman**
5. **If missing env vars, ask the user** — never guess or hardcode
6. **One service per entity** — don't merge unrelated business logic
7. **Docstrings on all router endpoints** — they appear in Swagger/ReDoc
8. **Use `created_by`/`updated_by`/`deleted_by`** — always pass `current_user.username`
