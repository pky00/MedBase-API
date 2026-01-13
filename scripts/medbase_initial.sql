-- ============================================================================
-- MEDBASE CLINIC MANAGEMENT DATABASE
-- PostgreSQL Database Schema
-- ============================================================================

-- Drop database if exists and create fresh (uncomment if needed)
-- DROP DATABASE IF EXISTS medbase_clinic;
-- CREATE DATABASE medbase_clinic;

-- Connect to the database
-- \c medbase_clinic;

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CUSTOM TYPES (ENUMS)
-- ============================================================================

CREATE TYPE gender_type AS ENUM ('male', 'female');

CREATE TYPE blood_type AS ENUM ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown');

CREATE TYPE appointment_status AS ENUM (
    'scheduled',
    'completed',
    'cancelled',
    'no_show',
    'rescheduled'
);

CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced', 'widowed');

CREATE TYPE donor_type AS ENUM ('individual', 'organization', 'government', 'ngo', 'pharmaceutical_company');

CREATE TYPE donation_type AS ENUM ('medicine', 'equipment', 'medical_device', 'mixed');

CREATE TYPE equipment_condition AS ENUM ('new', 'excellent', 'good', 'fair', 'needs_repair', 'out_of_service');

CREATE TYPE document_type AS ENUM (
    'lab_result',
    'imaging',
    'prescription',
    'referral',
    'consent_form',
    'insurance_document',
    'identification',
    'medical_history',
    'discharge_summary',
    'other'
);

CREATE TYPE severity AS ENUM ('mild', 'moderate', 'severe', 'life_threatening');

CREATE TYPE dosage_form AS ENUM (
    'tablet',
    'capsule',
    'syrup',
    'injection',
    'cream',
    'ointment',
    'drops',
    'inhaler',
    'patch',
    'suppository',
    'powder',
    'solution',
    'suspension',
    'gel',
    'spray',
    'other'
);

CREATE TYPE inventory_transaction_type AS ENUM (
    'perscribed',
    'donated',
    'expired',
    'damaged',
    'returned',
    'purchased',
    'lost',
    'stolen'
);

CREATE TYPE reference_type AS ENUM (
    'prescription',
    'donation',
    'adjustment',
    'transfer',
    'disposal'
);

CREATE TYPE appointment_type AS ENUM (
    'consultation',
    'follow_up',
    'emergency',
    'checkup'
);

CREATE TYPE prescription_status AS ENUM (
    'pending',
    'dispensed',
    'cancelled'
);

-- ============================================================================
-- USERS TABLE (System Access)
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

-- Create index for faster lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================================================
-- DOCTORS TABLE
-- ============================================================================
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    donor_id UUID, -- Optional: if doctor is provided/sponsored by a donor
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender gender_type,
    specialization VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    qualification TEXT,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_doctors_user_id ON doctors(user_id);
CREATE INDEX idx_doctors_donor_id ON doctors(donor_id);
CREATE INDEX idx_doctors_specialization ON doctors(specialization);
CREATE INDEX idx_doctors_name ON doctors(last_name, first_name);

-- ============================================================================
-- PATIENTS TABLE
-- ============================================================================
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender gender_type NOT NULL,
    blood_type blood_type DEFAULT 'unknown',
    national_id VARCHAR(50),
    passport_number VARCHAR(50),
    phone VARCHAR(20),
    alternative_phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Unknown',
    occupation VARCHAR(100),
    marital_status marital_status,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_patients_patient_number ON patients(patient_number);
CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_national_id ON patients(national_id);

-- ============================================================================
-- PATIENT ALLERGIES TABLE
-- ============================================================================
CREATE TABLE patient_allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    allergen VARCHAR(200) NOT NULL,
    reaction TEXT,
    severity severity NOT NULL DEFAULT 'moderate',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_patient_allergies_patient_id ON patient_allergies(patient_id);
CREATE INDEX idx_patient_allergies_allergen ON patient_allergies(allergen);

-- ============================================================================
-- PATIENT MEDICAL HISTORY TABLE
-- ============================================================================
CREATE TABLE patient_medical_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    condition_name VARCHAR(200) NOT NULL,
    icd_code VARCHAR(20),
    diagnosis_date DATE,
    resolution_date DATE,
    is_chronic BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT TRUE,
    severity severity,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_patient_medical_history_patient_id ON patient_medical_history(patient_id);
CREATE INDEX idx_patient_medical_history_condition ON patient_medical_history(condition_name);
CREATE INDEX idx_patient_medical_history_icd_code ON patient_medical_history(icd_code);

-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    appointment_type appointment_type DEFAULT 'consultation',
    status appointment_status DEFAULT 'scheduled',
    chief_complaint TEXT,
    notes TEXT,
    is_follow_up BOOLEAN DEFAULT FALSE,
    previous_appointment_id UUID REFERENCES appointments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_date_doctor ON appointments(appointment_date, doctor_id);
CREATE INDEX idx_appointments_date_patient ON appointments(appointment_date, patient_id);

-- ============================================================================
-- VITAL SIGNS TABLE
-- ============================================================================
CREATE TABLE vital_signs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    temperature_celsius DECIMAL(4, 1),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    pulse_rate INTEGER,
    respiratory_rate INTEGER,
    oxygen_saturation DECIMAL(5, 2),
    weight_kg DECIMAL(5, 2),
    height_cm DECIMAL(5, 1),
    bmi DECIMAL(4, 1),
    blood_glucose DECIMAL(5, 1),
    pain_level INTEGER CHECK (pain_level BETWEEN 0 AND 10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_vital_signs_patient_id ON vital_signs(patient_id);
CREATE INDEX idx_vital_signs_appointment_id ON vital_signs(appointment_id);
CREATE INDEX idx_vital_signs_recorded_at ON vital_signs(recorded_at);

-- ============================================================================
-- MEDICAL RECORDS TABLE (Visit Records)
-- ============================================================================
CREATE TABLE medical_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    visit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    chief_complaint TEXT,
    history_of_present_illness TEXT,
    physical_examination TEXT,
    assessment TEXT,
    diagnosis TEXT[],
    icd_codes VARCHAR(20)[],
    treatment_plan TEXT,
    procedures_performed TEXT,
    follow_up_instructions TEXT,
    follow_up_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medical_records_patient_id ON medical_records(patient_id);
CREATE INDEX idx_medical_records_doctor_id ON medical_records(doctor_id);
CREATE INDEX idx_medical_records_appointment_id ON medical_records(appointment_id);
CREATE INDEX idx_medical_records_visit_date ON medical_records(visit_date);

-- ============================================================================
-- MEDICINE CATEGORIES TABLE
-- ============================================================================
CREATE TABLE medicine_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES medicine_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medicine_categories_name ON medicine_categories(name);
CREATE INDEX idx_medicine_categories_parent ON medicine_categories(parent_category_id);

-- ============================================================================
-- MEDICINES TABLE
-- ============================================================================
CREATE TABLE medicines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    brand_name VARCHAR(200),
    category_id UUID REFERENCES medicine_categories(id) ON DELETE SET NULL,
    manufacturer VARCHAR(200),
    dosage_form dosage_form NOT NULL,
    strength VARCHAR(100),
    unit VARCHAR(50) NOT NULL, -- e.g., mg, ml, g
    package_size VARCHAR(100),
    barcode VARCHAR(100),
    purchase_price DECIMAL(12, 2),
    description TEXT,
    indications TEXT,
    contraindications TEXT,
    side_effects TEXT,
    storage_conditions TEXT,
    requires_prescription BOOLEAN DEFAULT TRUE,
    is_controlled_substance BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medicines_name ON medicines(name);
CREATE INDEX idx_medicines_generic_name ON medicines(generic_name);
CREATE INDEX idx_medicines_category_id ON medicines(category_id);
CREATE INDEX idx_medicines_barcode ON medicines(barcode);
CREATE INDEX idx_medicines_is_active ON medicines(is_active);

-- ============================================================================
-- DONORS TABLE
-- ============================================================================
CREATE TABLE donors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donor_code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    donor_type donor_type NOT NULL DEFAULT 'individual',
    contact_person VARCHAR(200),
    phone VARCHAR(20),
    alternative_phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_donors_name ON donors(name);
CREATE INDEX idx_donors_donor_type ON donors(donor_type);
CREATE INDEX idx_donors_is_active ON donors(is_active);

-- ============================================================================
-- MEDICINE INVENTORY TABLE
-- ============================================================================
CREATE TABLE medicine_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medicine_id UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medicine_inventory_medicine_id ON medicine_inventory(medicine_id);

-- ============================================================================
-- MEDICINE EXPIRY TABLE
-- ============================================================================
CREATE TABLE medicine_expiry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medicine_id UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    batch_number VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 0,
    expiry_date DATE NOT NULL,
    actual_expiry_date DATE NOT NULL,
    manufacturing_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medicine_expiry_medicine_id ON medicine_expiry(medicine_id);
CREATE INDEX idx_medicine_expiry_expiry_date ON medicine_expiry(expiry_date);
CREATE INDEX idx_medicine_expiry_batch ON medicine_expiry(batch_number);

-- ============================================================================
-- MEDICAL DEVICE CATEGORIES TABLE
-- ============================================================================
CREATE TABLE medical_device_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES medical_device_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medical_device_categories_name ON medical_device_categories(name);
CREATE INDEX idx_medical_device_categories_parent ON medical_device_categories(parent_category_id);

-- ============================================================================
-- MEDICAL DEVICES TABLE (Prescribable devices like wheelchairs, walkers, braces)
-- ============================================================================
CREATE TABLE medical_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    category_id UUID REFERENCES medical_device_categories(id) ON DELETE SET NULL,
    manufacturer VARCHAR(200),
    model VARCHAR(100),
    description TEXT,
    specifications TEXT,
    size VARCHAR(50), -- e.g., S, M, L, XL or specific measurements
    is_reusable BOOLEAN DEFAULT TRUE,
    requires_fitting BOOLEAN DEFAULT FALSE,
    purchase_price DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medical_devices_name ON medical_devices(name);
CREATE INDEX idx_medical_devices_category_id ON medical_devices(category_id);
CREATE INDEX idx_medical_devices_is_active ON medical_devices(is_active);

-- ============================================================================
-- MEDICAL DEVICE INVENTORY TABLE
-- ============================================================================
CREATE TABLE medical_device_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES medical_devices(id) ON DELETE CASCADE,
    serial_number VARCHAR(100),
    condition equipment_condition DEFAULT 'good',
    is_donation BOOLEAN DEFAULT FALSE,
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    notes TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_medical_device_inventory_device_id ON medical_device_inventory(device_id);
CREATE INDEX idx_medical_device_inventory_is_available ON medical_device_inventory(is_available);
CREATE INDEX idx_medical_device_inventory_donor_id ON medical_device_inventory(donor_id);

-- ============================================================================
-- PRESCRIBED DEVICES TABLE (Devices issued to patients)
-- ============================================================================
CREATE TABLE prescribed_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES medical_devices(id) ON DELETE CASCADE,
    prescription_date DATE NOT NULL DEFAULT CURRENT_DATE,
    issue_date DATE,
    return_date DATE,
    expected_return_date DATE,
    is_permanent BOOLEAN DEFAULT FALSE, -- If true, patient keeps the device
    condition_on_issue equipment_condition,
    condition_on_return equipment_condition,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_prescribed_devices_patient_id ON prescribed_devices(patient_id);
CREATE INDEX idx_prescribed_devices_doctor_id ON prescribed_devices(doctor_id);
CREATE INDEX idx_prescribed_devices_device_id ON prescribed_devices(device_id);
CREATE INDEX idx_prescribed_devices_prescription_date ON prescribed_devices(prescription_date);

-- ============================================================================
-- EQUIPMENT CATEGORIES TABLE
-- ============================================================================
CREATE TABLE equipment_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES equipment_categories(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_equipment_categories_name ON equipment_categories(name);
CREATE INDEX idx_equipment_categories_parent ON equipment_categories(parent_category_id);

-- ============================================================================
-- EQUIPMENT TABLE
-- ============================================================================
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    category_id UUID REFERENCES equipment_categories(id) ON DELETE SET NULL,
    model VARCHAR(100),
    manufacturer VARCHAR(200),
    serial_number VARCHAR(100),
    barcode VARCHAR(100),
    description TEXT,
    purchase_date DATE,
    purchase_price DECIMAL(12, 2),
    is_donation BOOLEAN DEFAULT FALSE,
    donor_id UUID REFERENCES donors(id) ON DELETE SET NULL,
    donation_id UUID, -- Will reference donations table
    equipment_condition equipment_condition DEFAULT 'good',
    is_portable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_equipment_name ON equipment(name);
CREATE INDEX idx_equipment_category_id ON equipment(category_id);
CREATE INDEX idx_equipment_serial_number ON equipment(serial_number);
CREATE INDEX idx_equipment_is_donation ON equipment(is_donation);
CREATE INDEX idx_equipment_donor_id ON equipment(donor_id);
CREATE INDEX idx_equipment_condition ON equipment(equipment_condition);
CREATE INDEX idx_equipment_is_active ON equipment(is_active);

-- ============================================================================
-- DONATIONS TABLE
-- ============================================================================
CREATE TABLE donations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donation_number VARCHAR(50) UNIQUE NOT NULL,
    donor_id UUID NOT NULL REFERENCES donors(id) ON DELETE CASCADE,
    donation_type donation_type NOT NULL,
    donation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    received_date DATE,
    total_estimated_value DECIMAL(15, 2),
    total_items_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_donations_donor_id ON donations(donor_id);
CREATE INDEX idx_donations_donation_type ON donations(donation_type);
CREATE INDEX idx_donations_donation_date ON donations(donation_date);

-- Add foreign key to doctors after donors table is created
ALTER TABLE doctors 
    ADD CONSTRAINT fk_doctors_donor 
    FOREIGN KEY (donor_id) REFERENCES donors(id) ON DELETE SET NULL;

-- Add foreign key to equipment after donations table is created
ALTER TABLE equipment 
    ADD CONSTRAINT fk_equipment_donation 
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE SET NULL;

-- ============================================================================
-- DONATION ITEMS TABLE (Medicine Donations)
-- ============================================================================
CREATE TABLE donation_medicine_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    medicine_id UUID REFERENCES medicines(id) ON DELETE SET NULL,
    medicine_name VARCHAR(200) NOT NULL, -- In case medicine doesn't exist in system
    quantity INTEGER NOT NULL,
    unit VARCHAR(50),
    manufacturing_date DATE,
    expiry_date DATE,
    estimated_unit_value DECIMAL(10, 2),
    total_value DECIMAL(12, 2),
    condition_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_donation_medicine_items_donation_id ON donation_medicine_items(donation_id);
CREATE INDEX idx_donation_medicine_items_medicine_id ON donation_medicine_items(medicine_id);

-- ============================================================================
-- DONATION ITEMS TABLE (Equipment Donations)
-- ============================================================================
CREATE TABLE donation_equipment_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,
    equipment_name VARCHAR(200) NOT NULL, -- In case equipment doesn't exist in system
    model VARCHAR(100),
    serial_number VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,
    equipment_condition equipment_condition DEFAULT 'good',
    estimated_value DECIMAL(12, 2),
    condition_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_donation_equipment_items_donation_id ON donation_equipment_items(donation_id);
CREATE INDEX idx_donation_equipment_items_equipment_id ON donation_equipment_items(equipment_id);

-- ============================================================================
-- DONATION ITEMS TABLE (Medical Device Donations)
-- ============================================================================
CREATE TABLE donation_medical_device_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    device_id UUID REFERENCES medical_devices(id) ON DELETE SET NULL,
    device_name VARCHAR(200) NOT NULL, -- In case device doesn't exist in system
    model VARCHAR(100),
    serial_number VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,
    device_condition equipment_condition DEFAULT 'good',
    estimated_value DECIMAL(12, 2),
    condition_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_donation_medical_device_items_donation_id ON donation_medical_device_items(donation_id);
CREATE INDEX idx_donation_medical_device_items_device_id ON donation_medical_device_items(device_id);

-- ============================================================================
-- PRESCRIPTIONS TABLE
-- ============================================================================
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prescription_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
    prescription_date DATE NOT NULL DEFAULT CURRENT_DATE,
    diagnosis TEXT,
    notes TEXT,
    pharmacy_notes TEXT,
    status prescription_status DEFAULT 'pending',
    dispensed_at TIMESTAMP WITH TIME ZONE,
    is_refillable BOOLEAN DEFAULT FALSE,
    refills_remaining INTEGER DEFAULT 0,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_prescriptions_patient_id ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor_id ON prescriptions(doctor_id);
CREATE INDEX idx_prescriptions_appointment_id ON prescriptions(appointment_id);
CREATE INDEX idx_prescriptions_prescription_date ON prescriptions(prescription_date);
CREATE INDEX idx_prescriptions_status ON prescriptions(status);

-- ============================================================================
-- PRESCRIPTION ITEMS TABLE
-- ============================================================================
CREATE TABLE prescription_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prescription_id UUID NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    medicine_id UUID REFERENCES medicines(id) ON DELETE SET NULL,
    medicine_name VARCHAR(200) NOT NULL, -- Stored separately for record keeping
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL, -- e.g., "twice daily", "every 8 hours"
    duration VARCHAR(100), -- e.g., "7 days", "2 weeks"
    quantity INTEGER NOT NULL,
    quantity_dispensed INTEGER DEFAULT 0,
    route_of_administration VARCHAR(100), -- e.g., oral, topical, injection
    instructions TEXT,
    is_substitution_allowed BOOLEAN DEFAULT TRUE,
    is_dispensed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_prescription_items_prescription_id ON prescription_items(prescription_id);
CREATE INDEX idx_prescription_items_medicine_id ON prescription_items(medicine_id);

-- ============================================================================
-- PATIENT DOCUMENTS TABLE
-- ============================================================================
CREATE TABLE patient_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    medical_record_id UUID REFERENCES medical_records(id) ON DELETE SET NULL,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    document_type document_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64), -- For integrity verification
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    document_date DATE, -- Date the actual document was created/issued
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_patient_documents_patient_id ON patient_documents(patient_id);
CREATE INDEX idx_patient_documents_medical_record_id ON patient_documents(medical_record_id);
CREATE INDEX idx_patient_documents_document_type ON patient_documents(document_type);
CREATE INDEX idx_patient_documents_upload_date ON patient_documents(upload_date);

-- ============================================================================
-- INVENTORY TRANSACTIONS TABLE (For tracking medicine movements)
-- ============================================================================
CREATE TABLE inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medicine_inventory_id UUID REFERENCES medicine_inventory(id) ON DELETE CASCADE,
    medical_device_inventory_id UUID REFERENCES medical_device_inventory(id) ON DELETE CASCADE,
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    transaction_type inventory_transaction_type NOT NULL,
    quantity INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    reference_type reference_type,
    reference_id UUID, -- ID of the related record
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_inventory_transactions_medicine ON inventory_transactions(medicine_inventory_id);
CREATE INDEX idx_inventory_transactions_device ON inventory_transactions(medical_device_inventory_id);
CREATE INDEX idx_inventory_transactions_equipment ON inventory_transactions(equipment_id);
CREATE INDEX idx_inventory_transactions_type ON inventory_transactions(transaction_type);
CREATE INDEX idx_inventory_transactions_date ON inventory_transactions(transaction_date);
CREATE INDEX idx_inventory_transactions_reference ON inventory_transactions(reference_type, reference_id);

-- ============================================================================
-- SYSTEM SETTINGS TABLE
-- ============================================================================
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string', -- string, number, boolean, json
    category VARCHAR(100),
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- ============================================================================
-- FUNCTIONS: Auto-update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- TRIGGERS: Apply updated_at trigger to all tables
-- ============================================================================
DO $$ 
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t);
    END LOOP;
END $$;

-- ============================================================================
-- FUNCTION: Generate sequential numbers
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_sequence_number(prefix TEXT, sequence_name TEXT)
RETURNS TEXT AS $$
DECLARE
    seq_value BIGINT;
    current_year TEXT;
BEGIN
    current_year := TO_CHAR(CURRENT_DATE, 'YYYY');
    
    -- Create sequence if it doesn't exist
    EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %I START 1', sequence_name || '_' || current_year);
    
    -- Get next value
    EXECUTE format('SELECT nextval(%L)', sequence_name || '_' || current_year) INTO seq_value;
    
    -- Return formatted number: PREFIX-YYYY-NNNNNN
    RETURN prefix || '-' || current_year || '-' || LPAD(seq_value::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS: Useful reporting views
-- ============================================================================

-- View: Current medicine stock levels
CREATE OR REPLACE VIEW vw_medicine_stock_summary AS
SELECT 
    m.id AS medicine_id,
    m.name AS medicine_name,
    m.generic_name,
    m.dosage_form,
    m.strength,
    mc.name AS category_name,
    COALESCE(SUM(mi.quantity), 0) AS total_quantity,
    CASE 
        WHEN COALESCE(SUM(mi.quantity), 0) = 0 THEN 'out_of_stock'
        WHEN COALESCE(SUM(mi.quantity), 0) <= 10 THEN 'low_stock'
        ELSE 'in_stock'
    END AS stock_status
FROM medicines m
LEFT JOIN medicine_categories mc ON m.category_id = mc.id
LEFT JOIN medicine_inventory mi ON m.id = mi.medicine_id
WHERE m.is_active = TRUE
GROUP BY m.id, m.name, m.generic_name, m.dosage_form, m.strength, mc.name;

-- View: Expiring medicines (within 90 days)
CREATE OR REPLACE VIEW vw_expiring_medicines AS
SELECT 
    me.id AS expiry_id,
    m.name AS medicine_name,
    m.generic_name,
    me.batch_number,
    me.quantity,
    me.expiry_date,
    me.actual_expiry_date,
    (me.expiry_date - CURRENT_DATE) AS days_until_expiry
FROM medicine_expiry me
JOIN medicines m ON me.medicine_id = m.id
WHERE me.quantity > 0
    AND me.expiry_date <= CURRENT_DATE + INTERVAL '90 days'
ORDER BY me.expiry_date;

-- View: Today's appointments
CREATE OR REPLACE VIEW vw_todays_appointments AS
SELECT 
    a.id AS appointment_id,
    a.appointment_number,
    a.appointment_date,
    a.start_time,
    a.end_time,
    a.status,
    p.patient_number,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.phone AS patient_phone,
    d.first_name || ' ' || d.last_name AS doctor_name,
    d.specialization,
    a.appointment_type,
    a.chief_complaint
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN doctors d ON a.doctor_id = d.id
WHERE a.appointment_date = CURRENT_DATE
ORDER BY a.start_time;

-- View: Donation summary by donor
CREATE OR REPLACE VIEW vw_donation_summary_by_donor AS
SELECT 
    d.id AS donor_id,
    d.name AS donor_name,
    d.donor_type,
    d.contact_person,
    d.email,
    COUNT(dn.id) AS total_donations,
    COALESCE(SUM(dn.total_estimated_value), 0) AS total_value,
    MAX(dn.donation_date) AS last_donation_date,
    SUM(dn.total_items_count) AS total_items_donated
FROM donors d
LEFT JOIN donations dn ON d.id = dn.donor_id
GROUP BY d.id, d.name, d.donor_type, d.contact_person, d.email;

-- ============================================================================
-- INSERT DEFAULT DATA
-- ============================================================================

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) VALUES
('clinic_name', 'MedBase Clinic', 'string', 'general', 'Name of the clinic'),
('clinic_address', '', 'string', 'general', 'Clinic address'),
('clinic_phone', '', 'string', 'general', 'Clinic phone number'),
('clinic_email', '', 'string', 'general', 'Clinic email address'),
('appointment_duration_default', '30', 'number', 'appointments', 'Default appointment duration in minutes'),
('working_hours_start', '08:00', 'string', 'appointments', 'Working hours start time'),
('working_hours_end', '18:00', 'string', 'appointments', 'Working hours end time'),
('low_stock_threshold', '10', 'number', 'inventory', 'Low stock warning threshold'),
('expiry_warning_days', '90', 'number', 'inventory', 'Days before expiry to show warning'),
('prescription_prefix', 'RX', 'string', 'prescriptions', 'Prescription number prefix'),
('patient_number_prefix', 'PAT', 'string', 'patients', 'Patient number prefix'),
('appointment_number_prefix', 'APT', 'string', 'appointments', 'Appointment number prefix');

-- Insert default medicine categories
INSERT INTO medicine_categories (name, code, description) VALUES
('Analgesics', 'ANA', 'Pain relievers and fever reducers'),
('Antibiotics', 'ANT', 'Antimicrobial medications'),
('Antivirals', 'AVR', 'Medications to treat viral infections'),
('Cardiovascular', 'CAR', 'Heart and blood pressure medications'),
('Respiratory', 'RES', 'Medications for respiratory conditions'),
('Gastrointestinal', 'GAS', 'Digestive system medications'),
('Endocrine', 'END', 'Hormonal medications'),
('Neurological', 'NEU', 'Nervous system medications'),
('Dermatological', 'DER', 'Skin treatment medications'),
('Vitamins & Supplements', 'VIT', 'Nutritional supplements'),
('Emergency Medications', 'EMR', 'Critical emergency medications'),
('Vaccines', 'VAC', 'Immunization vaccines');

-- Insert default medical device categories
INSERT INTO medical_device_categories (name, code, description) VALUES
('Mobility Aids', 'MOB', 'Wheelchairs, walkers, canes, crutches'),
('Orthopedic Devices', 'ORTH', 'Braces, splints, supports'),
('Respiratory Devices', 'RESP', 'Nebulizers, oxygen equipment'),
('Prosthetics', 'PROS', 'Artificial limbs and parts'),
('Hearing Devices', 'HEAR', 'Hearing aids and accessories'),
('Vision Aids', 'VIS', 'Magnifiers, reading aids'),
('Daily Living Aids', 'DAILY', 'Assistive devices for daily activities');

-- Insert default equipment categories
INSERT INTO equipment_categories (name, code, description) VALUES
('Diagnostic Equipment', 'DIAG', 'Equipment for diagnosis'),
('Surgical Equipment', 'SURG', 'Equipment for surgical procedures'),
('Patient Monitoring', 'MNTR', 'Patient monitoring devices'),
('Imaging Equipment', 'IMG', 'X-ray, ultrasound, etc.'),
('Rehabilitation Equipment', 'REHB', 'Physical therapy equipment'),
('Emergency Equipment', 'EMRG', 'Emergency response equipment'),
('Furniture', 'FURN', 'Medical furniture'),
('Sterilization Equipment', 'STER', 'Sterilization and cleaning equipment'),
('IT Equipment', 'IT', 'Computers and related equipment');

-- Create initial admin user (password should be changed immediately)
-- Password: 'changeme123' (hashed with pgcrypto)
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active)
VALUES (
    'admin',
    'admin@medbase.local',
    crypt('changeme123', gen_salt('bf')),
    'System',
    'Administrator',
    TRUE
);

-- ============================================================================
-- GRANTS (Adjust based on your user setup)
-- ============================================================================
-- Example: GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medbase_app;
-- Example: GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO medbase_app;

-- ============================================================================
-- COMMENTS ON TABLES
-- ============================================================================
COMMENT ON TABLE users IS 'System users with access to the clinic management software';
COMMENT ON TABLE patients IS 'Patient demographic and contact information';
COMMENT ON TABLE doctors IS 'Doctor/physician information and credentials';
COMMENT ON TABLE appointments IS 'Patient appointments with doctors';
COMMENT ON TABLE prescriptions IS 'Medical prescriptions issued to patients';
COMMENT ON TABLE prescription_items IS 'Individual medicine items in a prescription';
COMMENT ON TABLE medicines IS 'Medicine catalog/master list';
COMMENT ON TABLE medicine_inventory IS 'Current medicine stock with batch tracking';
COMMENT ON TABLE equipment IS 'Clinic equipment inventory';
COMMENT ON TABLE medical_devices IS 'Prescribable medical devices (wheelchairs, walkers, braces, etc.)';
COMMENT ON TABLE medical_device_inventory IS 'Stock of medical devices available for prescription';
COMMENT ON TABLE prescribed_devices IS 'Medical devices prescribed/issued to patients';
COMMENT ON TABLE donors IS 'Organizations and individuals who donate to the clinic';
COMMENT ON TABLE donations IS 'Donation records for medicines and equipment';
COMMENT ON TABLE patient_documents IS 'Uploaded documents for patients (including external lab results)';
COMMENT ON TABLE medical_records IS 'Patient visit/encounter records';
COMMENT ON TABLE inventory_transactions IS 'Track all medicine inventory movements';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

