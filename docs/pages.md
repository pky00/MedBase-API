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

---

## Style Guide

No external UI frameworks (no Bootstrap, no Material). Fully custom design system using SCSS variables and mixins.

### Font

- **Family**: Inter (Google Fonts), fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Base size**: 16px (html root)
- **Rendering**: `-webkit-font-smoothing: antialiased`

### Font Sizes

| Token | Size |
|-------|------|
| xs | 0.75rem (12px) |
| sm | 0.875rem (14px) |
| base | 1rem (16px) |
| lg | 1.125rem (18px) |
| xl | 1.25rem (20px) |
| 2xl | 1.5rem (24px) |
| 3xl | 1.875rem (30px) |

### Font Weights

| Token | Weight |
|-------|--------|
| normal | 400 |
| medium | 500 |
| semibold | 600 |
| bold | 700 |

### Line Heights

| Token | Value |
|-------|-------|
| tight | 1.25 (headings) |
| normal | 1.5 (body text) |
| relaxed | 1.75 |

---

### Color Palette

#### Primary Blue (Brand)

| Token | Hex |
|-------|-----|
| primary-50 | #E3F2FD |
| primary-100 | #BBDEFB |
| primary-200 | #90CAF9 |
| primary-300 | #64B5F6 |
| primary-400 | #42A5F5 |
| primary-500 | #2196F3 |
| primary-600 | #1E88E5 |
| primary-700 | #1976D2 (main primary) |
| primary-800 | #1565C0 (hover states) |
| primary-900 | #0D47A1 |

#### Backgrounds

| Token | Hex | Usage |
|-------|-----|-------|
| background-white | #FFFFFF | Main content background |
| background-light | #F5F7FA | Page background, secondary areas |
| background-hover | #EEF2F6 | Hover state backgrounds |
| background-blue-tint | #E3F2FD | Subtle blue tinted backgrounds |

#### Text

| Token | Hex | Usage |
|-------|-----|-------|
| text-primary | #212121 | Main text |
| text-secondary | #757575 | Labels, secondary text |
| text-disabled | #BDBDBD | Disabled inputs |
| text-hint | #9E9E9E | Placeholders, hints |
| text-on-primary | #FFFFFF | Text on blue backgrounds |

#### Status / Semantic

| Status | Main | Light | Dark |
|--------|------|-------|------|
| Success | #4CAF50 | #E8F5E9 | #388E3C |
| Warning | #FF9800 | #FFF3E0 | #F57C00 |
| Error | #F44336 | #FFEBEE | #D32F2F |
| Info | #2196F3 | #E3F2FD | #1976D2 |

#### Borders

| Token | Hex |
|-------|-----|
| border-light | #E0E0E0 (default borders) |
| border-default | #BDBDBD |
| border-focus | #2196F3 (on focus) |

---

### Spacing Scale

| Token | Value |
|-------|-------|
| xs | 0.25rem (4px) |
| sm | 0.5rem (8px) |
| md | 1rem (16px) |
| lg | 1.5rem (24px) |
| xl | 2rem (32px) |
| 2xl | 3rem (48px) |

### Border Radius

| Token | Value |
|-------|-------|
| sm | 0.25rem (4px) |
| md | 0.5rem (8px) — inputs, buttons |
| lg | 0.75rem (12px) — cards |
| xl | 1rem (16px) — modals, large cards |
| full | 9999px — pills, avatars |

### Shadows

| Token | Value |
|-------|-------|
| sm | 0 1px 3px rgba(0,0,0,0.1) |
| md | 0 4px 6px rgba(0,0,0,0.1) |
| lg | 0 10px 15px rgba(0,0,0,0.1) |
| xl | 0 20px 25px rgba(0,0,0,0.1) |

### Transitions

| Token | Value |
|-------|-------|
| fast | 150ms ease-in-out |
| normal | 250ms ease-in-out |

---

### Layout Dimensions

| Token | Value |
|-------|-------|
| sidebar-width | 260px |
| header-height | 64px |
| z-fixed | 100 (header, sidebar) |
| z-modal | 200 (modals, dropdowns) |

---

### Component Styles

#### Sidebar

- Position: fixed, left: 0, top: 0, height: 100vh
- Width: 260px
- Background: white, border-right: 1px solid border-light
- Overflow-y: auto with custom scrollbar

**Logo area:**
- Padding: 1.5rem, border-bottom: 1px solid border-light
- Logo icon: 36x36px, background gradient (135deg, #2196F3 → #1976D2), border-radius: md
- Logo text: font-size xl (20px), weight bold, color primary-700

**Nav groups:**
- Group title: font-size xs (12px), weight semibold, color text-hint, uppercase, letter-spacing 0.05em, padding 0.5rem 1.5rem
- Nav items: padding 0.5rem 1.5rem, margin 0 0.5rem, color text-secondary, border-radius md, gap 0.5rem
- Nav item hover: background background-hover, color text-primary
- Nav item active: background primary-50, color primary-700

#### Header

- Position: fixed, top: 0, left: sidebar-width, right: 0
- Height: 64px, background white, border-bottom 1px solid border-light
- Padding: 0 1.5rem, z-index 100
- Title: font-size lg (18px), weight semibold, color text-primary

**User avatar:**
- 32px circle, background gradient (135deg, #2196F3 → #1976D2), white text, font-size sm
- Menu dropdown: width 280px, border-radius lg, shadow-lg, z-index 200

#### Main Layout

- `.layout`: flex, min-height 100vh, background background-light
- `.layout-main`: flex 1, margin-left sidebar-width
- `.layout-content`: padding 1.5rem, margin-top header-height

---

#### Buttons

**Primary (.btn-primary):**
- Padding: 0.5rem 1rem
- Background: primary-700 (#1976D2), color white
- Font-size: sm (14px), weight medium, border: none, border-radius: md
- Hover: background primary-800 (#1565C0)
- Disabled: opacity 0.5, cursor not-allowed
- Focus: 2px solid outline primary-500, offset 2px
- Icon gap: 0.5rem

**Secondary (.btn-secondary):**
- Same padding/size as primary
- Background: white, color primary-700, border: 1px solid primary-700
- Hover: background primary-50

**Ghost (.btn-ghost):**
- Background: transparent, color text-primary
- Hover: background background-hover

---

#### Form Inputs

**Base input:**
- Width: 100%, padding: 0.5rem 1rem
- Font: Inter, size base (16px), color text-primary
- Background: white, border: 1px solid border-default, border-radius: md
- Placeholder color: text-hint

**Focus:** border-color primary-500, box-shadow `0 0 0 3px rgba(33,150,243,0.15)`
**Disabled:** background background-light, color text-disabled, cursor not-allowed
**Error:** border-color error, focus shadow `0 0 0 3px rgba(244,67,54,0.1)`

**Select inputs:** appearance none, custom SVG dropdown arrow, padding-right extra for arrow

**Labels:** font-size sm (14px), weight medium, color text-secondary, margin-bottom xs
**Required indicator (*):** color error, margin-left 2px
**Error messages:** font-size xs (12px), color error, margin-top xs

**Form grid:** display grid, 2 columns, gap 1rem. Mobile (max-width 640px): 1 column
**Form actions bar:** flex, justify-content flex-end, gap 1rem, padding 1.5rem, background background-light, border-top 1px solid border-light

---

#### Cards

- Background: white, border: 1px solid border-light, border-radius: lg, shadow-sm, padding: 1.5rem
- Hover effect (dashboard cards): transform translateY(-4px), shadow-lg, transition fast

---

#### Data Table

**Header (th):**
- Padding: 1rem, font-size sm (14px), weight semibold
- Color: text-secondary, background: background-light
- Border-bottom: 1px solid border-light, white-space: nowrap

**Data cells (td):**
- Padding: 1rem, font-size sm (14px), color text-primary
- Border-bottom: 1px solid border-light

**Sortable headers:** cursor pointer, user-select none, hover background background-hover
**Sorted headers:** color primary-700, background primary-50

**Row hover:** background background-hover

**Action buttons:** padding 0.25rem, background transparent, border-radius sm, color text-secondary
- Hover: background background-light, color primary-700
- Delete hover: background rgba(244,67,54,0.1), color error

---

#### Pagination

- Flex, space-between, align-items center, margin-top 1.5rem, padding 1rem, gap 1rem
- Buttons: padding 0.25rem, border-radius md, color text-secondary, no border/background
- Hover: background background-hover, color primary-700
- Disabled: opacity 0.5, cursor not-allowed

---

#### Badges

**General badge style:** inline-block, padding 2px 8px, border-radius sm or full, font-size xs (12px), weight medium, text-transform capitalize

**Gender:** Male: #3b82f6 text + 10% opacity bg. Female: #ec4899 text + 10% opacity bg

**Appointment status:**
- Scheduled: #3b82f6 (blue)
- Completed: #10b981 (green)
- Cancelled: #6b7280 (gray)
- No Show: #f59e0b (amber)
- Rescheduled: #8b5cf6 (purple)

**Equipment condition:**
- New: #10b981 (green)
- Excellent: #3b82f6 (blue)
- Good: #8b5cf6 (purple)
- Fair: #f59e0b (amber)
- Needs Repair: #ef4444 (red)
- Out of Service: gray

**Donor type:**
- Individual: primary-50 bg
- Organization: info-light bg
- Government: warning-light bg
- NGO: success-light bg
- Pharmaceutical Company: #F3E5F5 bg

---

#### Stat Cards (Dashboard)

- Flex, align center, gap 1rem, padding 1.5rem
- Icon container: 48x48px, border-radius lg, gradient backgrounds:
  - Blue: 135deg #2196F3 → #1976D2
  - Green: 135deg #4CAF50 → #388E3C
  - Orange: 135deg #FF9800 → #F57C00
  - Purple: 135deg #9C27B0 → #7B1FA2
  - Red: 135deg #F44336 → #D32F2F
  - Teal: 135deg #009688 → #00796B
- Stat value: font-size 2xl (24px), weight bold, color text-primary

---

#### Alerts

**Error alert:**
- Background: rgba(244,67,54,0.1), color error, border: 1px solid rgba(244,67,54,0.2)
- Border-radius: md, padding: 1rem, flex with gap 0.5rem, margin-bottom 1.5rem

---

#### Loading Spinner

- 32x32px, border: 3px solid border-light, border-top-color: primary-500
- Border-radius: 50%, animation: spin 0.8s linear infinite
- Small variant: 16x16px, border 2px

---

#### Empty States

- Text-align center, padding 3rem (2xl), color text-hint
- Icon: 48px, margin-bottom 0.5rem

---

#### Custom Scrollbar

```
width: 6px
track: background-light
thumb: border-default, border-radius full
thumb hover: text-hint
```

---

### Page Structure Patterns

#### List Pages

- **Page header:** flex, space-between, align flex-start, margin-bottom 1.5rem, gap 1rem
- **Page title (h1):** font-size 1.75rem (28px), weight semibold, color text-primary
- **Page subtitle:** font-size sm (14px), color text-secondary, margin-top xs
- **Filters bar:** flex, gap 1rem, margin-bottom 1.5rem, flex-wrap
- **Search box:** flex 1, min-width 250px, max-width 400px, search icon positioned absolute left

#### Form Pages

- **Container:** background white, border-radius lg, border 1px solid border-light
- **Section:** padding 1.5rem, border-bottom 1px solid border-light (last section no border)
- **Section title:** font-size base (16px), weight semibold, color text-primary, margin-bottom 1rem

---

### Responsive Breakpoints

| Breakpoint | Usage |
|------------|-------|
| max-width: 1200px | Split layouts stack vertically |
| max-width: 640px | Form grids collapse to 1 column, mobile adjustments |
