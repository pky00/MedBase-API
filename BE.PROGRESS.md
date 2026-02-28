# MedBase Backend Progress

## Agent Instructions

You are the Backend Agent for MedBase. Your job is to build the FastAPI backend following the 4-layer architecture (router, service, model, schema). For each feature, work in this order: implement the endpoints, write tests (endpoint tests + database tests), then create Postman requests. Always follow the coding practices in `docs/ProjectOverview.md`, use the database schema from `docs/database.dbml`, and implement endpoints as specified in `docs/endpoints.md`. Update this progress file before finishing each feature. Follow the development plan in `docs/plan.md` and complete features in sequential order.

---

## Current Phase: Phase 5 - Appointments & Records

---

## Completed Features

| # | Feature | Date Completed | Notes |
|---|---------|----------------|-------|
| 1 | Project Setup (BE) | 2026-02-03 | FastAPI structure, Docker (Miniconda), PostgreSQL, Alembic, Makefile |
| 3 | Third Parties | 2026-02-14 | Base identity table for users/doctors/patients/partners. Read-only API (GET list, GET by ID). Auto-created by linked entities |
| 4 | Users & Authentication | 2026-02-03 | User CRUD, JWT auth (1hr expiry), admin role, login/logout/me endpoints. Users now have third_party_id |
| 5 | Inventory Categories | 2026-02-11 | Medicine, Equipment, Medical Device categories with CRUD, search, soft delete, linked item checks |
| 6 | Medicines | 2026-02-11 | Medicine CRUD with category, auto inventory creation, delete restriction (qty > 0) |
| 7 | Equipment | 2026-02-11 | Equipment CRUD with category/condition, auto inventory creation, delete restriction |
| 8 | Medical Devices | 2026-02-11 | Medical device CRUD with category/serial number, auto inventory creation, delete restriction |
| 9 | Partners | 2026-02-14 | Partner CRUD with donor/referral/both types, organization types, third_party_id (auto-created or linked), search, filters |
| 10 | Doctors | 2026-02-14 | Doctor CRUD with internal/external/partner_provided types, third_party_id (auto-created or linked), partner validation |
| 11 | Patients | 2026-02-27 | Patient CRUD with third_party auto-creation, gender filter, search by name/phone/email, pagination |
| 12 | Patient Documents | 2026-02-27 | Document upload to Lightsail bucket (S3), list/get/delete, multipart/form-data, document_type filter |
| 13 | Appointments | 2026-02-27 | Appointment CRUD with status flow, patient/doctor/partner links, internal/external locations, filters, pagination |
| 14 | Vital Signs | 2026-02-27 | One vital signs record per appointment, all fields optional, cannot edit when completed |
| 15 | Medical Records | 2026-02-27 | One medical record per appointment, patient_id/appointment_id filters, cannot edit when completed |
| 16 | Treatments | 2026-02-27 | Multiple treatments per appointment, referral partner validation, status flow, patient/partner names |

---

## In Progress

| # | Feature | Started | Notes |
|---|---------|---------|-------|
|   |         |         |       |

---

## Phase 1 Details

### Feature 1: Project Setup (BE)
**Status:** Complete

**Implemented:**
- 4-layer architecture (router, service, model, schema)
- Docker configuration with Miniconda base image
- docker-compose.yml for local development (with PostgreSQL + test DB)
- docker-compose.prod.yml for production
- environment.yml and requirements.txt with all dependencies
- Alembic migration setup for async SQLAlchemy
- Makefile with common commands (build, up, down, test, migrate, etc.)
- Configuration management with pydantic-settings
- .env and .env.example files

### Feature 3: Third Parties
**Status:** Complete

**Endpoints:**
- GET `/api/v1/third-parties` - List all third parties (paginated, filterable by type, is_active, searchable)
- GET `/api/v1/third-parties/{id}` - Get third party by ID

**Model:**
- id, name, type (user/doctor/patient/partner), phone, email, is_active, is_deleted, audit columns

**Notes:**
- Read-only API — no direct create/update/delete
- Records created automatically when creating users, doctors, patients, or partners
- Linked by FK from users.third_party_id, partners.third_party_id, doctors.third_party_id

**Tests:**
- test_third_parties.py (6 tests: list, filter by type, filter by is_active, auto-creation via user, get by ID, not found)

**Postman:**
- Third Parties folder (Get All, Get by ID)

### Feature 4: Users & Authentication
**Status:** Complete

**Endpoints:**
- POST `/api/v1/auth/login` - JWT login
- POST `/api/v1/auth/logout` - Logout (client discards token)
- GET `/api/v1/auth/me` - Get current user info
- GET `/api/v1/users` - List users (admin only, paginated, filterable)
- GET `/api/v1/users/{id}` - Get user by ID (admin only)
- POST `/api/v1/users` - Create user (admin only, auto-creates third_party record)
- PUT `/api/v1/users/{id}` - Update user (admin only)
- DELETE `/api/v1/users/{id}` - Delete user (admin only, soft delete)

**User Model:**
- id, third_party_id (FK), username (unique), email (unique), password_hash
- role (admin/user), is_active, is_deleted
- Audit columns: created_by, created_at, updated_by, updated_at

**Tests:**
- Endpoint tests: test_auth.py (login, logout, me)
- Endpoint tests: test_users.py (CRUD operations, pagination, filters)

**Postman:**
- Authentication folder (Login, Logout, Get Current User)
- Users folder (Get All, Get by ID, Create, Update, Delete)

---

## Phase 2 Details

### Feature 5: Inventory Categories
**Status:** Complete

**Tests:**
- test_medicine_categories.py (12 tests)
- test_equipment_categories.py (11 tests)
- test_medical_device_categories.py (11 tests)

### Feature 6: Medicines
**Status:** Complete

**Tests:**
- test_medicines.py (14 tests)

### Feature 7: Equipment
**Status:** Complete

**Tests:**
- test_equipment.py (13 tests)

### Feature 8: Medical Devices
**Status:** Complete

**Tests:**
- test_medical_devices.py (13 tests)

### Inventory (supporting feature)
**Status:** Complete

**Tests:**
- test_inventory.py (10 tests)

---

## Phase 3 Details

### Feature 9: Partners
**Status:** Complete

**Endpoints:**
- GET `/api/v1/partners` - List all partners (paginated, filterable by partner_type, organization_type, is_active, searchable)
- GET `/api/v1/partners/{id}` - Get partner by ID
- POST `/api/v1/partners` - Create partner (auto-creates third_party if third_party_id not provided)
- PUT `/api/v1/partners/{id}` - Update partner
- DELETE `/api/v1/partners/{id}` - Delete partner (soft delete)

**Model:**
- id, third_party_id (FK), name (unique), partner_type (donor/referral/both), organization_type (NGO/organization/individual/hospital/medical_center)
- contact_person, phone, email, address, is_active, is_deleted, audit columns

**Tests:**
- test_partners.py (17 tests: CRUD, filters, search, pagination, third_party auto-creation, link to existing third_party, duplicate name, validation)

**Postman:**
- Partners folder (Get All, Get by ID, Create, Update, Delete)

### Feature 10: Doctors
**Status:** Complete

**Endpoints:**
- GET `/api/v1/doctors` - List all doctors (paginated, filterable by type, is_active, partner_id, searchable)
- GET `/api/v1/doctors/{id}` - Get doctor by ID (includes partner name if partner_provided)
- POST `/api/v1/doctors` - Create doctor (auto-creates third_party if third_party_id not provided; partner_id required for partner_provided)
- PUT `/api/v1/doctors/{id}` - Update doctor
- DELETE `/api/v1/doctors/{id}` - Delete doctor (soft delete)

**Model:**
- id, third_party_id (FK), name (unique), specialization, phone, email, type (internal/external/partner_provided)
- partner_id (FK to partners, required for partner_provided), is_active, is_deleted, audit columns

**Tests:**
- test_doctors.py (18 tests: CRUD, filters, search, third_party auto-creation, link to existing third_party, partner validation, type validation, duplicate name)

**Postman:**
- Doctors folder (Get All, Get by ID, Create Internal, Create Partner Provided, Update, Delete)

---

## Phase 4 Details

### Feature 11: Patients
**Status:** Complete

**Endpoints:**
- GET `/api/v1/patients` - List all patients (paginated, filterable by is_active, gender, searchable by first_name, last_name, phone, email)
- GET `/api/v1/patients/{id}` - Get patient by ID
- POST `/api/v1/patients` - Create patient (auto-creates third_party if third_party_id not provided)
- PUT `/api/v1/patients/{id}` - Update patient (syncs third_party name)
- DELETE `/api/v1/patients/{id}` - Delete patient (soft delete)

**Model:**
- id, third_party_id (FK), first_name, last_name, date_of_birth, gender (male/female), phone, email, address
- emergency_contact, emergency_phone, is_active, is_deleted, audit columns

**Tests:**
- test_patients.py (20 tests: CRUD, filters by gender/is_active, search by first_name/last_name, pagination, third_party auto-creation, link to existing third_party, invalid third_party, validation errors, soft delete verification)

**Postman:**
- Patients folder (Get All, Get by ID, Create, Update, Delete)

### Feature 12: Patient Documents
**Status:** Complete

**Endpoints:**
- GET `/api/v1/patients/{patient_id}/documents` - List documents for patient (paginated, filterable by document_type)
- GET `/api/v1/patient-documents/{id}` - Get document by ID (includes file_url)
- POST `/api/v1/patients/{patient_id}/documents` - Upload document (multipart/form-data)
- DELETE `/api/v1/patient-documents/{id}` - Delete document (soft delete, removes from storage)

**Model:**
- id, patient_id (FK), document_name, document_type, file_path, upload_date, is_deleted, audit columns

**Storage:**
- Files uploaded to Amazon Lightsail Bucket (S3-compatible) via aioboto3
- Storage utility: `app/utility/storage.py` (upload_file, delete_file, get_file_url)
- File key format: `patient-documents/{patient_id}/{uuid}.{ext}`

**Tests:**
- test_patient_documents.py (14 tests: list, filter by type, pagination, get by ID, upload with/without type, upload for non-existent patient, delete, soft delete verification, S3 operations mocked)

**Postman:**
- Patient Documents folder (Get Patient Documents, Get Document by ID, Upload Document, Delete Document)

---

## Phase 5 Details

### Feature 13: Appointments
**Status:** Complete

**Endpoints:**
- GET `/api/v1/appointments` - List all appointments (paginated, filterable by patient_id, doctor_id, partner_id, status, type, location, appointment_date, searchable)
- GET `/api/v1/appointments/{id}` - Get appointment by ID (includes vitals, medical record, patient/doctor/partner names)
- POST `/api/v1/appointments` - Create appointment (validates patient, doctor, partner; external requires partner_id)
- PUT `/api/v1/appointments/{id}` - Update appointment (cannot update completed appointments)
- PUT `/api/v1/appointments/{id}/status` - Update appointment status
- DELETE `/api/v1/appointments/{id}` - Delete appointment (soft delete)

**Model:**
- id, patient_id (FK), doctor_id (FK, optional), partner_id (FK, optional), appointment_date, status (scheduled/in_progress/completed/cancelled), type (scheduled/walk_in), location (internal/external), notes, is_deleted, audit columns

**Tests:**
- test_appointments.py (25 tests: list, filters by status/type/patient_id/location, pagination, names in response, get by ID with details, create scheduled/walk_in/external, external without partner fails, invalid patient/doctor/type, update success/not found/completed fails, status updates, delete/soft delete verification)

**Postman:**
- Appointments folder (Get All, Get by ID, Create, Update, Update Status, Delete)

### Feature 14: Vital Signs
**Status:** Complete

**Endpoints:**
- GET `/api/v1/appointments/{appointment_id}/vitals` - Get vitals for appointment
- POST `/api/v1/appointments/{appointment_id}/vitals` - Add vitals to appointment (one per appointment)
- PUT `/api/v1/vital-signs/{id}` - Update vital signs (cannot edit if completed)
- DELETE `/api/v1/vital-signs/{id}` - Delete vital signs (soft delete)

**Model:**
- id, appointment_id (FK), blood_pressure_systolic, blood_pressure_diastolic, heart_rate, temperature, respiratory_rate, weight, height, notes, is_deleted, audit columns

**Business Rules:**
- One vital signs record per appointment
- All vital sign fields are optional
- Cannot add/edit if appointment is completed

**Tests:**
- test_vital_signs.py (14 tests: get vitals success/no vitals/appointment not found, create success/optional fields/duplicate fails/completed fails/appointment not found, update success/not found/completed fails, delete success/not found)

**Postman:**
- Vital Signs folder (Get Vitals, Add Vitals, Update, Delete)

### Feature 15: Medical Records
**Status:** Complete

**Endpoints:**
- GET `/api/v1/medical-records` - List all medical records (paginated, filterable by patient_id, appointment_id)
- GET `/api/v1/medical-records/{id}` - Get medical record by ID (includes patient_name)
- GET `/api/v1/appointments/{appointment_id}/medical-record` - Get record for appointment
- POST `/api/v1/appointments/{appointment_id}/medical-record` - Create record for appointment (one per appointment)
- PUT `/api/v1/medical-records/{id}` - Update medical record (cannot edit if completed)
- DELETE `/api/v1/medical-records/{id}` - Delete medical record (soft delete)

**Model:**
- id, appointment_id (FK), chief_complaint, diagnosis, treatment_notes, follow_up_date, is_deleted, audit columns

**Business Rules:**
- One medical record per appointment
- Cannot add/edit if appointment is completed

**Tests:**
- test_medical_records.py (19 tests: list, filters by patient/appointment, patient_name in response, get by ID/not found, get for appointment/no record/appointment not found, create success/minimal/duplicate fails/completed fails/appointment not found, update success/not found/completed fails, delete success/not found)

**Postman:**
- Medical Records folder (Get All, Get by ID, Get for Appointment, Create, Update, Delete)

### Feature 16: Treatments
**Status:** Complete

**Endpoints:**
- GET `/api/v1/treatments` - List all treatments (paginated, filterable by patient_id, partner_id, appointment_id, status)
- GET `/api/v1/treatments/{id}` - Get treatment by ID (includes patient_name, partner_name)
- POST `/api/v1/treatments` - Create treatment (partner must be referral/both, appointment optional, multiple per appointment allowed)
- PUT `/api/v1/treatments/{id}` - Update treatment
- PUT `/api/v1/treatments/{id}/status` - Update treatment status
- DELETE `/api/v1/treatments/{id}` - Delete treatment (soft delete)

**Model:**
- id, patient_id (FK), appointment_id (FK, optional), partner_id (FK), treatment_type, description, treatment_date, status (pending/in_progress/completed/cancelled), cost, notes, is_deleted, audit columns

**Business Rules:**
- Partner must have partner_type of 'referral' or 'both'
- Can optionally link to an appointment
- Multiple treatments allowed per appointment

**Tests:**
- test_treatments.py (24 tests: list, filters by status/patient/partner, pagination, names in response, get by ID/not found, create success/with appointment/multiple per appointment/donor fails/invalid patient/partner/appointment/empty type, update success/not found/invalid partner type, status updates/not found/invalid value, delete/soft delete verification)

**Postman:**
- Treatments folder (Get All, Get by ID, Create, Update, Update Status, Delete)

---

## Migration Notes

- Initial migration: `20260226_193257_039074b781f1_initial.py` (Phase 1-3 schema)
- Phase 4 migration: `20260227_add_patients_and_patient_documents.py` (patients and patient_documents tables)
- Phase 5 migration: `20260227_add_phase5_appointments_records_treatments.py` (appointments, vital_signs, medical_records, treatments tables)

---

## Notes

- Update this file before finishing each feature
- Format: Endpoints → Tests → Postman requests
