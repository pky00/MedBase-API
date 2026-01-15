from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PrescriptionStatus


class PrescriptionBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_id: UUID | None = None
    medical_record_id: UUID | None = None
    prescription_date: date
    diagnosis: str | None = None
    notes: str | None = None
    pharmacy_notes: str | None = None
    is_refillable: bool = False
    refills_remaining: int = Field(0, ge=0)
    valid_until: date | None = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    prescription_date: date | None = None
    diagnosis: str | None = None
    notes: str | None = None
    pharmacy_notes: str | None = None
    status: PrescriptionStatus | None = None
    is_refillable: bool | None = None
    refills_remaining: int | None = Field(None, ge=0)
    valid_until: date | None = None


class PrescriptionResponse(PrescriptionBase):
    id: UUID
    prescription_number: str
    status: PrescriptionStatus
    dispensed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PrescriptionListResponse(BaseModel):
    data: list[PrescriptionResponse]
    total: int
    page: int
    size: int

