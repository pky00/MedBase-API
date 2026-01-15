from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DonationMedicineItemBase(BaseModel):
    donation_id: UUID
    medicine_id: UUID | None = None
    medicine_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., ge=1)
    unit: str | None = Field(None, max_length=50)
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    estimated_unit_value: Decimal | None = Field(None, ge=0)
    total_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationMedicineItemCreate(DonationMedicineItemBase):
    pass


class DonationMedicineItemUpdate(BaseModel):
    medicine_id: UUID | None = None
    medicine_name: str | None = Field(None, min_length=1, max_length=200)
    quantity: int | None = Field(None, ge=1)
    unit: str | None = Field(None, max_length=50)
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    estimated_unit_value: Decimal | None = Field(None, ge=0)
    total_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationMedicineItemResponse(DonationMedicineItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DonationMedicineItemListResponse(BaseModel):
    data: list[DonationMedicineItemResponse]
    total: int

