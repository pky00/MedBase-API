from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EquipmentCondition(str, Enum):
    """Equipment condition values."""

    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class EquipmentBase(BaseModel):
    """Base schema for equipment."""

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
    """Schema for equipment response with inventory info."""

    inventory_quantity: Optional[int] = 0
    category_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "EquipmentDetailResponse":
        """Build from a SQLAlchemy row of (Equipment, quantity, category_name)."""
        equipment = row[0]
        return cls.model_validate(
            {
                "id": equipment.id,
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
                "category_name": row[2],
            }
        )
