from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.enums import InventoryTransactionType, ReferenceType


class InventoryTransactionBase(BaseModel):
    medicine_inventory_id: UUID | None = None
    medical_device_inventory_id: UUID | None = None
    equipment_id: UUID | None = None
    transaction_type: InventoryTransactionType
    quantity: int
    previous_quantity: int
    new_quantity: int
    reference_type: ReferenceType | None = None
    reference_id: UUID | None = None


class InventoryTransactionCreate(InventoryTransactionBase):
    transaction_date: datetime | None = None


class InventoryTransactionResponse(InventoryTransactionBase):
    id: UUID
    transaction_date: datetime
    created_at: datetime
    created_by: str | None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InventoryTransactionListResponse(BaseModel):
    data: list[InventoryTransactionResponse]
    total: int
    page: int
    size: int

