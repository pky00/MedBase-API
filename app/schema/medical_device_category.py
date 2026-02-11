from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MedicalDeviceCategoryBase(BaseModel):
    """Base schema for medical device category."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class MedicalDeviceCategoryCreate(MedicalDeviceCategoryBase):
    """Schema for creating a medical device category."""
    pass


class MedicalDeviceCategoryUpdate(BaseModel):
    """Schema for updating a medical device category."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class MedicalDeviceCategoryResponse(MedicalDeviceCategoryBase):
    """Schema for medical device category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
