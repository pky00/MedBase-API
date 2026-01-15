from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicineExpiryBase(BaseModel):
    medicine_id: UUID
    batch_number: str | None = Field(None, max_length=100)
    quantity: int = Field(0, ge=0)
    expiry_date: date
    actual_expiry_date: date
    manufacturing_date: date | None = None
    notes: str | None = None


class MedicineExpiryCreate(MedicineExpiryBase):
    pass


class MedicineExpiryUpdate(BaseModel):
    batch_number: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=0)
    expiry_date: date | None = None
    actual_expiry_date: date | None = None
    manufacturing_date: date | None = None
    notes: str | None = None


class MedicineExpiryResponse(MedicineExpiryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicineExpiryListResponse(BaseModel):
    data: list[MedicineExpiryResponse]
    total: int

