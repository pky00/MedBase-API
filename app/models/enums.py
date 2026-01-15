"""Database enums used across models."""
from enum import Enum


class GenderType(str, Enum):
    """Gender types for patients and doctors."""
    male = "male"
    female = "female"


class BloodType(str, Enum):
    """Blood types."""
    A_positive = "A+"
    A_negative = "A-"
    B_positive = "B+"
    B_negative = "B-"
    AB_positive = "AB+"
    AB_negative = "AB-"
    O_positive = "O+"
    O_negative = "O-"
    unknown = "unknown"


class MaritalStatus(str, Enum):
    """Marital status options."""
    single = "single"
    married = "married"
    divorced = "divorced"
    widowed = "widowed"


class Severity(str, Enum):
    """Severity levels for allergies and medical conditions."""
    mild = "mild"
    moderate = "moderate"
    severe = "severe"
    life_threatening = "life_threatening"


class AppointmentStatus(str, Enum):
    """Appointment status options."""
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"


class AppointmentType(str, Enum):
    """Types of appointments."""
    consultation = "consultation"
    follow_up = "follow_up"
    emergency = "emergency"
    checkup = "checkup"


class PrescriptionStatus(str, Enum):
    """Prescription status options."""
    pending = "pending"
    dispensed = "dispensed"
    cancelled = "cancelled"


class DonorType(str, Enum):
    """Types of donors."""
    individual = "individual"
    organization = "organization"
    government = "government"
    ngo = "ngo"
    pharmaceutical_company = "pharmaceutical_company"


class DonationType(str, Enum):
    """Types of donations."""
    medicine = "medicine"
    equipment = "equipment"
    medical_device = "medical_device"
    mixed = "mixed"


class EquipmentCondition(str, Enum):
    """Condition of equipment and devices."""
    new = "new"
    excellent = "excellent"
    good = "good"
    fair = "fair"
    needs_repair = "needs_repair"
    out_of_service = "out_of_service"


class DocumentType(str, Enum):
    """Types of patient documents."""
    lab_result = "lab_result"
    imaging = "imaging"
    prescription = "prescription"
    referral = "referral"
    consent_form = "consent_form"
    insurance_document = "insurance_document"
    identification = "identification"
    medical_history = "medical_history"
    discharge_summary = "discharge_summary"
    other = "other"


class DosageForm(str, Enum):
    """Medication dosage forms."""
    tablet = "tablet"
    capsule = "capsule"
    syrup = "syrup"
    injection = "injection"
    cream = "cream"
    ointment = "ointment"
    drops = "drops"
    inhaler = "inhaler"
    patch = "patch"
    suppository = "suppository"
    powder = "powder"
    solution = "solution"
    suspension = "suspension"
    gel = "gel"
    spray = "spray"
    other = "other"


class InventoryTransactionType(str, Enum):
    """Types of inventory transactions."""
    prescribed = "prescribed"
    donated = "donated"
    expired = "expired"
    damaged = "damaged"
    returned = "returned"
    purchased = "purchased"
    lost = "lost"
    stolen = "stolen"


class ReferenceType(str, Enum):
    """Reference types for inventory transactions."""
    prescription = "prescription"
    donation = "donation"
    adjustment = "adjustment"
    transfer = "transfer"
    disposal = "disposal"
