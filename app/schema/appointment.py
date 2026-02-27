from datetime import datetime, date
from decimal import Decimal
from enum import StrEnum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentType(StrEnum):
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"


class AppointmentLocation(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class AppointmentBase(BaseModel):
    """Base schema for appointment."""

    patient_id: int
    doctor_id: Optional[int] = None
    partner_id: Optional[int] = None
    appointment_date: datetime
    type: AppointmentType
    location: AppointmentLocation = AppointmentLocation.INTERNAL
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment."""
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    partner_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
    type: Optional[AppointmentType] = None
    location: Optional[AppointmentLocation] = None
    notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    """Schema for updating appointment status."""

    status: AppointmentStatus


class VitalSignResponse(BaseModel):
    """Schema for vital sign in appointment detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[Decimal] = None
    respiratory_rate: Optional[int] = None
    weight: Optional[Decimal] = None
    height: Optional[Decimal] = None
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class MedicalRecordResponse(BaseModel):
    """Schema for medical record in appointment detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    partner_id: Optional[int] = None
    appointment_date: datetime
    status: str
    type: str
    location: str
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    partner_name: Optional[str] = None


class AppointmentDetailResponse(AppointmentResponse):
    """Schema for appointment detail response with vitals and medical record."""

    vital_signs: Optional[VitalSignResponse] = None
    medical_record: Optional[MedicalRecordResponse] = None
