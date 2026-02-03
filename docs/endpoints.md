# MedBase API Endpoints

Base URL: `/api/v1`

All GET (list) endpoints support: `page`, `size`, `sort`, `search`, and resource-specific filters.

---

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login, returns JWT token |
| POST | `/auth/logout` | Logout, invalidate token |
| GET | `/auth/me` | Get current user info |

**Notes:**
- Token expires after 1 hour
- All other endpoints require valid JWT token in Authorization header

---

## Users (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user by ID |
| POST | `/users` | Create user |
| PUT | `/users/{id}` | Update user |
| DELETE | `/users/{id}` | Delete user |

**Notes:**
- Filters: `role`, `is_active`
- Admin cannot delete themselves

---

## Medicine Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medicine-categories` | List all categories |
| GET | `/medicine-categories/{id}` | Get category by ID |
| POST | `/medicine-categories` | Create category |
| PUT | `/medicine-categories/{id}` | Update category |
| DELETE | `/medicine-categories/{id}` | Delete category |

**Notes:**
- Cannot delete category if medicines are linked to it

---

## Equipment Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/equipment-categories` | List all categories |
| GET | `/equipment-categories/{id}` | Get category by ID |
| POST | `/equipment-categories` | Create category |
| PUT | `/equipment-categories/{id}` | Update category |
| DELETE | `/equipment-categories/{id}` | Delete category |

**Notes:**
- Cannot delete category if equipment items are linked to it

---

## Medical Device Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medical-device-categories` | List all categories |
| GET | `/medical-device-categories/{id}` | Get category by ID |
| POST | `/medical-device-categories` | Create category |
| PUT | `/medical-device-categories/{id}` | Update category |
| DELETE | `/medical-device-categories/{id}` | Delete category |

**Notes:**
- Cannot delete category if medical devices are linked to it

---

## Medicines

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medicines` | List all medicines |
| GET | `/medicines/{id}` | Get medicine by ID (includes inventory) |
| POST | `/medicines` | Create medicine |
| PUT | `/medicines/{id}` | Update medicine |
| DELETE | `/medicines/{id}` | Delete medicine |

**Notes:**
- Filters: `category_id`, `is_active`
- Creating a medicine automatically creates an inventory record
- Deleting only allowed if inventory quantity is 0

---

## Equipment

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/equipment` | List all equipment |
| GET | `/equipment/{id}` | Get equipment by ID (includes inventory) |
| POST | `/equipment` | Create equipment |
| PUT | `/equipment/{id}` | Update equipment |
| DELETE | `/equipment/{id}` | Delete equipment |

**Notes:**
- Filters: `category_id`, `is_active`, `condition`
- Creating equipment automatically creates an inventory record
- Deleting only allowed if inventory quantity is 0

---

## Medical Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medical-devices` | List all medical devices |
| GET | `/medical-devices/{id}` | Get medical device by ID (includes inventory) |
| POST | `/medical-devices` | Create medical device |
| PUT | `/medical-devices/{id}` | Update medical device |
| DELETE | `/medical-devices/{id}` | Delete medical device |

**Notes:**
- Filters: `category_id`, `is_active`
- Creating a device automatically creates an inventory record
- Deleting only allowed if inventory quantity is 0

---

## Inventory

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory` | List all inventory records |
| GET | `/inventory/{id}` | Get inventory record by ID |
| GET | `/inventory/item/{item_type}/{item_id}` | Get inventory by item |

**Notes:**
- Filters: `item_type`
- `item_type` values: `medicine`, `equipment`, `medical_device`
- Inventory records are created automatically when an item (medicine/equipment/device) is created
- Quantity is modified only through inventory transactions
- Deleted automatically with the item when quantity is 0

---

## Inventory Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory-transactions` | List all transactions |
| GET | `/inventory-transactions/{id}` | Get transaction by ID |
| POST | `/inventory-transactions` | Create transaction (updates inventory) |
| DELETE | `/inventory-transactions/{id}` | Delete transaction |

**Notes:**
- Filters: `transaction_type`, `item_type`, `item_id`
- `transaction_type` values: `purchase`, `donation`, `prescription`, `loss`, `breakage`, `expiration`, `destruction`
- Creating a transaction automatically updates inventory quantity (+ for purchase/donation, - for others)
- This is the only way to modify inventory quantities

---

## Partners

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/partners` | List all partners |
| GET | `/partners/{id}` | Get partner by ID (includes donations/treatments) |
| POST | `/partners` | Create partner |
| PUT | `/partners/{id}` | Update partner |
| DELETE | `/partners/{id}` | Delete partner |

**Notes:**
- Filters: `partner_type`, `organization_type`, `is_active`
- `partner_type` values: `donor`, `referral`, `both`
- `organization_type` values: `NGO`, `organization`, `individual`, `hospital`, `medical_center`
- GET by ID returns donations (if donor) and treatments (if referral)

---

## Donations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/donations` | List all donations |
| GET | `/donations/{id}` | Get donation by ID (includes items) |
| POST | `/donations` | Create donation with items |
| PUT | `/donations/{id}` | Update donation |
| DELETE | `/donations/{id}` | Delete donation |

**Notes:**
- Filters: `partner_id`, `donation_date`
- POST can include items array to create donation with items in one request
- Creates inventory transactions automatically
- Partner must have `partner_type` of `donor`, `referral` or `both`

---

## Donation Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/donations/{donation_id}/items` | List items for a donation |
| POST | `/donations/{donation_id}/items` | Add item to donation |
| PUT | `/donation-items/{id}` | Update donation item |
| DELETE | `/donation-items/{id}` | Delete donation item |

**Notes:**
- `item_type` values: `medicine`, `equipment`, `medical_device`
- Adding items updates inventory automatically

---

## Doctors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/doctors` | List all doctors |
| GET | `/doctors/{id}` | Get doctor by ID |
| POST | `/doctors` | Create doctor |
| PUT | `/doctors/{id}` | Update doctor |
| DELETE | `/doctors/{id}` | Delete doctor |

**Notes:**
- Filters: `type`, `is_active`, `partner_id`
- `type` values: `internal`, `external`, `partner_provided`
- If `partner_provided`, must include `partner_id`

---

## Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patients` | List all patients |
| GET | `/patients/{id}` | Get patient by ID |
| POST | `/patients` | Create patient |
| PUT | `/patients/{id}` | Update patient |
| DELETE | `/patients/{id}` | Delete patient |

**Notes:**
- Filters: `is_active`, `gender`
- Search searches: `first_name`, `last_name`, `phone`, `email`

---

## Patient Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patients/{patient_id}/documents` | List documents for patient |
| GET | `/patient-documents/{id}` | Get document by ID |
| POST | `/patients/{patient_id}/documents` | Upload document |
| DELETE | `/patient-documents/{id}` | Delete document |

**Notes:**
- Filters: `document_type`
- POST accepts multipart/form-data for file upload
- Returns file URL for download

---

## Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/appointments` | List all appointments |
| GET | `/appointments/{id}` | Get appointment by ID (includes vitals, record) |
| POST | `/appointments` | Create appointment |
| PUT | `/appointments/{id}` | Update appointment |
| PUT | `/appointments/{id}/status` | Update appointment status |
| DELETE | `/appointments/{id}` | Delete appointment |

**Notes:**
- Filters: `patient_id`, `doctor_id`, `partner_id`, `status`, `type`, `location`, `appointment_date`
- `status` values: `scheduled`, `in_progress`, `completed`, `cancelled`
- `type` values: `scheduled`, `walk_in`
- `location` values: `internal` (at clinic), `external` (with partner)

---

## Vital Signs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/appointments/{appointment_id}/vitals` | Get vitals for appointment |
| POST | `/appointments/{appointment_id}/vitals` | Add vitals to appointment |
| PUT | `/vital-signs/{id}` | Update vital signs |
| DELETE | `/vital-signs/{id}` | Delete vital signs |

**Notes:**
- One vital signs record per appointment
- All vital sign fields are optional
- Cannot edit if appointment is completed

---

## Medical Records

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medical-records` | List all medical records |
| GET | `/medical-records/{id}` | Get medical record by ID |
| GET | `/appointments/{appointment_id}/medical-record` | Get record for appointment |
| POST | `/appointments/{appointment_id}/medical-record` | Create record for appointment |
| PUT | `/medical-records/{id}` | Update medical record |
| DELETE | `/medical-records/{id}` | Delete medical record |

**Notes:**
- Filters: `patient_id`, `appointment_id`
- One medical record per appointment
- Cannot edit if appointment is completed

---

## Prescriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/prescriptions` | List all prescriptions |
| GET | `/prescriptions/{id}` | Get prescription by ID (includes items) |
| POST | `/prescriptions` | Create prescription with items |
| PUT | `/prescriptions/{id}` | Update prescription |
| DELETE | `/prescriptions/{id}` | Delete prescription |

**Notes:**
- Filters: `patient_id`, `medical_record_id`
- POST can include items array
- Creating prescription items decreases inventory automatically

---

## Prescription Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/prescriptions/{prescription_id}/items` | List items for prescription |
| POST | `/prescriptions/{prescription_id}/items` | Add item to prescription |
| PUT | `/prescription-items/{id}` | Update prescription item |
| DELETE | `/prescription-items/{id}` | Delete prescription item |

**Notes:**
- `item_type` values: `medicine`, `medical_device`
- `dosage` field only for medicines
- Adding items decreases inventory automatically

---

## Treatments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/treatments` | List all treatments |
| GET | `/treatments/{id}` | Get treatment by ID |
| POST | `/treatments` | Create treatment |
| PUT | `/treatments/{id}` | Update treatment |
| PUT | `/treatments/{id}/status` | Update treatment status |
| DELETE | `/treatments/{id}` | Delete treatment |

**Notes:**
- Filters: `patient_id`, `partner_id`, `appointment_id`, `status`
- `status` values: `pending`, `in_progress`, `completed`, `cancelled`
- Can optionally link to an appointment
- Partner must have `partner_type` of `referral` or `both`

---

## Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Get summary statistics |
| GET | `/dashboard/inventory` | Inventory stats |
| GET | `/dashboard/appointments` | Appointment stats |
| GET | `/dashboard/donations` | Donation stats |

**Notes:**
- Summary includes counts for: patients, appointments, inventory items, donations, partners
- Inventory stats: low stock alerts, items by type
- Appointment stats: today's appointments, upcoming, by status
- Donation stats: recent donations, total items donated
