from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MedicineBase(BaseModel):
    """Base schema for medicine."""

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

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class MedicineResponse(MedicineBase):
    """Schema for medicine response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime


class MedicineDetailResponse(MedicineResponse):
    """Schema for medicine response with inventory info."""

    inventory_quantity: Optional[int] = 0
    category_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "MedicineDetailResponse":
        """Build from a SQLAlchemy row of (Medicine, quantity, category_name)."""
        medicine = row[0]
        return cls.model_validate(
            {
                "id": medicine.id,
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
                "category_name": row[2],
            }
        )
