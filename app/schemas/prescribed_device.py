from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import EquipmentCondition


class PrescribedDeviceBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    device_id: UUID
    prescription_date: date
    issue_date: date | None = None
    return_date: date | None = None
    expected_return_date: date | None = None
    is_permanent: bool = False
    condition_on_issue: EquipmentCondition | None = None
    condition_on_return: EquipmentCondition | None = None
    notes: str | None = None


class PrescribedDeviceCreate(PrescribedDeviceBase):
    pass


class PrescribedDeviceUpdate(BaseModel):
    issue_date: date | None = None
    return_date: date | None = None
    expected_return_date: date | None = None
    is_permanent: bool | None = None
    condition_on_issue: EquipmentCondition | None = None
    condition_on_return: EquipmentCondition | None = None
    notes: str | None = None


class PrescribedDeviceResponse(PrescribedDeviceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PrescribedDeviceListResponse(BaseModel):
    data: list[PrescribedDeviceResponse]
    total: int
    page: int
    size: int

