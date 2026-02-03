# MedBase Development Plan

## Phase 1: Foundation

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | Project Setup (BE) | FastAPI structure, Docker, database connection, Alembic | Pending |
| 2 | Project Setup (FE) | Angular structure, routing, reusable components (buttons, inputs, tables, dropdowns), sidebar | Pending |
| 3 | Users & Authentication | User CRUD, JWT auth, admin role, login/logout | Pending |

---

## Phase 2: Core Entities

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 4 | Inventory Categories | Categories for Medicines, Equipment, Medical Devices | Pending |
| 5 | Medicines | Medicine inventory items with category | Pending |
| 6 | Equipment | Equipment inventory items with category | Pending |
| 7 | Medical Devices | Medical device inventory items with category | Pending |

---

## Phase 3: Partners & Doctors

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 8 | Partners | Partner records (donors, referral partners, or both) | Pending |
| 9 | Donations | Donations with donated items (medicines, equipment, medical devices) | Pending |
| 10 | Doctors | Doctor records (clinic staff, external, partner-provided) | Pending |

---

## Phase 4: Patients

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 11 | Patients | Patient records and data | Pending |
| 12 | Patient Documents | Document upload and storage for patients | Pending |

---

## Phase 5: Appointments & Records

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 13 | Appointments | Appointments management | Pending |
| 14 | Vital Signs | Vital signs recording per appointment | Pending |
| 15 | Medical Records | Medical record per appointment | Pending |
| 16 | Appointment Flow | Page to process appointment: begin → vitals + record (optional) → treatment (optional) → complete. Usually vitals + record, sometimes treatment only | Pending |

---

## Phase 6: Transactions & Treatments

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 17 | Prescriptions | Prescribe medicines/devices (decreases inventory) | Pending |
| 18 | Inventory Transactions | Track inventory movement (prescribing, loss, breakage, expiration, purchase, etc.) | Pending |
| 19 | Treatments | External treatments via partners | Pending |

---

## Phase 7: Dashboard & Polish

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 20 | Dashboard | Summary statistics (inventory, appointments, donations, partners) | Pending |
| 21 | Final Testing & Polish | End-to-end testing, bug fixes, UI refinements | Pending |

---

## Notes

- Each feature = BE endpoints → BE tests → Postman requests → FE pages
- Update `BE.PROGRESS.md` and `FE.PROGRESS.md` after each feature
- Dependencies flow downward (later phases depend on earlier ones)

## PR Workflow

- **Each phase requires a Pull Request (PR)**
- Open a PR when all features in the phase are complete
- Phase ends only when the PR is merged
- PR will be merged after owner approval
