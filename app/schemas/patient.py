from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import GenderType, BloodType, MaritalStatus


class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: GenderType
    blood_type: BloodType | None = BloodType.unknown
    national_id: str | None = Field(None, max_length=50)
    passport_number: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=20)
    alternative_phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=100)
    country: str | None = Field("Unknown", max_length=100)
    occupation: str | None = Field(None, max_length=100)
    marital_status: MaritalStatus | None = None
    notes: str | None = None


class PatientCreate(PatientBase):
    """Schema for creating a patient. patient_number is auto-generated."""
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    gender: GenderType | None = None
    blood_type: BloodType | None = None
    national_id: str | None = Field(None, max_length=50)
    passport_number: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=20)
    alternative_phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    occupation: str | None = Field(None, max_length=100)
    marital_status: MaritalStatus | None = None
    notes: str | None = None


class PatientResponse(PatientBase):
    id: UUID
    patient_number: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    data: list[PatientResponse]
    total: int
    page: int
    size: int

