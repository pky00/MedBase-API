from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import GenderType


class DoctorBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    specialization: str = Field(..., min_length=1, max_length=150)
    gender: GenderType | None = None
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None
    qualification: str | None = None
    bio: str | None = None


class DoctorCreate(DoctorBase):
    user_id: UUID | None = None
    donor_id: UUID | None = None


class DoctorUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    specialization: str | None = Field(None, min_length=1, max_length=150)
    gender: GenderType | None = None
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = None
    qualification: str | None = None
    bio: str | None = None
    user_id: UUID | None = None
    donor_id: UUID | None = None


class DoctorResponse(DoctorBase):
    id: UUID
    user_id: UUID | None
    donor_id: UUID | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DoctorListResponse(BaseModel):
    data: list[DoctorResponse]
    total: int
    page: int
    size: int

