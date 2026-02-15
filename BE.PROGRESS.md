# MedBase Backend Progress

## Agent Instructions

You are the Backend Agent for MedBase. Your job is to build the FastAPI backend following the 4-layer architecture (router, service, model, schema). For each feature, work in this order: implement the endpoints, write tests (endpoint tests + database tests), then create Postman requests. Always follow the coding practices in `docs/ProjectOverview.md`, use the database schema from `docs/database.dbml`, and implement endpoints as specified in `docs/endpoints.md`. Update this progress file before finishing each feature. Follow the development plan in `docs/plan.md` and complete features in sequential order.

---

## Current Phase: Phase 3 - Partners & Doctors

---

## Completed Features

| # | Feature | Date Completed | Notes |
|---|---------|----------------|-------|
| 1 | Project Setup (BE) | 2026-02-03 | FastAPI structure, Docker (Miniconda), PostgreSQL, Alembic, Makefile |
| 3 | Users & Authentication | 2026-02-03 | User CRUD, JWT auth (1hr expiry), admin role, login/logout/me endpoints |
| 4 | Inventory Categories | 2026-02-11 | Medicine, Equipment, Medical Device categories with CRUD, search, soft delete, linked item checks |
| 5 | Medicines | 2026-02-11 | Medicine CRUD with category, auto inventory creation, delete restriction (qty > 0) |
| 6 | Equipment | 2026-02-11 | Equipment CRUD with category/condition, auto inventory creation, delete restriction |
| 7 | Medical Devices | 2026-02-11 | Medical device CRUD with category/serial number, auto inventory creation, delete restriction |
| 8 | Partners | 2026-02-14 | Partner CRUD with donor/referral/both types, organization types, search, filters, donation summary in detail view |
| 9 | Donations | 2026-02-14 | Donation CRUD with items, inventory transactions created automatically, any partner type allowed, donation items CRUD |
| 10 | Doctors | 2026-02-14 | Doctor CRUD with internal/external/partner_provided types, partner validation for partner_provided, partner name in detail view |
| - | Inventory Transactions | 2026-02-14 | Transaction CRUD (purchase/donation/prescription/loss/breakage/expiration/destruction), auto inventory update, reversal on delete |

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

### Feature 3: Users & Authentication
**Status:** Complete

**Endpoints:**
- POST `/api/v1/auth/login` - JWT login
- POST `/api/v1/auth/logout` - Logout (client discards token)
- GET `/api/v1/auth/me` - Get current user info
- GET `/api/v1/users` - List users (admin only, paginated, filterable)
- GET `/api/v1/users/{id}` - Get user by ID (admin only)
- POST `/api/v1/users` - Create user (admin only)
- PUT `/api/v1/users/{id}` - Update user (admin only)
- DELETE `/api/v1/users/{id}` - Delete user (admin only, soft delete)

**User Model:**
- id, username (unique), email (unique), password_hash
- role (admin/user), is_active, is_deleted
- Audit columns: created_by, created_at, updated_by, updated_at

**Tests:**
- Endpoint tests: test_auth.py (login, logout, me)
- Endpoint tests: test_users.py (CRUD operations, pagination, filters)
- Database tests: test_user_model.py (model, service layer)

**Postman:**
- Authentication folder (Login, Logout, Get Current User)
- Users folder (Get All, Get by ID, Create, Update, Delete)

---

## Phase 2 Details

### Feature 4: Inventory Categories
**Status:** Complete

**Endpoints:**
- GET `/api/v1/medicine-categories` - List all medicine categories (paginated, searchable)
- GET `/api/v1/medicine-categories/{id}` - Get medicine category by ID
- POST `/api/v1/medicine-categories` - Create medicine category
- PUT `/api/v1/medicine-categories/{id}` - Update medicine category
- DELETE `/api/v1/medicine-categories/{id}` - Delete medicine category (blocked if medicines linked)
- GET `/api/v1/equipment-categories` - List all equipment categories
- GET `/api/v1/equipment-categories/{id}` - Get equipment category by ID
- POST `/api/v1/equipment-categories` - Create equipment category
- PUT `/api/v1/equipment-categories/{id}` - Update equipment category
- DELETE `/api/v1/equipment-categories/{id}` - Delete equipment category (blocked if equipment linked)
- GET `/api/v1/medical-device-categories` - List all medical device categories
- GET `/api/v1/medical-device-categories/{id}` - Get medical device category by ID
- POST `/api/v1/medical-device-categories` - Create medical device category
- PUT `/api/v1/medical-device-categories/{id}` - Update medical device category
- DELETE `/api/v1/medical-device-categories/{id}` - Delete medical device category (blocked if devices linked)

**Models:**
- MedicineCategory: id, name, description, audit columns
- EquipmentCategory: id, name, description, audit columns
- MedicalDeviceCategory: id, name, description, audit columns

**Tests:**
- test_medicine_categories.py (12 tests)
- test_equipment_categories.py (11 tests)
- test_medical_device_categories.py (11 tests)

**Postman:**
- Medicine Categories folder (Get All, Get by ID, Create, Update, Delete)
- Equipment Categories folder (Get All, Get by ID, Create, Update, Delete)
- Medical Device Categories folder (Get All, Get by ID, Create, Update, Delete)

### Feature 5: Medicines
**Status:** Complete

**Endpoints:**
- GET `/api/v1/medicines` - List all medicines (paginated, filterable by category_id, is_active, searchable)
- GET `/api/v1/medicines/{id}` - Get medicine by ID (includes inventory quantity, category name)
- POST `/api/v1/medicines` - Create medicine (auto-creates inventory record with quantity 0)
- PUT `/api/v1/medicines/{id}` - Update medicine
- DELETE `/api/v1/medicines/{id}` - Delete medicine (only if inventory quantity is 0)

**Model:**
- id, name, category_id (FK), description, unit, is_active, is_deleted, audit columns

**Tests:**
- test_medicines.py (14 tests: CRUD, filters, search, inventory auto-creation, delete restrictions)

**Postman:**
- Medicines folder (Get All, Get by ID, Create, Update, Delete)

### Feature 6: Equipment
**Status:** Complete

**Endpoints:**
- GET `/api/v1/equipment` - List all equipment (paginated, filterable by category_id, is_active, condition, searchable)
- GET `/api/v1/equipment/{id}` - Get equipment by ID (includes inventory quantity, category name)
- POST `/api/v1/equipment` - Create equipment (auto-creates inventory record)
- PUT `/api/v1/equipment/{id}` - Update equipment
- DELETE `/api/v1/equipment/{id}` - Delete equipment (only if inventory quantity is 0)

**Model:**
- id, name, category_id (FK), description, condition (new/good/fair/poor), is_active, is_deleted, audit columns

**Tests:**
- test_equipment.py (13 tests: CRUD, condition filter, search, inventory, delete restrictions)

**Postman:**
- Equipment folder (Get All, Get by ID, Create, Update, Delete)

### Feature 7: Medical Devices
**Status:** Complete

**Endpoints:**
- GET `/api/v1/medical-devices` - List all medical devices (paginated, filterable, searchable)
- GET `/api/v1/medical-devices/{id}` - Get device by ID (includes inventory quantity, category name)
- POST `/api/v1/medical-devices` - Create medical device (auto-creates inventory record)
- PUT `/api/v1/medical-devices/{id}` - Update medical device
- DELETE `/api/v1/medical-devices/{id}` - Delete medical device (only if inventory quantity is 0)

**Model:**
- id, name, category_id (FK), description, serial_number, is_active, is_deleted, audit columns

**Tests:**
- test_medical_devices.py (13 tests: CRUD, filters, serial_number, inventory, delete restrictions)

**Postman:**
- Medical Devices folder (Get All, Get by ID, Create, Update, Delete)

### Inventory (supporting feature)
**Status:** Complete

**Endpoints:**
- GET `/api/v1/inventory` - List all inventory records (paginated, filterable by item_type)
- GET `/api/v1/inventory/{id}` - Get inventory record by ID
- GET `/api/v1/inventory/item/{item_type}/{item_id}` - Get inventory by item type and ID

**Model:**
- id, item_type (medicine/equipment/medical_device), item_id, quantity, is_deleted, audit columns

**Tests:**
- test_inventory.py (10 tests: list, filter, pagination, get by item, auto-creation)

**Postman:**
- Inventory folder (Get All, Get by ID, Get by Item)

---

## Phase 3 Details

### Feature 8: Partners
**Status:** Complete

**Endpoints:**
- GET `/api/v1/partners` - List all partners (paginated, filterable by partner_type, organization_type, is_active, searchable)
- GET `/api/v1/partners/{id}` - Get partner by ID (includes donations summary if donor)
- POST `/api/v1/partners` - Create partner
- PUT `/api/v1/partners/{id}` - Update partner
- DELETE `/api/v1/partners/{id}` - Delete partner (soft delete)

**Model:**
- id, name (unique), partner_type (donor/referral/both), organization_type (NGO/organization/individual/hospital/medical_center)
- contact_person, phone, email, address, is_active, is_deleted, audit columns

**Tests:**
- test_partners.py (20 tests: CRUD, filters, search, pagination, duplicate name, validation)

**Postman:**
- Partners folder (Get All, Get by ID, Create, Update, Delete)

### Feature 9: Donations
**Status:** Complete

**Endpoints:**
- GET `/api/v1/donations` - List all donations (paginated, filterable by partner_id, donation_date, searchable)
- GET `/api/v1/donations/{id}` - Get donation by ID (includes items with item names)
- POST `/api/v1/donations` - Create donation with optional items (creates inventory transactions automatically)
- PUT `/api/v1/donations/{id}` - Update donation
- DELETE `/api/v1/donations/{id}` - Delete donation (soft delete, creates reversal transactions)
- GET `/api/v1/donations/{donation_id}/items` - List items for a donation
- POST `/api/v1/donations/{donation_id}/items` - Add item to donation (creates inventory transaction)
- PUT `/api/v1/donation-items/{id}` - Update donation item (adjusts via transactions)
- DELETE `/api/v1/donation-items/{id}` - Delete donation item (creates reversal transaction)

**Models:**
- Donation: id, partner_id (FK), donation_date, notes, is_deleted, audit columns
- DonationItem: id, donation_id (FK), item_type (medicine/equipment/medical_device), item_id, quantity, is_deleted, audit columns

**Notes:**
- Partner validation: any partner_type (donor/referral/both) is allowed for donations
- Inventory is updated exclusively through inventory_transactions (not direct modification)

**Tests:**
- test_donations.py (20 tests: CRUD, filters, items CRUD, inventory transactions, inventory reversal, partner validation)

**Postman:**
- Donations folder (Get All, Get by ID, Create, Update, Delete)
- Donation Items folder (Get Items, Add Item, Update Item, Delete Item)

### Inventory Transactions (supporting feature)
**Status:** Complete

**Endpoints:**
- GET `/api/v1/inventory-transactions` - List all transactions (paginated, filterable by transaction_type, item_type, item_id)
- GET `/api/v1/inventory-transactions/{id}` - Get transaction by ID
- POST `/api/v1/inventory-transactions` - Create transaction (auto-updates inventory: + for purchase/donation, - for others)
- DELETE `/api/v1/inventory-transactions/{id}` - Delete transaction (soft delete, reverses inventory change)

**Model:**
- id, transaction_type (purchase/donation/prescription/loss/breakage/expiration/destruction), item_type, item_id, quantity, notes, transaction_date, is_deleted, audit columns

**Notes:**
- This is the only way to modify inventory quantities
- Created automatically by donation item operations
- Can also be created manually via the API for purchases, losses, etc.

**Tests:**
- test_inventory_transactions.py (17 tests: CRUD, filters, purchase/donation increase, loss/breakage decrease, inventory floor at 0, deletion reversal)

**Postman:**
- Inventory Transactions folder (Get All, Get by ID, Create Purchase, Create Loss, Delete)

### Feature 10: Doctors
**Status:** Complete

**Endpoints:**
- GET `/api/v1/doctors` - List all doctors (paginated, filterable by type, is_active, partner_id, searchable)
- GET `/api/v1/doctors/{id}` - Get doctor by ID (includes partner name if partner_provided)
- POST `/api/v1/doctors` - Create doctor (partner_id required for partner_provided type)
- PUT `/api/v1/doctors/{id}` - Update doctor
- DELETE `/api/v1/doctors/{id}` - Delete doctor (soft delete)

**Model:**
- id, name (unique), specialization, phone, email, type (internal/external/partner_provided)
- partner_id (FK to partners, required for partner_provided), is_active, is_deleted, audit columns

**Tests:**
- test_doctors.py (20 tests: CRUD, filters, search, pagination, partner validation, type validation, duplicate name)

**Postman:**
- Doctors folder (Get All, Get by ID, Create Internal, Create Partner Provided, Update, Delete)

---

## Notes

- Update this file before finishing each feature
- Format: Endpoints → Tests → Postman requests
- All tests pass (Phase 1: 30 tests + Phase 2: 87 tests + Phase 3: ~77 tests)
