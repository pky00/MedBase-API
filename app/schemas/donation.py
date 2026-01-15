from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DonationType


class DonationBase(BaseModel):
    donor_id: UUID
    donation_type: DonationType
    donation_date: date
    received_date: date | None = None
    total_estimated_value: Decimal | None = Field(None, ge=0)
    total_items_count: int = Field(0, ge=0)
    notes: str | None = None


class DonationCreate(DonationBase):
    pass


class DonationUpdate(BaseModel):
    donation_type: DonationType | None = None
    donation_date: date | None = None
    received_date: date | None = None
    total_estimated_value: Decimal | None = Field(None, ge=0)
    total_items_count: int | None = Field(None, ge=0)
    notes: str | None = None


class DonationResponse(DonationBase):
    id: UUID
    donation_number: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DonationListResponse(BaseModel):
    data: list[DonationResponse]
    total: int
    page: int
    size: int

