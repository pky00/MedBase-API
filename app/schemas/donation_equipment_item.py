from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import EquipmentCondition


class DonationEquipmentItemBase(BaseModel):
    donation_id: UUID
    equipment_id: UUID | None = None
    equipment_name: str = Field(..., min_length=1, max_length=200)
    model: str | None = Field(None, max_length=100)
    serial_number: str | None = Field(None, max_length=100)
    quantity: int = Field(1, ge=1)
    equipment_condition: EquipmentCondition = EquipmentCondition.good
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationEquipmentItemCreate(DonationEquipmentItemBase):
    pass


class DonationEquipmentItemUpdate(BaseModel):
    equipment_id: UUID | None = None
    equipment_name: str | None = Field(None, min_length=1, max_length=200)
    model: str | None = Field(None, max_length=100)
    serial_number: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=1)
    equipment_condition: EquipmentCondition | None = None
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationEquipmentItemResponse(DonationEquipmentItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DonationEquipmentItemListResponse(BaseModel):
    data: list[DonationEquipmentItemResponse]
    total: int

