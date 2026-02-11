from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EquipmentBase(BaseModel):
    """Base schema for equipment."""

    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    condition: Optional[str] = Field(None, pattern="^(new|good|fair|poor)$")
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment."""
    pass


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    condition: Optional[str] = Field(None, pattern="^(new|good|fair|poor)$")
    is_active: Optional[bool] = None


class EquipmentResponse(EquipmentBase):
    """Schema for equipment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime


class EquipmentDetailResponse(EquipmentResponse):
    """Schema for equipment response with inventory info."""

    inventory_quantity: Optional[int] = 0
    category_name: Optional[str] = None
