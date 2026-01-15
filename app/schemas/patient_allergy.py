from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import Severity


class PatientAllergyBase(BaseModel):
    allergen: str = Field(..., min_length=1, max_length=200)
    reaction: str | None = None
    severity: Severity = Severity.moderate
    notes: str | None = None


class PatientAllergyCreate(PatientAllergyBase):
    """Schema for creating a patient allergy."""
    pass


class PatientAllergyUpdate(BaseModel):
    allergen: str | None = Field(None, min_length=1, max_length=200)
    reaction: str | None = None
    severity: Severity | None = None
    notes: str | None = None


class PatientAllergyResponse(PatientAllergyBase):
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PatientAllergyListResponse(BaseModel):
    data: list[PatientAllergyResponse]
    total: int

