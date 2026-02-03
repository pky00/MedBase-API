# MedBase - Clinic Management System

## Project Idea

MedBase is a clinic management application designed for small medical clinics. It will help manage patients, appointments, medical records, and daily clinic operations in one unified platform.

---

## Tech Stack

- **Frontend**: Angular
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic, Pydantic, Conda
- **Database**: PostgreSQL
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

**Authentication**
- JWT Bearer tokens
- Token expiry: 1 hour

**Project Structure**
- `main.py` at root
- General app utilities in `utility/` folder

**Migrations**
- Alembic for migration management
- Auto-generate migrations, manually edit if needed

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

**API Endpoints (Get All)**
- Pagination: `page` and `size` parameters
- Sorting: sortable by specified fields
- Searching: text search across relevant fields
- Filtering: exact match filters

**Docker & Environment**
- Base image: Miniconda slim
- Dependency files: `environment.yml` + `requirements.txt`
- Two configurations:
  - **Local**: development setup with hot reload
  - **Production**: optimized for deployment
- Makefile for common commands (build, run, test, migrate, etc.)

**Testing**
- Separate test database (clean/empty before each test run)
- Endpoint tests: validate API responses
- Database tests: verify data is correctly inserted, updated, and deleted

**API Documentation**
- Postman collection with request examples for each endpoint

---

## Development Flow

**Approach**
- Features developed independently in sequential order
- Frontend and Backend developed separately
- Backend order per feature: Endpoints → Tests → Postman requests

**Progress Tracking**
- `BE.PROGRESS.md` — backend progress
- `FE.PROGRESS.md` — frontend progress
- `plan.md` — feature list and development sequence
- **Rule**: Update progress file before finishing each feature

**Documentation Files**
- `database.sql` — database schema (Backend)
- `endpoints.md` — API endpoints list (Backend, copied to Frontend)
- `Postman collection` — (Backend, copied to Frontend)
- `pages.md` — page layouts and functionality (Frontend)

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
- Prescribe medicine and medical devices (automatically decreases inventory)

### Partners
- Track partners (NGO, organization, individual, hospital, medical center)
- Partner types: donor, referral, or both
- **Donations**: Record what items were donated per donation
- **Treatments**: Track treatments/operations sent to referral partners

### Doctors
- Track doctors (clinic staff, external, or provided by donors)

### Users & Authentication
- User system for data entry staff
- Admin role to manage users (CRUD)

### Dashboard
- Summary statistics: inventory, appointments, donations, donors

### UI & Navigation
- Sidebar for quick access to all sections
- Table page for each resource to view all records
- Table rows have action buttons: view, edit, delete
- Separate pages for create, view, and update (create/update can share a page if feasible)

### View Page Layout
- Two-section layout: left side shows general data, right side shows related items/sub-items (where applicable)
- **Donor view**: Donor details + donation cards with summarized data
- **Donation view**: Donation details + table of donated items (can include any mix of medicines, equipment, medical devices)
- **Referral Partner view**: Partner details + list of treatments

### Treatments
- Track treatments provided to patients through external partners
