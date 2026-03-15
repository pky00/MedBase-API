from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schema.medicine_category import MedicineCategoryResponse


class MedicineBase(BaseModel):
    """Base schema for medicine."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class MedicineCreate(MedicineBase):
    """Schema for creating a medicine."""
    pass


class MedicineUpdate(BaseModel):
    """Schema for updating a medicine."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class MedicineResponse(MedicineBase):
    """Schema for medicine response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class MedicineDetailResponse(MedicineResponse):
    """Schema for medicine response with inventory and category info."""

    inventory_quantity: Optional[int] = 0
    category: Optional[MedicineCategoryResponse] = None

    @classmethod
    def from_row(cls, row) -> "MedicineDetailResponse":
        """Build from a SQLAlchemy row of (Medicine, quantity, MedicineCategory|None)."""
        medicine = row[0]
        category_obj = row[2]
        return cls.model_validate(
            {
                "id": medicine.id,
                "item_id": medicine.item_id,
                "code": medicine.code,
                "name": medicine.name,
                "category_id": medicine.category_id,
                "description": medicine.description,
                "unit": medicine.unit,
                "is_active": medicine.is_active,
                "is_deleted": medicine.is_deleted,
                "created_by": medicine.created_by,
                "created_at": medicine.created_at,
                "updated_by": medicine.updated_by,
                "updated_at": medicine.updated_at,
                "inventory_quantity": row[1] or 0,
                "category": MedicineCategoryResponse.model_validate(category_obj) if category_obj else None,
            }
        )
