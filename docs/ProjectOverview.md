# MedBase - Clinic Management System

## Project Idea

MedBase is a clinic management application designed for small medical clinics. It will help manage patients, appointments, medical records, and daily clinic operations in one unified platform.

---

## Tech Stack

- **Frontend**: Angular
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic, Pydantic, Conda
- **Database**: PostgreSQL (Amazon RDS)
- **File Storage**: Amazon Lightsail Bucket (S3-compatible)
- **Containerization**: Docker (backend)
- **Deployment**: AWS

---

## Code & Design

### Frontend (Angular)

**Reusable Components**
- Create basic reusable components for: buttons, inputs, dropdowns, tables
- Keep components simple with basic functionality only
- Page-specific functionality stays in the page, not in shared components

**Dropdown Behavior**
- Paginated API calls with page size of 50
- "View More..." button to load next page
- Search triggers API call (not local filtering)
- Search only activates after 3+ characters

**Table Behavior**
- Sortable columns via header click
- Pagination
- Action buttons per row: View, Edit, Delete

**Page Layouts**
- View/Edit/Create pages use two-column layout:
  - Left: main entity data
  - Right: related items list/table

**Navigation**
- Sidebar with links to all resource list pages

**General**
- Use `ng` CLI commands to auto-generate and configure when possible
- Mobile responsive design

**Theme**
- White and blue color scheme

---

### Backend (FastAPI)

**Architecture (4-Layer Pattern)**
- `router` — endpoints, authentication, authorization, validation
- `service` — business logic
- `model` — SQLAlchemy ORM class
- `schema` — Pydantic input/output validation

**Database Columns (Standard)**
| Column | Required | Notes |
|--------|----------|-------|
| `created_by` | Yes | Set on creation |
| `created_at` | Yes | Set on creation |
| `updated_by` | Yes | Set on creation, updated on edit |
| `updated_at` | Yes | Set on creation, updated on edit |
| `is_deleted` | Yes | Soft delete flag |
| `is_active` | Optional | For resources that can be deactivated (e.g., doctors) |

**Unique Names**
- In general, entity names should be unique across the system
- Add unique constraints on name fields in models to prevent duplicates
- Validate uniqueness in the service layer when creating or updating entities

**Third Parties**
- A `third_parties` table serves as the base identity record for all persons/entities in the system
- Every user, doctor, patient, and partner has a corresponding `third_party` record
- When creating a doctor, patient, or partner: if no `third_party_id` is provided, the system automatically creates a third_party record; if a `third_party_id` is provided, it links to the existing one
- `inventory_transactions` links to `third_party_id` to identify who is involved in the transaction:
  - **Donations**: `third_party_id` must point to a donor (partner with `partner_type` of `donor` or `both`)
  - **Prescriptions**: `third_party_id` must point to a doctor
  - **Other types** (purchase, loss, breakage, expiration, destruction): `third_party_id` is set to the logged-in user's `third_party_id`

**Business Rules**
- Only doctors can make prescriptions
- Only donors (partners with `partner_type` of `donor` or `both`) can make donations
- For non-donation/non-prescription transactions, the system automatically uses the current user's `third_party_id`

**Authentication**
- JWT Bearer tokens
- Token expiry: 1 hour

**Project Structure**
- `main.py` at root
- General app utilities in `utility/` folder

**Migrations**
- Alembic for migration management
- After creating/updating a model, run autogenerate command to create migration
- Manually edit migration if needed

**SQLAlchemy Joins**
- Do NOT use `selectinload()` or lazy loading
- Always use explicit manual joins with `outerjoin()` + `contains_eager()`

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

**Limited Option Fields (Enums)**
- Fields with limited options should be stored as `String` type in the database model
- Create a corresponding `StrEnum` class to define the allowed values in code
- Each enum should be defined in its relative resource's file (e.g., `AppointmentType` in `appointment.py`)
- This provides type safety and validation while maintaining database flexibility

```python
from enum import StrEnum

class AppointmentType(StrEnum):
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"

class Appointment(Base):
    __tablename__ = "appointments"
    type = Column(String, nullable=False)  # Stores enum values as strings
```

**API Endpoints (Get All)**
- Pagination: `page` and `size` parameters
- Sorting: sortable by specified fields
- Searching: text search across relevant fields
- Filtering: exact match filters

**Docker & Environment**
- Base image: Miniconda slim
- Dependency files: `environment.yml` + `requirements.txt`
- Single Docker setup with hot reload for development
- Database hosted on Amazon RDS (no local PostgreSQL containers)
- File storage via Amazon Lightsail Bucket (S3-compatible, using `aioboto3`)
- All environment variables loaded from `.env` (`DATABASE_URL`, `TEST_DATABASE_URL`, `LIGHTSAIL_*`, etc.)
- Makefile for common commands (build, run, test, migrate, etc.)

**Testing**
- Separate test database on Amazon RDS (`TEST_DATABASE_URL` from `.env`)
- Clean/empty before each test run
- Endpoint tests: validate API responses AND query the database directly to verify data was correctly inserted, updated, or deleted

**Logging**
- Python standard `logging` module
- Middleware logs every request (method, URL, body) and response (status, duration)
- Sensitive fields (`password`, `access_token`) are masked in body logs
- Router layer: `info` for actions and outcomes, `warning` for failures (not found, duplicates, auth failures)
- Service layer: `info` for writes (create, update, delete), `debug` for reads and auth details
- Logger names follow `medbase.<layer>.<module>` convention (e.g. `medbase.router.auth`)
- Log level controlled by `DEBUG` env var (`DEBUG=true` → DEBUG level, otherwise INFO)

**API Documentation**
- Postman collection with request examples for each endpoint

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

### Dashboard
- Summary statistics: inventory, appointments, transactions, partners

### UI & Navigation
- Sidebar for quick access to all sections
- Table page for each resource to view all records
- Table rows have action buttons: view, edit, delete
- Separate pages for create, view, and update (create/update can share a page if feasible)

### View Page Layout
- Two-section layout: left side shows general data, right side shows related items/sub-items (where applicable)
- **Donor view**: Donor details + donation transaction cards with summarized data
- **Referral Partner view**: Partner details + list of treatments

### Treatments
- Track treatments provided to patients through external partners


