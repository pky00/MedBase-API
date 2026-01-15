from __future__ import annotations
from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import AppointmentStatus, AppointmentType


class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_date: date
    start_time: time
    end_time: time
    duration_minutes: int = Field(30, ge=5)
    appointment_type: AppointmentType = AppointmentType.consultation
    chief_complaint: str | None = None
    notes: str | None = None
    is_follow_up: bool = False
    previous_appointment_id: UUID | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_id: UUID | None = None
    doctor_id: UUID | None = None
    appointment_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = Field(None, ge=5)
    appointment_type: AppointmentType | None = None
    status: AppointmentStatus | None = None
    chief_complaint: str | None = None
    notes: str | None = None
    is_follow_up: bool | None = None
    previous_appointment_id: UUID | None = None


class AppointmentResponse(AppointmentBase):
    id: UUID
    appointment_number: str
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AppointmentListResponse(BaseModel):
    data: list[AppointmentResponse]
    total: int
    page: int
    size: int

