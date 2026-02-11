from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EquipmentCategoryBase(BaseModel):
    """Base schema for equipment category."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EquipmentCategoryCreate(EquipmentCategoryBase):
    """Schema for creating an equipment category."""
    pass


class EquipmentCategoryUpdate(BaseModel):
    """Schema for updating an equipment category."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class EquipmentCategoryResponse(EquipmentCategoryBase):
    """Schema for equipment category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
