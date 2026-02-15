# MedBase Development Plan

## Phase 1: Foundation

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 1 | Project Setup (BE) | FastAPI structure, Docker, database connection, Alembic | Done | - |
| 2 | Project Setup (FE) | Angular structure, routing, reusable components (buttons, inputs, tables, dropdowns), sidebar | - | Pending |
| 3 | Third Parties | Base identity table for all persons/entities (users, doctors, patients, partners). Created automatically when any linked entity is created | Done | Pending |
| 4 | Users & Authentication | User CRUD, JWT auth, admin role, login/logout. Each user gets a third_party record | Done | Pending |

---

## Phase 2: Core Entities

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 5 | Inventory Categories | Categories for Medicines, Equipment, Medical Devices | Done | Pending |
| 6 | Medicines | Medicine inventory items with category | Done | Pending |
| 7 | Equipment | Equipment inventory items with category | Done | Pending |
| 8 | Medical Devices | Medical device inventory items with category | Done | Pending |

---

## Phase 3: Partners & Doctors

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 9 | Partners | Partner records (donors, referral partners, or both). Each partner gets a third_party record | Pending | Pending |
| 10 | Doctors | Doctor records (clinic staff, external, partner-provided). Each doctor gets a third_party record | Pending | Pending |

### Inventory Transactions — Migration Notes

**What changed from the original plan:**

The original plan had separate `donations`/`donation_items` tables, separate `prescriptions`/`prescription_items` tables, and a flat `inventory_transactions` table (one item per row, no header). All of these have been replaced with a unified two-table design:

| Old Tables (REMOVED) | New Tables (REPLACED WITH) |
|---|---|
| `donations` (header: partner_id, date, notes) | `inventory_transactions` (header: transaction_type, third_party_id, date, notes) |
| `donation_items` (line items: item_type, item_id, quantity) | `inventory_transaction_items` (line items: item_type, item_id, quantity) |
| `prescriptions` (header: medical_record_id, patient_id, date, notes) | `inventory_transactions` with `transaction_type = prescription` |
| `prescription_items` (line items: item_type, item_id, quantity, dosage) | `inventory_transaction_items` |
| `inventory_transactions` (flat: one item per row) | _(merged into the above two tables)_ |

**How it works now:**

- `inventory_transactions` — contains general transaction data (type, date, who, notes). Has a `third_party_id` (not `partner_id`) that links to the `third_parties` table.
- `inventory_transaction_items` — contains individual items in a transaction (item_type, item_id, quantity). Each item belongs to one transaction via `transaction_id`.

**`third_party_id` rules per transaction type:**

| Transaction Type | `third_party_id` must be | How it's set |
|---|---|---|
| `donation` | A donor partner's third_party (partner with `partner_type` = `donor` or `both`) | Provided in request |
| `prescription` | A doctor's third_party | Provided in request |
| `purchase`, `loss`, `breakage`, `expiration`, `destruction` | The logged-in user's third_party | Set automatically from current user |

**Key points for implementation:**
- Donations are NO longer a separate resource — they are inventory transactions with `transaction_type = donation`
- Prescriptions are NO longer a separate resource — they are inventory transactions with `transaction_type = prescription`
- There are NO `donations`, `donation_items`, `prescriptions`, or `prescription_items` tables/models/endpoints
- All inventory movement goes through the `inventory_transactions` + `inventory_transaction_items` tables
- The old `inventory_transactions` flat table (one item per row) is replaced by the header + items pattern

---

## Phase 4: Patients

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 11 | Patients | Patient records and data. Each patient gets a third_party record | Pending | Pending |
| 12 | Patient Documents | Document upload and storage for patients | Pending | Pending |

---

## Phase 5: Appointments & Records

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 13 | Appointments | Appointments management | Pending | Pending |
| 14 | Vital Signs | Vital signs recording per appointment | Pending | Pending |
| 15 | Medical Records | Medical record per appointment | Pending | Pending |
| 16 | Appointment Flow | Page to process appointment: begin → vitals + record (optional) → treatment (optional) → complete. Usually vitals + record, sometimes treatment only | Pending | Pending |

---

## Phase 6: Inventory Transactions & Treatments

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 17 | Inventory Transactions | Inventory transactions with transaction items (see migration notes below) | Pending | Pending |
| 18 | Treatments | External treatments via partners | Pending | Pending |

---

## Phase 7: Dashboard & Polish

| # | Feature | Description | BE | FE |
|---|---------|-------------|----|----|
| 19 | Dashboard | Summary statistics (inventory, appointments, transactions, partners) | Pending | Pending |
| 20 | Final Testing & Polish | End-to-end testing, bug fixes, UI refinements | Pending | Pending |

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
