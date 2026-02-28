from datetime import datetime, date
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TreatmentStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"


class TreatmentBase(BaseModel):
    """Base schema for treatment."""

    patient_id: int
    partner_id: int
    appointment_id: Optional[int] = None
    treatment_type: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    treatment_date: Optional[date] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class TreatmentCreate(TreatmentBase):
    """Schema for creating a treatment."""
    status: TreatmentStatus = TreatmentStatus.IN_PROGRESS


class TreatmentUpdate(BaseModel):
    """Schema for updating a treatment."""

    patient_id: Optional[int] = None
    partner_id: Optional[int] = None
    appointment_id: Optional[int] = None
    treatment_type: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    treatment_date: Optional[date] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class TreatmentStatusUpdate(BaseModel):
    """Schema for updating treatment status."""

    status: TreatmentStatus


class TreatmentResponse(BaseModel):
    """Schema for treatment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    appointment_id: Optional[int] = None
    partner_id: int
    treatment_type: str
    description: Optional[str] = None
    treatment_date: Optional[date] = None
    status: str
    cost: Optional[Decimal] = None
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    patient_name: Optional[str] = None
    partner_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "TreatmentResponse":
        """Build from a SQLAlchemy row of (Treatment, patient_name, partner_name)."""
        treatment = row[0]
        return cls.model_validate(
            {
                "id": treatment.id,
                "patient_id": treatment.patient_id,
                "appointment_id": treatment.appointment_id,
                "partner_id": treatment.partner_id,
                "treatment_type": treatment.treatment_type,
                "description": treatment.description,
                "treatment_date": treatment.treatment_date,
                "status": treatment.status,
                "cost": treatment.cost,
                "notes": treatment.notes,
                "is_deleted": treatment.is_deleted,
                "created_by": treatment.created_by,
                "created_at": treatment.created_at,
                "updated_by": treatment.updated_by,
                "updated_at": treatment.updated_at,
                "patient_name": row[1],
                "partner_name": row[2],
            }
        )
