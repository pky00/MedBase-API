from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DoctorType(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    PARTNER_PROVIDED = "partner_provided"


class DoctorBase(BaseModel):
    """Base schema for doctor."""

    name: str = Field(..., min_length=1, max_length=255)
    specialization: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    type: DoctorType
    partner_id: Optional[int] = None
    is_active: bool = True


class DoctorCreate(DoctorBase):
    """Schema for creating a doctor."""
    third_party_id: Optional[int] = None


class DoctorUpdate(BaseModel):
    """Schema for updating a doctor."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    specialization: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    type: Optional[DoctorType] = None
    partner_id: Optional[int] = None
    is_active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    """Schema for doctor response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    third_party_id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime


class DoctorDetailResponse(DoctorResponse):
    """Schema for doctor response with partner name."""

    partner_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "DoctorDetailResponse":
        """Build from a SQLAlchemy row of (Doctor, partner_name)."""
        doctor = row[0]
        return cls.model_validate(
            {
                "id": doctor.id,
                "third_party_id": doctor.third_party_id,
                "name": doctor.name,
                "specialization": doctor.specialization,
                "phone": doctor.phone,
                "email": doctor.email,
                "type": doctor.type,
                "partner_id": doctor.partner_id,
                "is_active": doctor.is_active,
                "is_deleted": doctor.is_deleted,
                "created_by": doctor.created_by,
                "created_at": doctor.created_at,
                "updated_by": doctor.updated_by,
                "updated_at": doctor.updated_at,
                "partner_name": row[1],
            }
        )
