from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schema.equipment_category import EquipmentCategoryResponse


class EquipmentCondition(str, Enum):
    """Equipment condition values."""

    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class EquipmentBase(BaseModel):
    """Base schema for equipment."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    condition: Optional[EquipmentCondition] = None
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment."""
    pass


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    condition: Optional[EquipmentCondition] = None
    is_active: Optional[bool] = None


class EquipmentResponse(EquipmentBase):
    """Schema for equipment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class EquipmentDetailResponse(EquipmentResponse):
    """Schema for equipment response with inventory and category info."""

    inventory_quantity: Optional[int] = 0
    category: Optional[EquipmentCategoryResponse] = None

    @classmethod
    def from_row(cls, row) -> "EquipmentDetailResponse":
        """Build from a SQLAlchemy row of (Equipment, quantity, EquipmentCategory|None)."""
        equipment = row[0]
        category_obj = row[2]
        return cls.model_validate(
            {
                "id": equipment.id,
                "code": equipment.code,
                "name": equipment.name,
                "category_id": equipment.category_id,
                "description": equipment.description,
                "condition": equipment.condition,
                "is_active": equipment.is_active,
                "is_deleted": equipment.is_deleted,
                "created_by": equipment.created_by,
                "created_at": equipment.created_at,
                "updated_by": equipment.updated_by,
                "updated_at": equipment.updated_at,
                "inventory_quantity": row[1] or 0,
                "category": EquipmentCategoryResponse.model_validate(category_obj) if category_obj else None,
            }
        )
