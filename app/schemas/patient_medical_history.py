from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import Severity


class PatientMedicalHistoryBase(BaseModel):
    condition_name: str = Field(..., min_length=1, max_length=200)
    icd_code: str | None = Field(None, max_length=20)
    diagnosis_date: date | None = None
    resolution_date: date | None = None
    is_chronic: bool = False
    is_current: bool = True
    severity: Severity | None = None
    notes: str | None = None


class PatientMedicalHistoryCreate(PatientMedicalHistoryBase):
    """Schema for creating a patient medical history entry."""
    pass


class PatientMedicalHistoryUpdate(BaseModel):
    condition_name: str | None = Field(None, min_length=1, max_length=200)
    icd_code: str | None = Field(None, max_length=20)
    diagnosis_date: date | None = None
    resolution_date: date | None = None
    is_chronic: bool | None = None
    is_current: bool | None = None
    severity: Severity | None = None
    notes: str | None = None


class PatientMedicalHistoryResponse(PatientMedicalHistoryBase):
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PatientMedicalHistoryListResponse(BaseModel):
    data: list[PatientMedicalHistoryResponse]
    total: int

