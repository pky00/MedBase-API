from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MedicalRecordBase(BaseModel):
    """Base schema for medical record."""

    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_notes: Optional[str] = None
    follow_up_date: Optional[date] = None


class MedicalRecordCreate(MedicalRecordBase):
    """Schema for creating a medical record."""
    pass


class MedicalRecordUpdate(MedicalRecordBase):
    """Schema for updating a medical record."""
    pass


class MedicalRecordResponse(MedicalRecordBase):
    """Schema for medical record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    patient_name: Optional[str] = None
