from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import DonorType


class DonorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    donor_type: DonorType = DonorType.individual
    contact_person: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=20)
    alternative_phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    website: str | None = Field(None, max_length=255)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    notes: str | None = None
    is_active: bool = True


class DonorCreate(DonorBase):
    donor_code: str | None = Field(None, max_length=50)


class DonorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    donor_type: DonorType | None = None
    donor_code: str | None = Field(None, max_length=50)
    contact_person: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=20)
    alternative_phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    website: str | None = Field(None, max_length=255)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    notes: str | None = None
    is_active: bool | None = None


class DonorResponse(DonorBase):
    id: UUID
    donor_code: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DonorListResponse(BaseModel):
    data: list[DonorResponse]
    total: int
    page: int
    size: int

