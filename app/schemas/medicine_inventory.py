from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicineInventoryBase(BaseModel):
    medicine_id: UUID
    quantity: int = Field(0, ge=0)


class MedicineInventoryCreate(MedicineInventoryBase):
    pass


class MedicineInventoryUpdate(BaseModel):
    quantity: int | None = Field(None, ge=0)


class MedicineInventoryResponse(MedicineInventoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicineInventoryListResponse(BaseModel):
    data: list[MedicineInventoryResponse]
    total: int

