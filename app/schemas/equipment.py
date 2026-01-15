from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import EquipmentCondition


class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category_id: UUID | None = None
    model: str | None = Field(None, max_length=100)
    manufacturer: str | None = Field(None, max_length=200)
    serial_number: str | None = Field(None, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    description: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(None, ge=0)
    is_donation: bool = False
    donor_id: UUID | None = None
    donation_id: UUID | None = None
    equipment_condition: EquipmentCondition = EquipmentCondition.good
    is_portable: bool = False
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    asset_code: str | None = Field(None, max_length=50)


class EquipmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    asset_code: str | None = Field(None, max_length=50)
    category_id: UUID | None = None
    model: str | None = Field(None, max_length=100)
    manufacturer: str | None = Field(None, max_length=200)
    serial_number: str | None = Field(None, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    description: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(None, ge=0)
    is_donation: bool | None = None
    donor_id: UUID | None = None
    donation_id: UUID | None = None
    equipment_condition: EquipmentCondition | None = None
    is_portable: bool | None = None
    is_active: bool | None = None


class EquipmentResponse(EquipmentBase):
    id: UUID
    asset_code: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentListResponse(BaseModel):
    data: list[EquipmentResponse]
    total: int
    page: int
    size: int

