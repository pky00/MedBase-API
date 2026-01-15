from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import EquipmentCondition


class MedicalDeviceInventoryBase(BaseModel):
    device_id: UUID
    serial_number: str | None = Field(None, max_length=100)
    condition: EquipmentCondition = EquipmentCondition.good
    is_donation: bool = False
    donor_id: UUID | None = None
    notes: str | None = None
    is_available: bool = True


class MedicalDeviceInventoryCreate(MedicalDeviceInventoryBase):
    pass


class MedicalDeviceInventoryUpdate(BaseModel):
    serial_number: str | None = Field(None, max_length=100)
    condition: EquipmentCondition | None = None
    is_donation: bool | None = None
    donor_id: UUID | None = None
    notes: str | None = None
    is_available: bool | None = None


class MedicalDeviceInventoryResponse(MedicalDeviceInventoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicalDeviceInventoryListResponse(BaseModel):
    data: list[MedicalDeviceInventoryResponse]
    total: int
    page: int
    size: int

