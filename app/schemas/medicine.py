from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DosageForm


class MedicineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    generic_name: str | None = Field(None, max_length=200)
    brand_name: str | None = Field(None, max_length=200)
    category_id: UUID | None = None
    manufacturer: str | None = Field(None, max_length=200)
    dosage_form: DosageForm
    strength: str | None = Field(None, max_length=100)
    unit: str = Field(..., max_length=50)
    package_size: str | None = Field(None, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    purchase_price: Decimal | None = Field(None, ge=0)
    description: str | None = None
    indications: str | None = None
    contraindications: str | None = None
    side_effects: str | None = None
    storage_conditions: str | None = None
    requires_prescription: bool = True
    is_controlled_substance: bool = False
    is_active: bool = True


class MedicineCreate(MedicineBase):
    code: str | None = Field(None, max_length=50)


class MedicineUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    code: str | None = Field(None, max_length=50)
    generic_name: str | None = Field(None, max_length=200)
    brand_name: str | None = Field(None, max_length=200)
    category_id: UUID | None = None
    manufacturer: str | None = Field(None, max_length=200)
    dosage_form: DosageForm | None = None
    strength: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    package_size: str | None = Field(None, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    purchase_price: Decimal | None = Field(None, ge=0)
    description: str | None = None
    indications: str | None = None
    contraindications: str | None = None
    side_effects: str | None = None
    storage_conditions: str | None = None
    requires_prescription: bool | None = None
    is_controlled_substance: bool | None = None
    is_active: bool | None = None


class MedicineResponse(MedicineBase):
    id: UUID
    code: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicineListResponse(BaseModel):
    data: list[MedicineResponse]
    total: int
    page: int
    size: int

