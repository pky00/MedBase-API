from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicalRecordBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_id: UUID | None = None
    visit_date: date
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    physical_examination: str | None = None
    assessment: str | None = None
    diagnosis: list[str] | None = None
    icd_codes: list[str] | None = None
    treatment_plan: str | None = None
    procedures_performed: str | None = None
    follow_up_instructions: str | None = None
    follow_up_date: date | None = None
    notes: str | None = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    visit_date: date | None = None
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    physical_examination: str | None = None
    assessment: str | None = None
    diagnosis: list[str] | None = None
    icd_codes: list[str] | None = None
    treatment_plan: str | None = None
    procedures_performed: str | None = None
    follow_up_instructions: str | None = None
    follow_up_date: date | None = None
    notes: str | None = None


class MedicalRecordResponse(MedicalRecordBase):
    id: UUID
    record_number: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicalRecordListResponse(BaseModel):
    data: list[MedicalRecordResponse]
    total: int
    page: int
    size: int

