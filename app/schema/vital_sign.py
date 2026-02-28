from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VitalSignBase(BaseModel):
    """Base schema for vital signs."""

    blood_pressure_systolic: Optional[int] = Field(None, ge=0, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=0, le=300)
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    temperature: Optional[Decimal] = Field(None, ge=0, le=50)
    respiratory_rate: Optional[int] = Field(None, ge=0, le=100)
    weight: Optional[Decimal] = Field(None, ge=0, le=1000)
    height: Optional[Decimal] = Field(None, ge=0, le=300)
    notes: Optional[str] = None


class VitalSignCreate(VitalSignBase):
    """Schema for creating vital signs."""
    pass


class VitalSignUpdate(VitalSignBase):
    """Schema for updating vital signs."""
    pass


class VitalSignResponse(VitalSignBase):
    """Schema for vital sign response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
