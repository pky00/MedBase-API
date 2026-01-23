-- ============================================================================
-- MEDBASE CLINIC - SAMPLE DATA
-- Run this script after the initial schema is created
-- ============================================================================

-- Ensure extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS (Additional users besides admin)
-- Password for all: 'password123' (use bcrypt in production)
-- ============================================================================
INSERT INTO users (id, username, email, password_hash, first_name, last_name, is_active, created_at, updated_at, created_by) VALUES
    ('a1111111-1111-1111-1111-111111111111', 'drjohnson', 'drjohnson@medbase.com', '$2b$12$LQv3c1yqBwlVlLqkJYLIEeOpEBNbLzN.J.L.F.z.VYtqMQtqYqYqK', 'Robert', 'Johnson', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('a2222222-2222-2222-2222-222222222222', 'nurse_sarah', 'sarah.nurse@medbase.com', '$2b$12$LQv3c1yqBwlVlLqkJYLIEeOpEBNbLzN.J.L.F.z.VYtqMQtqYqYqK', 'Sarah', 'Williams', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('a3333333-3333-3333-3333-333333333333', 'receptionist', 'reception@medbase.com', '$2b$12$LQv3c1yqBwlVlLqkJYLIEeOpEBNbLzN.J.L.F.z.VYtqMQtqYqYqK', 'Maria', 'Garcia', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('a4444444-4444-4444-4444-444444444444', 'pharmacist', 'pharmacy@medbase.com', '$2b$12$LQv3c1yqBwlVlLqkJYLIEeOpEBNbLzN.J.L.F.z.VYtqMQtqYqYqK', 'James', 'Chen', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- DONORS
-- ============================================================================
INSERT INTO donors (id, donor_code, name, donor_type, contact_person, phone, email, website, address, city, country, notes, is_active, created_at, updated_at, created_by) VALUES
    ('d1111111-1111-1111-1111-111111111111', 'DON-2025-000001', 'Global Health Foundation', 'ngo', 'Dr. Amanda Foster', '+1-555-0101', 'donate@globalhealthfdn.org', 'www.globalhealthfdn.org', '123 Charity Lane', 'New York', 'USA', 'Major medical supply donor since 2020', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d2222222-2222-2222-2222-222222222222', 'DON-2025-000002', 'PharmaCare International', 'pharmaceutical_company', 'Michael Roberts', '+1-555-0102', 'csr@pharmacare.com', 'www.pharmacare.com', '456 Pharma Boulevard', 'Boston', 'USA', 'Quarterly medicine donations', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d3333333-3333-3333-3333-333333333333', 'DON-2025-000003', 'Community Health Initiative', 'organization', 'Lisa Thompson', '+1-555-0103', 'info@communityhealth.org', 'www.communityhealth.org', '789 Community Drive', 'Chicago', 'USA', 'Local community organization', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d4444444-4444-4444-4444-444444444444', 'DON-2025-000004', 'John Smith', 'individual', NULL, '+1-555-0104', 'jsmith@email.com', NULL, '321 Oak Street', 'Denver', 'USA', 'Regular individual donor', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d5555555-5555-5555-5555-555555555555', 'DON-2025-000005', 'City Health Department', 'government', 'Dr. Patricia Nguyen', '+1-555-0105', 'health@citygov.org', 'www.citygov.org/health', '100 Government Plaza', 'San Francisco', 'USA', 'Government health department', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d6666666-6666-6666-6666-666666666666', 'DON-2025-000006', 'Doctors Without Borders - Local Chapter', 'ngo', 'Dr. Hassan Ahmed', '+1-555-0106', 'local@dwb.org', 'www.dwb.org', '555 Medical Center Drive', 'Houston', 'USA', 'Provides volunteer doctors and equipment', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d7777777-7777-7777-7777-777777777777', 'DON-2025-000007', 'MedEquip Solutions', 'organization', 'Kevin O''Brien', '+1-555-0107', 'donations@medequip.com', 'www.medequip.com', '888 Equipment Way', 'Seattle', 'USA', 'Medical equipment supplier - donates refurbished equipment', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('d8888888-8888-8888-8888-888888888888', 'DON-2025-000008', 'Sunrise Pharmaceutical', 'pharmaceutical_company', 'Jennifer Lee', '+1-555-0108', 'giving@sunrisepharma.com', 'www.sunrisepharma.com', '999 Sunrise Avenue', 'Los Angeles', 'USA', 'Generic medicine manufacturer', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- DOCTORS (Some sponsored by donors)
-- ============================================================================
INSERT INTO doctors (id, user_id, donor_id, first_name, last_name, gender, specialization, phone, email, address, qualification, bio, created_at, updated_at, created_by) VALUES
    ('b1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', NULL, 'Robert', 'Johnson', 'male', 'General Practice', '+1-555-1001', 'drjohnson@medbase.com', '100 Doctor Lane, Medical City', 'MD, MBBS - Harvard Medical School', 'Over 15 years of experience in general medicine and primary care.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('b2222222-2222-2222-2222-222222222222', NULL, 'd6666666-6666-6666-6666-666666666666', 'Maria', 'Santos', 'female', 'Pediatrics', '+1-555-1002', 'msantos@email.com', '200 Child Care Blvd', 'MD Pediatrics - Johns Hopkins', 'Volunteer pediatrician sponsored by Doctors Without Borders.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('b3333333-3333-3333-3333-333333333333', NULL, NULL, 'Ahmed', 'Hassan', 'male', 'Internal Medicine', '+1-555-1003', 'ahassan@email.com', '300 Internal Ave', 'MD, MRCP - Oxford University', 'Specializes in chronic disease management.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('b4444444-4444-4444-4444-444444444444', NULL, 'd1111111-1111-1111-1111-111111111111', 'Emily', 'Chen', 'female', 'Family Medicine', '+1-555-1004', 'echen@email.com', '400 Family Street', 'MD Family Medicine - Stanford', 'Sponsored by Global Health Foundation. Focus on preventive care.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('b5555555-5555-5555-5555-555555555555', NULL, NULL, 'David', 'Williams', 'male', 'Orthopedics', '+1-555-1005', 'dwilliams@email.com', '500 Bone Street', 'MD Orthopedics, Fellowship - Mayo Clinic', 'Specializes in sports injuries and joint replacements.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('b6666666-6666-6666-6666-666666666666', NULL, NULL, 'Sarah', 'Miller', 'female', 'Dermatology', '+1-555-1006', 'smiller@email.com', '600 Skin Lane', 'MD Dermatology - UCLA', 'Expert in skin conditions and allergic reactions.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PATIENTS
-- ============================================================================
INSERT INTO patients (id, patient_number, first_name, last_name, date_of_birth, gender, blood_type, national_id, phone, email, address, city, region, country, occupation, marital_status, created_at, updated_at, created_by) VALUES
    ('c1111111-1111-1111-1111-111111111111', 'PAT-2025-000001', 'James', 'Anderson', '1985-03-15', 'male', 'A_positive', 'NID001234567', '+1-555-2001', 'james.anderson@email.com', '101 Patient Street', 'New York', 'NY', 'USA', 'Teacher', 'married', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c2222222-2222-2222-2222-222222222222', 'PAT-2025-000002', 'Emma', 'Thompson', '1990-07-22', 'female', 'O_positive', 'NID001234568', '+1-555-2002', 'emma.t@email.com', '202 Healthcare Ave', 'Boston', 'MA', 'USA', 'Nurse', 'single', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c3333333-3333-3333-3333-333333333333', 'PAT-2025-000003', 'Michael', 'Brown', '1975-11-08', 'male', 'B_positive', 'NID001234569', '+1-555-2003', 'mbrown@email.com', '303 Wellness Blvd', 'Chicago', 'IL', 'USA', 'Engineer', 'married', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c4444444-4444-4444-4444-444444444444', 'PAT-2025-000004', 'Sofia', 'Rodriguez', '2015-05-12', 'female', 'AB_positive', 'NID001234570', '+1-555-2004', 'srodriguez.parent@email.com', '404 Child Lane', 'Miami', 'FL', 'USA', 'Student', 'single', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c5555555-5555-5555-5555-555555555555', 'PAT-2025-000005', 'William', 'Davis', '1960-01-30', 'male', 'O_negative', 'NID001234571', '+1-555-2005', 'wdavis@email.com', '505 Senior Street', 'Phoenix', 'AZ', 'USA', 'Retired', 'widowed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c6666666-6666-6666-6666-666666666666', 'PAT-2025-000006', 'Olivia', 'Martinez', '1988-09-18', 'female', 'A_negative', 'NID001234572', '+1-555-2006', 'olivia.m@email.com', '606 Care Road', 'Seattle', 'WA', 'USA', 'Artist', 'single', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c7777777-7777-7777-7777-777777777777', 'PAT-2025-000007', 'Lucas', 'Garcia', '1995-12-05', 'male', 'B_negative', 'NID001234573', '+1-555-2007', 'lgarcia@email.com', '707 Health Way', 'Denver', 'CO', 'USA', 'Student', 'single', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c8888888-8888-8888-8888-888888888888', 'PAT-2025-000008', 'Ava', 'Wilson', '1978-06-25', 'female', 'AB_negative', 'NID001234574', '+1-555-2008', 'ava.wilson@email.com', '808 Medical Drive', 'Austin', 'TX', 'USA', 'Manager', 'divorced', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('c9999999-9999-9999-9999-999999999999', 'PAT-2025-000009', 'Ethan', 'Moore', '2010-02-14', 'male', 'O_positive', 'NID001234575', '+1-555-2009', 'ethan.parent@email.com', '909 Kids Lane', 'Portland', 'OR', 'USA', 'Student', 'single', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ca111111-1111-1111-1111-111111111111', 'PAT-2025-000010', 'Isabella', 'Taylor', '1982-08-07', 'female', 'A_positive', 'NID001234576', '+1-555-2010', 'isabella.t@email.com', '1010 Clinic Road', 'San Diego', 'CA', 'USA', 'Accountant', 'married', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PATIENT ALLERGIES
-- ============================================================================
INSERT INTO patient_allergies (id, patient_id, allergen, reaction, severity, notes, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'Penicillin', 'Skin rash and hives', 'moderate', 'Discovered in 2010', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'Shellfish', 'Anaphylaxis', 'severe', 'Carries EpiPen', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c2222222-2222-2222-2222-222222222222', 'Latex', 'Contact dermatitis', 'mild', 'Use non-latex gloves', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c3333333-3333-3333-3333-333333333333', 'Aspirin', 'Gastrointestinal bleeding', 'moderate', 'Avoid all NSAIDs', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'Sulfa drugs', 'Severe rash', 'severe', 'Documented in medical history', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c6666666-6666-6666-6666-666666666666', 'Pollen', 'Seasonal allergies', 'mild', 'Takes antihistamines seasonally', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c8888888-8888-8888-8888-888888888888', 'Codeine', 'Nausea and vomiting', 'moderate', 'Use alternative pain medications', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PATIENT MEDICAL HISTORY
-- ============================================================================
INSERT INTO patient_medical_history (id, patient_id, condition_name, icd_code, diagnosis_date, is_chronic, is_current, severity, notes, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'Hypertension', 'I10', '2018-05-15', TRUE, TRUE, 'moderate', 'Controlled with medication', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'Type 2 Diabetes', 'E11', '2020-01-20', TRUE, TRUE, 'moderate', 'Diet controlled, monitoring HbA1c', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c3333333-3333-3333-3333-333333333333', 'Asthma', 'J45', '1985-03-10', TRUE, TRUE, 'mild', 'Uses inhaler as needed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'Coronary Artery Disease', 'I25.1', '2015-08-22', TRUE, TRUE, 'severe', 'History of stent placement', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'Arthritis', 'M19.9', '2010-04-15', TRUE, TRUE, 'moderate', 'Affects knees and hips', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c6666666-6666-6666-6666-666666666666', 'Migraine', 'G43', '2012-06-30', TRUE, TRUE, 'moderate', 'Triggered by stress and bright lights', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c8888888-8888-8888-8888-888888888888', 'Appendectomy', 'Z98.89', '2005-11-12', FALSE, FALSE, NULL, 'Surgery in 2005, no complications', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- MEDICINES (Using existing categories)
-- ============================================================================
-- First, get category IDs
DO $$
DECLARE
    cat_analgesics UUID;
    cat_antibiotics UUID;
    cat_cardiovascular UUID;
    cat_respiratory UUID;
    cat_gastrointestinal UUID;
    cat_vitamins UUID;
    cat_emergency UUID;
BEGIN
    SELECT id INTO cat_analgesics FROM medicine_categories WHERE code = 'ANA';
    SELECT id INTO cat_antibiotics FROM medicine_categories WHERE code = 'ANT';
    SELECT id INTO cat_cardiovascular FROM medicine_categories WHERE code = 'CAR';
    SELECT id INTO cat_respiratory FROM medicine_categories WHERE code = 'RES';
    SELECT id INTO cat_gastrointestinal FROM medicine_categories WHERE code = 'GAS';
    SELECT id INTO cat_vitamins FROM medicine_categories WHERE code = 'VIT';
    SELECT id INTO cat_emergency FROM medicine_categories WHERE code = 'EMR';

    -- Insert medicines
    INSERT INTO medicines (id, code, name, generic_name, brand_name, category_id, manufacturer, dosage_form, strength, unit, package_size, description, requires_prescription, is_controlled_substance, is_active, created_at, updated_at, created_by) VALUES
        ('e1111111-1111-1111-1111-111111111111', 'MED-001', 'Paracetamol 500mg', 'Paracetamol', 'Tylenol', cat_analgesics, 'PharmaCare', 'tablet', '500mg', 'mg', '100 tablets', 'For pain and fever relief', FALSE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e2222222-2222-2222-2222-222222222222', 'MED-002', 'Ibuprofen 400mg', 'Ibuprofen', 'Advil', cat_analgesics, 'PharmaCare', 'tablet', '400mg', 'mg', '50 tablets', 'Anti-inflammatory pain reliever', FALSE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e3333333-3333-3333-3333-333333333333', 'MED-003', 'Amoxicillin 500mg', 'Amoxicillin', 'Amoxil', cat_antibiotics, 'Sunrise Pharmaceutical', 'capsule', '500mg', 'mg', '21 capsules', 'Broad-spectrum antibiotic', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e4444444-4444-4444-4444-444444444444', 'MED-004', 'Metformin 500mg', 'Metformin', 'Glucophage', cat_cardiovascular, 'GenericPharma', 'tablet', '500mg', 'mg', '60 tablets', 'For Type 2 Diabetes', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e5555555-5555-5555-5555-555555555555', 'MED-005', 'Lisinopril 10mg', 'Lisinopril', 'Zestril', cat_cardiovascular, 'CardioMeds', 'tablet', '10mg', 'mg', '30 tablets', 'ACE inhibitor for hypertension', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e6666666-6666-6666-6666-666666666666', 'MED-006', 'Salbutamol Inhaler', 'Salbutamol', 'Ventolin', cat_respiratory, 'RespiCare', 'inhaler', '100mcg', 'mcg', '200 doses', 'Bronchodilator for asthma', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e7777777-7777-7777-7777-777777777777', 'MED-007', 'Omeprazole 20mg', 'Omeprazole', 'Prilosec', cat_gastrointestinal, 'GastroMeds', 'capsule', '20mg', 'mg', '28 capsules', 'Proton pump inhibitor', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e8888888-8888-8888-8888-888888888888', 'MED-008', 'Vitamin D3 1000IU', 'Cholecalciferol', 'D-Vit', cat_vitamins, 'VitaHealth', 'tablet', '1000IU', 'IU', '90 tablets', 'Vitamin D supplement', FALSE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('e9999999-9999-9999-9999-999999999999', 'MED-009', 'Epinephrine Auto-Injector', 'Epinephrine', 'EpiPen', cat_emergency, 'EmergencyMeds', 'injection', '0.3mg', 'mg', '2 injectors', 'Emergency anaphylaxis treatment', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('ea111111-1111-1111-1111-111111111111', 'MED-010', 'Atorvastatin 20mg', 'Atorvastatin', 'Lipitor', cat_cardiovascular, 'CardioMeds', 'tablet', '20mg', 'mg', '30 tablets', 'Cholesterol-lowering medication', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('ea222222-2222-2222-2222-222222222222', 'MED-011', 'Cetirizine 10mg', 'Cetirizine', 'Zyrtec', cat_respiratory, 'AllergyRelief', 'tablet', '10mg', 'mg', '30 tablets', 'Antihistamine for allergies', FALSE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('ea333333-3333-3333-3333-333333333333', 'MED-012', 'Azithromycin 250mg', 'Azithromycin', 'Zithromax', cat_antibiotics, 'Sunrise Pharmaceutical', 'tablet', '250mg', 'mg', '6 tablets', 'Macrolide antibiotic', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');
END $$;

-- ============================================================================
-- MEDICINE INVENTORY
-- ============================================================================
INSERT INTO medicine_inventory (id, medicine_id, quantity, created_at, updated_at, created_by) VALUES
    ('ee111111-1111-1111-1111-111111111111', 'e1111111-1111-1111-1111-111111111111', 500, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee222222-2222-2222-2222-222222222222', 'e2222222-2222-2222-2222-222222222222', 300, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee333333-3333-3333-3333-333333333333', 'e3333333-3333-3333-3333-333333333333', 200, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee444444-4444-4444-4444-444444444444', 'e4444444-4444-4444-4444-444444444444', 150, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee555555-5555-5555-5555-555555555555', 'e5555555-5555-5555-5555-555555555555', 180, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee666666-6666-6666-6666-666666666666', 'e6666666-6666-6666-6666-666666666666', 50, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee777777-7777-7777-7777-777777777777', 'e7777777-7777-7777-7777-777777777777', 120, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee888888-8888-8888-8888-888888888888', 'e8888888-8888-8888-8888-888888888888', 400, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('ee999999-9999-9999-9999-999999999999', 'e9999999-9999-9999-9999-999999999999', 20, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('eea11111-1111-1111-1111-111111111111', 'ea111111-1111-1111-1111-111111111111', 90, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('eea22222-2222-2222-2222-222222222222', 'ea222222-2222-2222-2222-222222222222', 250, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('eea33333-3333-3333-3333-333333333333', 'ea333333-3333-3333-3333-333333333333', 80, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- MEDICINE EXPIRY
-- ============================================================================
INSERT INTO medicine_expiry (id, medicine_id, batch_number, quantity, expiry_date, actual_expiry_date, manufacturing_date, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'e1111111-1111-1111-1111-111111111111', 'BATCH-2025-001', 200, '2027-03-15', '2027-03-15', '2025-03-15', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'e1111111-1111-1111-1111-111111111111', 'BATCH-2025-002', 300, '2027-06-20', '2027-06-20', '2025-06-20', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'e3333333-3333-3333-3333-333333333333', 'BATCH-2024-015', 100, '2026-02-28', '2026-02-28', '2024-02-28', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'e3333333-3333-3333-3333-333333333333', 'BATCH-2025-008', 100, '2027-08-15', '2027-08-15', '2025-08-15', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'e6666666-6666-6666-6666-666666666666', 'BATCH-2024-022', 25, '2026-04-10', '2026-04-10', '2024-04-10', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'e9999999-9999-9999-9999-999999999999', 'BATCH-2025-003', 20, '2026-12-01', '2026-12-01', '2025-01-01', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- MEDICAL DEVICES (Using existing categories)
-- ============================================================================
DO $$
DECLARE
    cat_mobility UUID;
    cat_orthopedic UUID;
    cat_respiratory UUID;
    cat_daily UUID;
BEGIN
    SELECT id INTO cat_mobility FROM medical_device_categories WHERE code = 'MOB';
    SELECT id INTO cat_orthopedic FROM medical_device_categories WHERE code = 'ORTH';
    SELECT id INTO cat_respiratory FROM medical_device_categories WHERE code = 'RESP';
    SELECT id INTO cat_daily FROM medical_device_categories WHERE code = 'DAILY';

    INSERT INTO medical_devices (id, code, name, category_id, manufacturer, model, description, size, is_reusable, requires_fitting, is_active, created_at, updated_at, created_by) VALUES
        ('f1111111-1111-1111-1111-111111111111', 'DEV-001', 'Standard Wheelchair', cat_mobility, 'MobilityPlus', 'WC-100', 'Manual wheelchair for basic mobility', 'Standard', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f2222222-2222-2222-2222-222222222222', 'DEV-002', 'Folding Walker', cat_mobility, 'WalkAid', 'FW-200', 'Lightweight folding walker with wheels', 'Adjustable', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f3333333-3333-3333-3333-333333333333', 'DEV-003', 'Forearm Crutches', cat_mobility, 'MobilityPlus', 'FC-150', 'Ergonomic forearm crutches', 'Adult', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f4444444-4444-4444-4444-444444444444', 'DEV-004', 'Knee Brace', cat_orthopedic, 'OrthoSupport', 'KB-300', 'Adjustable knee support brace', 'S/M/L/XL', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f5555555-5555-5555-5555-555555555555', 'DEV-005', 'Wrist Splint', cat_orthopedic, 'OrthoSupport', 'WS-100', 'Rigid wrist support splint', 'S/M/L', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f6666666-6666-6666-6666-666666666666', 'DEV-006', 'Portable Nebulizer', cat_respiratory, 'RespiCare', 'PN-500', 'Compact portable nebulizer', 'One Size', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f7777777-7777-7777-7777-777777777777', 'DEV-007', 'Cervical Collar', cat_orthopedic, 'NeckSupport', 'CC-200', 'Soft cervical support collar', 'S/M/L', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('f8888888-8888-8888-8888-888888888888', 'DEV-008', 'Quad Cane', cat_mobility, 'WalkAid', 'QC-100', 'Four-point base walking cane', 'Adjustable', TRUE, FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');
END $$;

-- ============================================================================
-- MEDICAL DEVICE INVENTORY
-- ============================================================================
INSERT INTO medical_device_inventory (id, device_id, serial_number, condition, is_donation, donor_id, is_available, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'f1111111-1111-1111-1111-111111111111', 'WC-2025-001', 'excellent', TRUE, 'd7777777-7777-7777-7777-777777777777', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f1111111-1111-1111-1111-111111111111', 'WC-2025-002', 'good', TRUE, 'd7777777-7777-7777-7777-777777777777', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f1111111-1111-1111-1111-111111111111', 'WC-2024-015', 'fair', TRUE, 'd1111111-1111-1111-1111-111111111111', FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f2222222-2222-2222-2222-222222222222', 'FW-2025-001', 'new', TRUE, 'd3333333-3333-3333-3333-333333333333', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f2222222-2222-2222-2222-222222222222', 'FW-2025-002', 'excellent', FALSE, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f3333333-3333-3333-3333-333333333333', 'FC-2025-001', 'new', TRUE, 'd1111111-1111-1111-1111-111111111111', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f3333333-3333-3333-3333-333333333333', 'FC-2025-002', 'good', FALSE, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f4444444-4444-4444-4444-444444444444', 'KB-2025-001', 'new', TRUE, 'd3333333-3333-3333-3333-333333333333', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f5555555-5555-5555-5555-555555555555', 'WS-2025-001', 'new', FALSE, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f5555555-5555-5555-5555-555555555555', 'WS-2025-002', 'new', FALSE, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f6666666-6666-6666-6666-666666666666', 'PN-2025-001', 'new', TRUE, 'd5555555-5555-5555-5555-555555555555', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f7777777-7777-7777-7777-777777777777', 'CC-2025-001', 'good', FALSE, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'f8888888-8888-8888-8888-888888888888', 'QC-2025-001', 'excellent', TRUE, 'd4444444-4444-4444-4444-444444444444', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- EQUIPMENT (Using existing categories)
-- ============================================================================
DO $$
DECLARE
    cat_diagnostic UUID;
    cat_monitoring UUID;
    cat_emergency UUID;
    cat_furniture UUID;
BEGIN
    SELECT id INTO cat_diagnostic FROM equipment_categories WHERE code = 'DIAG';
    SELECT id INTO cat_monitoring FROM equipment_categories WHERE code = 'MNTR';
    SELECT id INTO cat_emergency FROM equipment_categories WHERE code = 'EMRG';
    SELECT id INTO cat_furniture FROM equipment_categories WHERE code = 'FURN';

    INSERT INTO equipment (id, asset_code, name, category_id, model, manufacturer, serial_number, description, is_donation, donor_id, equipment_condition, is_portable, is_active, created_at, updated_at, created_by) VALUES
        ('01111111-1111-1111-1111-111111111111', 'EQP-001', 'Digital Blood Pressure Monitor', cat_diagnostic, 'BP-200', 'MedTech', 'MT-BP-2025-001', 'Automatic digital BP monitor', TRUE, 'd1111111-1111-1111-1111-111111111111', 'excellent', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('02222222-2222-2222-2222-222222222222', 'EQP-002', 'Pulse Oximeter', cat_monitoring, 'PO-100', 'HealthCheck', 'HC-PO-2025-001', 'Fingertip pulse oximeter', TRUE, 'd7777777-7777-7777-7777-777777777777', 'new', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('03333333-3333-3333-3333-333333333333', 'EQP-003', 'Electronic Stethoscope', cat_diagnostic, 'ES-300', 'SoundMed', 'SM-ES-2024-015', 'Digital stethoscope with amplification', FALSE, NULL, 'good', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('04444444-4444-4444-4444-444444444444', 'EQP-004', 'Examination Table', cat_furniture, 'ET-500', 'MedFurniture', 'MF-ET-2024-001', 'Adjustable examination table', TRUE, 'd1111111-1111-1111-1111-111111111111', 'excellent', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('05555555-5555-5555-5555-555555555555', 'EQP-005', 'AED Defibrillator', cat_emergency, 'AED-Pro', 'LifeSave', 'LS-AED-2025-001', 'Automated external defibrillator', TRUE, 'd5555555-5555-5555-5555-555555555555', 'new', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('06666666-6666-6666-6666-666666666666', 'EQP-006', 'Patient Monitor', cat_monitoring, 'PM-400', 'VitalSign', 'VS-PM-2024-008', 'Multi-parameter patient monitor', TRUE, 'd7777777-7777-7777-7777-777777777777', 'good', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('07777777-7777-7777-7777-777777777777', 'EQP-007', 'Ophthalmoscope', cat_diagnostic, 'OP-150', 'EyeCare', 'EC-OP-2025-001', 'Direct ophthalmoscope', FALSE, NULL, 'excellent', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
        ('08888888-8888-8888-8888-888888888888', 'EQP-008', 'Wheelchair Scale', cat_diagnostic, 'WS-600', 'ScaleTech', 'ST-WS-2024-003', 'Platform scale for wheelchair patients', TRUE, 'd3333333-3333-3333-3333-333333333333', 'good', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');
END $$;

-- ============================================================================
-- DONATIONS
-- ============================================================================
INSERT INTO donations (id, donation_number, donor_id, donation_type, donation_date, received_date, total_estimated_value, total_items_count, notes, created_at, updated_at, created_by) VALUES
    ('aa111111-1111-1111-1111-111111111111', 'DON-2025-000001', 'd1111111-1111-1111-1111-111111111111', 'mixed', '2025-01-05', '2025-01-07', 15000.00, 25, 'Quarterly donation including medicines and equipment', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('aa222222-2222-2222-2222-222222222222', 'DON-2025-000002', 'd2222222-2222-2222-2222-222222222222', 'medicine', '2025-01-10', '2025-01-12', 8500.00, 500, 'Generic medicine donation - antibiotics and pain relievers', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('aa333333-3333-3333-3333-333333333333', 'DON-2025-000003', 'd7777777-7777-7777-7777-777777777777', 'equipment', '2025-01-15', '2025-01-16', 12000.00, 8, 'Refurbished medical equipment', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('aa444444-4444-4444-4444-444444444444', 'DON-2024-000015', 'd3333333-3333-3333-3333-333333333333', 'medical_device', '2024-12-20', '2024-12-22', 3500.00, 10, 'Mobility aids for elderly patients', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('aa555555-5555-5555-5555-555555555555', 'DON-2024-000012', 'd5555555-5555-5555-5555-555555555555', 'equipment', '2024-11-15', '2024-11-18', 5000.00, 3, 'Emergency equipment from city health department', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- DONATION MEDICINE ITEMS
-- ============================================================================
INSERT INTO donation_medicine_items (id, donation_id, medicine_id, medicine_name, quantity, unit, expiry_date, estimated_unit_value, total_value, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'aa111111-1111-1111-1111-111111111111', 'e1111111-1111-1111-1111-111111111111', 'Paracetamol 500mg', 200, 'tablets', '2027-03-15', 0.10, 20.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa111111-1111-1111-1111-111111111111', 'e3333333-3333-3333-3333-333333333333', 'Amoxicillin 500mg', 100, 'capsules', '2026-02-28', 0.50, 50.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa222222-2222-2222-2222-222222222222', 'e1111111-1111-1111-1111-111111111111', 'Paracetamol 500mg', 300, 'tablets', '2027-06-20', 0.10, 30.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa222222-2222-2222-2222-222222222222', 'e2222222-2222-2222-2222-222222222222', 'Ibuprofen 400mg', 150, 'tablets', '2027-05-15', 0.15, 22.50, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa222222-2222-2222-2222-222222222222', 'ea333333-3333-3333-3333-333333333333', 'Azithromycin 250mg', 50, 'tablets', '2027-04-10', 1.00, 50.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- DONATION EQUIPMENT ITEMS
-- ============================================================================
INSERT INTO donation_equipment_items (id, donation_id, equipment_id, equipment_name, model, serial_number, quantity, equipment_condition, estimated_value, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'aa111111-1111-1111-1111-111111111111', '01111111-1111-1111-1111-111111111111', 'Digital Blood Pressure Monitor', 'BP-200', 'MT-BP-2025-001', 1, 'excellent', 150.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa111111-1111-1111-1111-111111111111', '04444444-4444-4444-4444-444444444444', 'Examination Table', 'ET-500', 'MF-ET-2024-001', 1, 'excellent', 800.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa333333-3333-3333-3333-333333333333', '02222222-2222-2222-2222-222222222222', 'Pulse Oximeter', 'PO-100', 'HC-PO-2025-001', 2, 'new', 100.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa333333-3333-3333-3333-333333333333', '06666666-6666-6666-6666-666666666666', 'Patient Monitor', 'PM-400', 'VS-PM-2024-008', 1, 'good', 2500.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa555555-5555-5555-5555-555555555555', '05555555-5555-5555-5555-555555555555', 'AED Defibrillator', 'AED-Pro', 'LS-AED-2025-001', 1, 'new', 3500.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- DONATION MEDICAL DEVICE ITEMS
-- ============================================================================
INSERT INTO donation_medical_device_items (id, donation_id, device_id, device_name, model, quantity, device_condition, estimated_value, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'aa444444-4444-4444-4444-444444444444', 'f2222222-2222-2222-2222-222222222222', 'Folding Walker', 'FW-200', 2, 'new', 150.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa444444-4444-4444-4444-444444444444', 'f4444444-4444-4444-4444-444444444444', 'Knee Brace', 'KB-300', 5, 'new', 50.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'aa444444-4444-4444-4444-444444444444', 'f8888888-8888-8888-8888-888888888888', 'Quad Cane', 'QC-100', 3, 'excellent', 40.00, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- APPOINTMENTS
-- ============================================================================
INSERT INTO appointments (id, appointment_number, patient_id, doctor_id, appointment_date, start_time, end_time, duration_minutes, appointment_type, status, chief_complaint, notes, is_follow_up, previous_appointment_id, created_at, updated_at, created_by) VALUES
    -- Past appointments (completed)
    ('bb111111-1111-1111-1111-111111111111', 'APT-2025-000001', 'c1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', '2025-01-10', '09:00', '09:30', 30, 'consultation', 'completed', 'Routine checkup for hypertension', 'BP well controlled', FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb222222-2222-2222-2222-222222222222', 'APT-2025-000002', 'c4444444-4444-4444-4444-444444444444', 'b2222222-2222-2222-2222-222222222222', '2025-01-10', '10:00', '10:30', 30, 'checkup', 'completed', 'Annual pediatric checkup', 'All vaccinations up to date', FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb333333-3333-3333-3333-333333333333', 'APT-2025-000003', 'c3333333-3333-3333-3333-333333333333', 'b3333333-3333-3333-3333-333333333333', '2025-01-12', '14:00', '14:30', 30, 'follow_up', 'completed', 'Asthma follow-up', 'Symptoms improved with current medication', TRUE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb444444-4444-4444-4444-444444444444', 'APT-2025-000004', 'c5555555-5555-5555-5555-555555555555', 'b3333333-3333-3333-3333-333333333333', '2025-01-15', '11:00', '11:45', 45, 'consultation', 'completed', 'Chest discomfort', 'ECG normal, continue current medications', FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Today's appointments (use CURRENT_DATE)
    ('bb555555-5555-5555-5555-555555555555', 'APT-2025-000005', 'c2222222-2222-2222-2222-222222222222', 'b1111111-1111-1111-1111-111111111111', CURRENT_DATE, '09:00', '09:30', 30, 'consultation', 'scheduled', 'Flu-like symptoms', NULL, FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb666666-6666-6666-6666-666666666666', 'APT-2025-000006', 'c6666666-6666-6666-6666-666666666666', 'b6666666-6666-6666-6666-666666666666', CURRENT_DATE, '10:30', '11:00', 30, 'consultation', 'scheduled', 'Skin rash on arms', NULL, FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb777777-7777-7777-7777-777777777777', 'APT-2025-000007', 'c9999999-9999-9999-9999-999999999999', 'b2222222-2222-2222-2222-222222222222', CURRENT_DATE, '14:00', '14:30', 30, 'checkup', 'scheduled', 'School health checkup', NULL, FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Future appointments
    ('bb888888-8888-8888-8888-888888888888', 'APT-2025-000008', 'c1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', CURRENT_DATE + INTERVAL '7 days', '09:00', '09:30', 30, 'follow_up', 'scheduled', 'Diabetes follow-up', NULL, TRUE, 'bb111111-1111-1111-1111-111111111111', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bb999999-9999-9999-9999-999999999999', 'APT-2025-000009', 'c8888888-8888-8888-8888-888888888888', 'b5555555-5555-5555-5555-555555555555', CURRENT_DATE + INTERVAL '3 days', '15:00', '15:45', 45, 'consultation', 'scheduled', 'Knee pain evaluation', NULL, FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('bba11111-1111-1111-1111-111111111111', 'APT-2025-000010', 'c7777777-7777-7777-7777-777777777777', 'b4444444-4444-4444-4444-444444444444', CURRENT_DATE + INTERVAL '5 days', '11:00', '11:30', 30, 'checkup', 'scheduled', 'General health checkup', NULL, FALSE, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- VITAL SIGNS
-- ============================================================================
INSERT INTO vital_signs (id, patient_id, appointment_id, recorded_at, temperature_celsius, blood_pressure_systolic, blood_pressure_diastolic, pulse_rate, respiratory_rate, oxygen_saturation, weight_kg, height_cm, bmi, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'bb111111-1111-1111-1111-111111111111', '2025-01-10 09:05:00', 36.8, 130, 85, 72, 16, 98.0, 82.5, 175.0, 26.9, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c4444444-4444-4444-4444-444444444444', 'bb222222-2222-2222-2222-222222222222', '2025-01-10 10:05:00', 36.5, 100, 65, 90, 20, 99.0, 25.0, 110.0, 20.7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c3333333-3333-3333-3333-333333333333', 'bb333333-3333-3333-3333-333333333333', '2025-01-12 14:05:00', 36.7, 125, 80, 78, 18, 97.0, 78.0, 170.0, 27.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'bb444444-4444-4444-4444-444444444444', '2025-01-15 11:05:00', 36.9, 145, 90, 80, 17, 96.0, 85.0, 168.0, 30.1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- MEDICAL RECORDS
-- ============================================================================
INSERT INTO medical_records (id, record_number, patient_id, doctor_id, appointment_id, visit_date, chief_complaint, history_of_present_illness, physical_examination, assessment, diagnosis, icd_codes, treatment_plan, follow_up_instructions, follow_up_date, created_at, updated_at, created_by) VALUES
    ('cc111111-1111-1111-1111-111111111111', 'MR-2025-000001', 'c1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', 'bb111111-1111-1111-1111-111111111111', '2025-01-10', 'Routine checkup for hypertension', 'Patient reports good compliance with medications. No new symptoms.', 'BP 130/85, HR 72, regular. No edema. Heart sounds normal.', 'Hypertension well controlled on current regimen', ARRAY['Essential hypertension'], ARRAY['I10'], 'Continue Lisinopril 10mg daily. Diet and exercise counseling provided.', 'Return in 3 months for follow-up. Monitor BP at home weekly.', '2025-04-10', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('cc222222-2222-2222-2222-222222222222', 'MR-2025-000002', 'c4444444-4444-4444-4444-444444444444', 'b2222222-2222-2222-2222-222222222222', 'bb222222-2222-2222-2222-222222222222', '2025-01-10', 'Annual pediatric checkup', 'Routine well-child visit. No acute concerns.', 'Weight and height on track. Development milestones met. Heart and lungs clear.', 'Healthy child, normal development', ARRAY['Routine child health examination'], ARRAY['Z00.129'], 'Continue current nutrition. Encourage physical activity.', 'Annual checkup next year', '2026-01-10', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('cc333333-3333-3333-3333-333333333333', 'MR-2025-000003', 'c3333333-3333-3333-3333-333333333333', 'b3333333-3333-3333-3333-333333333333', 'bb333333-3333-3333-3333-333333333333', '2025-01-12', 'Asthma follow-up', 'Patient reports using rescue inhaler 2x per week. No nocturnal symptoms.', 'Lungs clear bilaterally. No wheezing. Good air entry.', 'Asthma well controlled', ARRAY['Mild persistent asthma'], ARRAY['J45.30'], 'Continue Salbutamol PRN. Review inhaler technique.', 'Follow-up in 6 months or sooner if symptoms worsen', '2025-07-12', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('cc444444-4444-4444-4444-444444444444', 'MR-2025-000004', 'c5555555-5555-5555-5555-555555555555', 'b3333333-3333-3333-3333-333333333333', 'bb444444-4444-4444-4444-444444444444', '2025-01-15', 'Chest discomfort', 'Patient reports intermittent chest discomfort for past week, not related to exertion.', 'BP 145/90, HR 80. ECG: Normal sinus rhythm, no ST changes. Chest exam unremarkable.', 'Atypical chest pain, likely musculoskeletal. CAD stable.', ARRAY['Atypical chest pain', 'Coronary artery disease'], ARRAY['R07.9', 'I25.1'], 'Continue cardiac medications. Trial of omeprazole for possible GERD component.', 'Return immediately if pain worsens or becomes exertional. Follow-up in 2 weeks.', '2025-01-29', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PRESCRIPTIONS
-- ============================================================================
INSERT INTO prescriptions (id, prescription_number, patient_id, doctor_id, appointment_id, medical_record_id, prescription_date, diagnosis, notes, status, is_refillable, refills_remaining, created_at, updated_at, created_by) VALUES
    ('dd111111-1111-1111-1111-111111111111', 'RX-2025-000001', 'c1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', 'bb111111-1111-1111-1111-111111111111', 'cc111111-1111-1111-1111-111111111111', '2025-01-10', 'Hypertension', 'Refill of maintenance medications', 'dispensed', TRUE, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('dd222222-2222-2222-2222-222222222222', 'RX-2025-000002', 'c3333333-3333-3333-3333-333333333333', 'b3333333-3333-3333-3333-333333333333', 'bb333333-3333-3333-3333-333333333333', 'cc333333-3333-3333-3333-333333333333', '2025-01-12', 'Asthma', 'Rescue inhaler refill', 'dispensed', TRUE, 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    ('dd333333-3333-3333-3333-333333333333', 'RX-2025-000003', 'c5555555-5555-5555-5555-555555555555', 'b3333333-3333-3333-3333-333333333333', 'bb444444-4444-4444-4444-444444444444', 'cc444444-4444-4444-4444-444444444444', '2025-01-15', 'Atypical chest pain, possible GERD', 'Trial of PPI', 'pending', FALSE, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PRESCRIPTION ITEMS
-- ============================================================================
INSERT INTO prescription_items (id, prescription_id, medicine_id, medicine_name, dosage, frequency, duration, quantity, quantity_dispensed, route_of_administration, instructions, is_substitution_allowed, is_dispensed, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'dd111111-1111-1111-1111-111111111111', 'e5555555-5555-5555-5555-555555555555', 'Lisinopril 10mg', '10mg', 'Once daily', '90 days', 90, 90, 'oral', 'Take in the morning with or without food', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'dd111111-1111-1111-1111-111111111111', 'e4444444-4444-4444-4444-444444444444', 'Metformin 500mg', '500mg', 'Twice daily', '90 days', 180, 180, 'oral', 'Take with meals', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'dd222222-2222-2222-2222-222222222222', 'e6666666-6666-6666-6666-666666666666', 'Salbutamol Inhaler', '100mcg', 'As needed', '3 months', 1, 1, 'inhalation', '2 puffs when needed for shortness of breath. Max 8 puffs per day.', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'dd333333-3333-3333-3333-333333333333', 'e7777777-7777-7777-7777-777777777777', 'Omeprazole 20mg', '20mg', 'Once daily', '14 days', 14, 0, 'oral', 'Take 30 minutes before breakfast', TRUE, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PRESCRIBED DEVICES
-- ============================================================================
INSERT INTO prescribed_devices (id, patient_id, doctor_id, device_id, prescription_date, issue_date, expected_return_date, is_permanent, condition_on_issue, notes, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'b5555555-5555-5555-5555-555555555555', 'f8888888-8888-8888-8888-888888888888', '2025-01-05', '2025-01-06', NULL, TRUE, 'excellent', 'Quad cane for mobility support. Patient to keep permanently.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c8888888-8888-8888-8888-888888888888', 'b5555555-5555-5555-5555-555555555555', 'f4444444-4444-4444-4444-444444444444', '2025-01-12', '2025-01-12', '2025-02-12', FALSE, 'new', 'Knee brace for left knee. Return after recovery.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- PATIENT DOCUMENTS (Lab results uploaded as documents)
-- ============================================================================
INSERT INTO patient_documents (id, patient_id, medical_record_id, document_type, title, description, file_path, upload_date, document_date, created_at, updated_at, created_by) VALUES
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'cc111111-1111-1111-1111-111111111111', 'lab_result', 'HbA1c Test Results', 'Quarterly diabetes monitoring', '/documents/patients/c1111111/lab_hba1c_2025_01.pdf', CURRENT_TIMESTAMP, '2025-01-08', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c1111111-1111-1111-1111-111111111111', 'cc111111-1111-1111-1111-111111111111', 'lab_result', 'Lipid Panel', 'Annual cholesterol screening', '/documents/patients/c1111111/lab_lipid_2025_01.pdf', CURRENT_TIMESTAMP, '2025-01-08', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c5555555-5555-5555-5555-555555555555', 'cc444444-4444-4444-4444-444444444444', 'imaging', 'Chest X-Ray', 'Routine chest imaging', '/documents/patients/c5555555/imaging_chest_2025_01.pdf', CURRENT_TIMESTAMP, '2025-01-14', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'c3333333-3333-3333-3333-333333333333', NULL, 'lab_result', 'Pulmonary Function Test', 'Annual spirometry for asthma monitoring', '/documents/patients/c3333333/lab_pft_2024_12.pdf', CURRENT_TIMESTAMP, '2024-12-15', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- INVENTORY TRANSACTIONS
-- ============================================================================
INSERT INTO inventory_transactions (id, medicine_inventory_id, medical_device_inventory_id, equipment_id, transaction_type, quantity, previous_quantity, new_quantity, reference_type, reference_id, transaction_date, created_at, updated_at, created_by) VALUES
    -- Medicine donations received (from donation aa111111)
    (uuid_generate_v4(), 'ee111111-1111-1111-1111-111111111111', NULL, NULL, 'donated', 200, 300, 500, 'donation', 'aa111111-1111-1111-1111-111111111111', '2025-01-07 10:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'ee333333-3333-3333-3333-333333333333', NULL, NULL, 'donated', 100, 100, 200, 'donation', 'aa111111-1111-1111-1111-111111111111', '2025-01-07 10:05:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Medicine donations received (from donation aa222222)
    (uuid_generate_v4(), 'ee111111-1111-1111-1111-111111111111', NULL, NULL, 'donated', 300, 200, 500, 'donation', 'aa222222-2222-2222-2222-222222222222', '2025-01-12 09:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'ee222222-2222-2222-2222-222222222222', NULL, NULL, 'donated', 150, 150, 300, 'donation', 'aa222222-2222-2222-2222-222222222222', '2025-01-12 09:05:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Medicines prescribed/dispensed (from prescription dd111111)
    (uuid_generate_v4(), 'ee555555-5555-5555-5555-555555555555', NULL, NULL, 'prescribed', 90, 270, 180, 'prescription', 'dd111111-1111-1111-1111-111111111111', '2025-01-10 10:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), 'ee444444-4444-4444-4444-444444444444', NULL, NULL, 'prescribed', 180, 330, 150, 'prescription', 'dd111111-1111-1111-1111-111111111111', '2025-01-10 10:05:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Medicines prescribed/dispensed (from prescription dd222222)
    (uuid_generate_v4(), 'ee666666-6666-6666-6666-666666666666', NULL, NULL, 'prescribed', 1, 51, 50, 'prescription', 'dd222222-2222-2222-2222-222222222222', '2025-01-12 15:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    -- Equipment donation received
    (uuid_generate_v4(), NULL, NULL, '01111111-1111-1111-1111-111111111111', 'donated', 1, 0, 1, 'donation', 'aa111111-1111-1111-1111-111111111111', '2025-01-07 11:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), NULL, NULL, '04444444-4444-4444-4444-444444444444', 'donated', 1, 0, 1, 'donation', 'aa111111-1111-1111-1111-111111111111', '2025-01-07 11:05:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin'),
    (uuid_generate_v4(), NULL, NULL, '05555555-5555-5555-5555-555555555555', 'donated', 1, 0, 1, 'donation', 'aa555555-5555-5555-5555-555555555555', '2024-11-18 14:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin');

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- This sample data includes:
-- - 4 additional users (beyond admin)
-- - 8 donors (various types)
-- - 6 doctors (2 sponsored by donors)
-- - 10 patients with allergies and medical history
-- - 12 medicines with inventory and expiry tracking
-- - 8 medical devices with inventory
-- - 8 pieces of equipment
-- - 5 donations with medicine, equipment, and device items
-- - 10 appointments (past, today, and future)
-- - 4 complete medical records with prescriptions
-- - Prescribed devices for 2 patients
-- - Patient documents including lab results

SELECT 'Sample data inserted successfully!' AS status;
