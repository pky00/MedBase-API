from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class VitalSignBase(BaseModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    temperature_celsius: Decimal | None = Field(None, ge=30, le=45)
    blood_pressure_systolic: int | None = Field(None, ge=50, le=300)
    blood_pressure_diastolic: int | None = Field(None, ge=30, le=200)
    pulse_rate: int | None = Field(None, ge=20, le=300)
    respiratory_rate: int | None = Field(None, ge=5, le=60)
    oxygen_saturation: Decimal | None = Field(None, ge=0, le=100)
    weight_kg: Decimal | None = Field(None, ge=0, le=500)
    height_cm: Decimal | None = Field(None, ge=0, le=300)
    bmi: Decimal | None = Field(None, ge=5, le=100)
    blood_glucose: Decimal | None = Field(None, ge=0, le=1000)
    pain_level: int | None = Field(None, ge=0, le=10)
    notes: str | None = None


class VitalSignCreate(VitalSignBase):
    pass


class VitalSignUpdate(BaseModel):
    appointment_id: UUID | None = None
    temperature_celsius: Decimal | None = Field(None, ge=30, le=45)
    blood_pressure_systolic: int | None = Field(None, ge=50, le=300)
    blood_pressure_diastolic: int | None = Field(None, ge=30, le=200)
    pulse_rate: int | None = Field(None, ge=20, le=300)
    respiratory_rate: int | None = Field(None, ge=5, le=60)
    oxygen_saturation: Decimal | None = Field(None, ge=0, le=100)
    weight_kg: Decimal | None = Field(None, ge=0, le=500)
    height_cm: Decimal | None = Field(None, ge=0, le=300)
    bmi: Decimal | None = Field(None, ge=5, le=100)
    blood_glucose: Decimal | None = Field(None, ge=0, le=1000)
    pain_level: int | None = Field(None, ge=0, le=10)
    notes: str | None = None


class VitalSignResponse(VitalSignBase):
    id: UUID
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VitalSignListResponse(BaseModel):
    data: list[VitalSignResponse]
    total: int

