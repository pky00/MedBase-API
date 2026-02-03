# MedBase Frontend Pages

## General Layout

- **Sidebar**: Navigation to all resource list pages
- **Two-column layout**: View/Edit/Create pages have left (main data) and right (related items)
- **Mobile responsive design**
- **Theme**: White and blue color scheme

---

## Authentication

### Login Page
- Username/email input
- Password input
- Login button
- Error messages for invalid credentials

---

## Dashboard

### Dashboard Page
- Summary cards: patients count, appointments today, inventory alerts, donations count
- Quick stats widgets
- Recent activity or upcoming appointments

---

## Users (Admin Only)

### Users List Page
- Table with columns: username, email, role, is_active, actions
- Filters: role, is_active
- Actions: View, Edit, Delete

### User Create/Edit Page
- Form fields: username, email, password, role, is_active

### User View Page
- Left: User details
- Right: N/A

---

## Inventory Categories

### Medicine Categories List Page
- Table with columns: name, description, actions
- Actions: View, Edit, Delete

### Medicine Category Create/Edit Page
- Form fields: name, description

### Equipment Categories List Page
- Same structure as Medicine Categories

### Medical Device Categories List Page
- Same structure as Medicine Categories

---

## Inventory Items

### Medicines List Page
- Table with columns: name, category, unit, quantity, is_active, actions
- Filters: category_id, is_active
- Actions: View, Edit, Delete

### Medicine Create/Edit Page
- Form fields: name, category (dropdown), description, unit, is_active

### Medicine View Page
- Left: Medicine details + inventory quantity
- Right: Inventory transactions history

### Equipment List Page
- Table with columns: name, category, condition, quantity, is_active, actions
- Filters: category_id, is_active, condition
- Actions: View, Edit, Delete

### Equipment Create/Edit Page
- Form fields: name, category (dropdown), description, condition, is_active

### Equipment View Page
- Left: Equipment details + inventory quantity
- Right: Inventory transactions history

### Medical Devices List Page
- Table with columns: name, category, serial_number, quantity, is_active, actions
- Filters: category_id, is_active
- Actions: View, Edit, Delete

### Medical Device Create/Edit Page
- Form fields: name, category (dropdown), description, serial_number, is_active

### Medical Device View Page
- Left: Device details + inventory quantity
- Right: Inventory transactions history

---

## Inventory

### Inventory List Page
- Table with columns: item_type, item_name, quantity
- Filters: item_type
- Read-only (no create/edit/delete)

### Inventory Transactions List Page
- Table with columns: transaction_type, item_type, item_name, quantity, date, actions
- Filters: transaction_type, item_type
- Actions: View, Delete

### Inventory Transaction Create Page
- Form fields: transaction_type (dropdown), item_type (dropdown), item (dropdown), quantity, notes

---

## Partners

### Partners List Page
- Table with columns: name, partner_type, organization_type, is_active, actions
- Filters: partner_type, organization_type, is_active
- Actions: View, Edit, Delete

### Partner Create/Edit Page
- Form fields: name, partner_type, organization_type, contact_person, phone, email, address, is_active

### Partner View Page
- Left: Partner details
- Right: 
  - If donor: Donation cards with summary
  - If referral: Treatments list
  - If both: Tabs for donations and treatments

---

## Donations

### Donations List Page
- Table with columns: partner_name, donation_date, items_count, actions
- Filters: partner_id, donation_date
- Actions: View, Edit, Delete

### Donation Create/Edit Page
- Left: Form fields: partner (dropdown), donation_date, notes
- Right: Items table with add/remove functionality
  - Each item: item_type, item (dropdown), quantity

### Donation View Page
- Left: Donation details
- Right: Table of donated items

---

## Doctors

### Doctors List Page
- Table with columns: name, specialization, type, is_active, actions
- Filters: type, is_active
- Actions: View, Edit, Delete

### Doctor Create/Edit Page
- Form fields: name, specialization, phone, email, type, partner (dropdown, if partner_provided), is_active

### Doctor View Page
- Left: Doctor details
- Right: N/A (or appointments if needed)

---

## Patients

### Patients List Page
- Table with columns: name, phone, email, is_active, actions
- Filters: is_active, gender
- Search: first_name, last_name, phone, email
- Actions: View, Edit, Delete

### Patient Create/Edit Page
- Form fields: first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, emergency_phone, is_active

### Patient View Page
- Left: Patient details
- Right: Tabs for:
  - Documents (upload/list)
  - Appointments history
  - Medical records

---

## Appointments

### Appointments List Page
- Table with columns: patient, doctor, date, status, type, location, actions
- Filters: patient_id, doctor_id, status, type, location, date
- Actions: View, Edit, Delete, Process (go to flow)

### Appointment Create/Edit Page
- Form fields: patient (dropdown), doctor (dropdown), partner (dropdown, if external), date, type, location, notes

### Appointment View Page
- Left: Appointment details
- Right: Vital signs, medical record, treatment (if any)

### Appointment Flow Page
- Step-by-step process:
  1. Begin appointment (change status to in_progress)
  2. Add vital signs (optional)
  3. Enter medical record (optional)
  4. Add treatment (optional)
  5. Complete appointment (change status to completed)
- Cannot edit after completed

---

## Vital Signs

- Managed within Appointment Flow Page
- Form fields: blood_pressure (systolic/diastolic), heart_rate, temperature, respiratory_rate, weight, height, notes

---

## Medical Records

### Medical Records List Page
- Table with columns: patient, appointment_date, diagnosis, actions
- Filters: patient_id
- Actions: View, Edit

### Medical Record View Page
- Left: Record details (chief_complaint, diagnosis, treatment_notes, follow_up_date)
- Right: Prescription items

---

## Prescriptions

### Prescriptions List Page
- Table with columns: patient, date, items_count, actions
- Filters: patient_id
- Actions: View, Edit, Delete

### Prescription Create/Edit Page
- Left: Form fields: patient (auto from medical record), date, notes
- Right: Items table with add/remove
  - Each item: item_type, item (dropdown), quantity, dosage (for medicines), instructions

### Prescription View Page
- Left: Prescription details
- Right: Table of prescription items

---

## Treatments

### Treatments List Page
- Table with columns: patient, partner, treatment_type, date, status, actions
- Filters: patient_id, partner_id, status
- Actions: View, Edit, Delete

### Treatment Create/Edit Page
- Form fields: patient (dropdown), partner (dropdown), appointment (dropdown, optional), treatment_type, description, date, status, cost, notes

### Treatment View Page
- Left: Treatment details
- Right: N/A

---

## Reusable Components

### Button Component
- Variants: primary, secondary, danger
- States: normal, hover, disabled, loading

### Input Component
- Types: text, number, email, password, date, textarea
- States: normal, focus, error, disabled

### Dropdown Component
- Paginated API calls (page size 50)
- "View More..." button for next page
- Search after 3+ characters (API call)
- Clear selection option

### Table Component
- Sortable columns (click header)
- Action buttons per row
- Pagination
- Loading state
- Empty state

### Card Component
- For summary displays (donations, stats)

### Modal Component
- For confirmations (delete), quick forms

### Sidebar Component
- Links to all list pages
- Collapsible on mobile
