from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DonationType, EquipmentCondition


class DonationBase(BaseModel):
    donor_id: UUID
    donation_type: DonationType
    donation_date: date
    received_date: date | None = None
    total_estimated_value: Decimal | None = Field(None, ge=0)
    total_items_count: int = Field(0, ge=0)
    notes: str | None = None


class DonationCreate(DonationBase):
    pass


class DonationUpdate(BaseModel):
    donation_type: DonationType | None = None
    donation_date: date | None = None
    received_date: date | None = None
    total_estimated_value: Decimal | None = Field(None, ge=0)
    total_items_count: int | None = Field(None, ge=0)
    notes: str | None = None


# Medicine Item Schemas
class DonationMedicineItemResponse(BaseModel):
    id: UUID
    donation_id: UUID
    medicine_id: UUID | None
    medicine_name: str
    quantity: int
    unit: str | None
    manufacturing_date: date | None
    expiry_date: date | None
    estimated_unit_value: Decimal | None
    total_value: Decimal | None
    condition_notes: str | None
    is_deleted: bool = False
    created_at: datetime
    created_by: str | None
    updated_at: datetime
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class DonationMedicineItemCreate(BaseModel):
    medicine_id: UUID | None = None
    medicine_name: str
    quantity: int = Field(gt=0)
    unit: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    estimated_unit_value: Decimal | None = Field(None, ge=0)
    total_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationMedicineItemUpdate(BaseModel):
    medicine_id: UUID | None = None
    medicine_name: str | None = None
    quantity: int | None = Field(None, gt=0)
    unit: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    estimated_unit_value: Decimal | None = Field(None, ge=0)
    total_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None
    is_deleted: bool | None = None


# Equipment Item Schemas
class DonationEquipmentItemResponse(BaseModel):
    id: UUID
    donation_id: UUID
    equipment_id: UUID | None
    equipment_name: str
    model: str | None
    serial_number: str | None
    quantity: int
    equipment_condition: EquipmentCondition
    estimated_value: Decimal | None
    condition_notes: str | None
    is_deleted: bool = False
    created_at: datetime
    created_by: str | None
    updated_at: datetime
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class DonationEquipmentItemCreate(BaseModel):
    equipment_id: UUID | None = None
    equipment_name: str
    model: str | None = None
    serial_number: str | None = None
    quantity: int = Field(default=1, gt=0)
    equipment_condition: EquipmentCondition = EquipmentCondition.good
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationEquipmentItemUpdate(BaseModel):
    equipment_id: UUID | None = None
    equipment_name: str | None = None
    model: str | None = None
    serial_number: str | None = None
    quantity: int | None = Field(None, gt=0)
    equipment_condition: EquipmentCondition | None = None
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None
    is_deleted: bool | None = None


# Medical Device Item Schemas
class DonationMedicalDeviceItemResponse(BaseModel):
    id: UUID
    donation_id: UUID
    device_id: UUID | None
    device_name: str
    model: str | None
    serial_number: str | None
    quantity: int
    device_condition: EquipmentCondition
    estimated_value: Decimal | None
    condition_notes: str | None
    is_deleted: bool = False
    created_at: datetime
    created_by: str | None
    updated_at: datetime
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class DonationMedicalDeviceItemCreate(BaseModel):
    device_id: UUID | None = None
    device_name: str
    model: str | None = None
    serial_number: str | None = None
    quantity: int = Field(default=1, gt=0)
    device_condition: EquipmentCondition = EquipmentCondition.good
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None


class DonationMedicalDeviceItemUpdate(BaseModel):
    device_id: UUID | None = None
    device_name: str | None = None
    model: str | None = None
    serial_number: str | None = None
    quantity: int | None = Field(None, gt=0)
    device_condition: EquipmentCondition | None = None
    estimated_value: Decimal | None = Field(None, ge=0)
    condition_notes: str | None = None
    is_deleted: bool | None = None


class DonationResponse(DonationBase):
    id: UUID
    donation_number: str
    created_at: datetime
    updated_at: datetime

    # Item lists
    medicine_items: List[DonationMedicineItemResponse] = []
    equipment_items: List[DonationEquipmentItemResponse] = []
    medical_device_items: List[DonationMedicalDeviceItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DonationListResponse(BaseModel):
    data: list[DonationResponse]
    total: int
    page: int
    size: int

