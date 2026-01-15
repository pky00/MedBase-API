from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PrescriptionItemBase(BaseModel):
    prescription_id: UUID
    medicine_id: UUID | None = None
    medicine_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str | None = Field(None, max_length=100)
    quantity: int = Field(..., ge=1)
    route_of_administration: str | None = Field(None, max_length=100)
    instructions: str | None = None
    is_substitution_allowed: bool = True
    notes: str | None = None


class PrescriptionItemCreate(PrescriptionItemBase):
    pass


class PrescriptionItemUpdate(BaseModel):
    medicine_id: UUID | None = None
    medicine_name: str | None = Field(None, min_length=1, max_length=200)
    dosage: str | None = Field(None, min_length=1, max_length=100)
    frequency: str | None = Field(None, min_length=1, max_length=100)
    duration: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=1)
    quantity_dispensed: int | None = Field(None, ge=0)
    route_of_administration: str | None = Field(None, max_length=100)
    instructions: str | None = None
    is_substitution_allowed: bool | None = None
    is_dispensed: bool | None = None
    notes: str | None = None


class PrescriptionItemResponse(PrescriptionItemBase):
    id: UUID
    quantity_dispensed: int
    is_dispensed: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PrescriptionItemListResponse(BaseModel):
    data: list[PrescriptionItemResponse]
    total: int

