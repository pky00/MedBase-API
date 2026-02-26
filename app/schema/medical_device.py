from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MedicalDeviceBase(BaseModel):
    """Base schema for medical device."""

    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    serial_number: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class MedicalDeviceCreate(MedicalDeviceBase):
    """Schema for creating a medical device."""
    pass


class MedicalDeviceUpdate(BaseModel):
    """Schema for updating a medical device."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    description: Optional[str] = None
    serial_number: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class MedicalDeviceResponse(MedicalDeviceBase):
    """Schema for medical device response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class MedicalDeviceDetailResponse(MedicalDeviceResponse):
    """Schema for medical device response with inventory info."""

    inventory_quantity: Optional[int] = 0
    category_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "MedicalDeviceDetailResponse":
        """Build from a SQLAlchemy row of (MedicalDevice, quantity, category_name)."""
        device = row[0]
        return cls.model_validate(
            {
                "id": device.id,
                "name": device.name,
                "category_id": device.category_id,
                "description": device.description,
                "serial_number": device.serial_number,
                "is_active": device.is_active,
                "is_deleted": device.is_deleted,
                "created_by": device.created_by,
                "created_at": device.created_at,
                "updated_by": device.updated_by,
                "updated_at": device.updated_at,
                "inventory_quantity": row[1] or 0,
                "category_name": row[2],
            }
        )
