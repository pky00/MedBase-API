from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicalDeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category_id: UUID | None = None
    manufacturer: str | None = Field(None, max_length=200)
    model: str | None = Field(None, max_length=100)
    description: str | None = None
    specifications: str | None = None
    size: str | None = Field(None, max_length=50)
    is_reusable: bool = True
    requires_fitting: bool = False
    purchase_price: Decimal | None = Field(None, ge=0)
    is_active: bool = True


class MedicalDeviceCreate(MedicalDeviceBase):
    code: str | None = Field(None, max_length=50)


class MedicalDeviceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    code: str | None = Field(None, max_length=50)
    category_id: UUID | None = None
    manufacturer: str | None = Field(None, max_length=200)
    model: str | None = Field(None, max_length=100)
    description: str | None = None
    specifications: str | None = None
    size: str | None = Field(None, max_length=50)
    is_reusable: bool | None = None
    requires_fitting: bool | None = None
    purchase_price: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None


class MedicalDeviceResponse(MedicalDeviceBase):
    id: UUID
    code: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicalDeviceListResponse(BaseModel):
    data: list[MedicalDeviceResponse]
    total: int
    page: int
    size: int

