from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.schema.inventory import ItemType


class DonationItemBase(BaseModel):
    """Base schema for donation item."""

    item_type: ItemType
    item_id: int
    quantity: int = Field(..., gt=0)


class DonationItemCreate(DonationItemBase):
    """Schema for creating a donation item."""
    pass


class DonationItemUpdate(BaseModel):
    """Schema for updating a donation item."""

    item_type: Optional[ItemType] = None
    item_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0)


class DonationItemResponse(DonationItemBase):
    """Schema for donation item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
    item_name: Optional[str] = None


class DonationBase(BaseModel):
    """Base schema for donation."""

    partner_id: int
    donation_date: date
    notes: Optional[str] = None


class DonationCreate(DonationBase):
    """Schema for creating a donation with optional items."""

    items: Optional[List[DonationItemCreate]] = None


class DonationUpdate(BaseModel):
    """Schema for updating a donation."""

    partner_id: Optional[int] = None
    donation_date: Optional[date] = None
    notes: Optional[str] = None


class DonationResponse(DonationBase):
    """Schema for donation response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
    partner_name: Optional[str] = None


class DonationDetailResponse(DonationResponse):
    """Schema for donation response with items."""

    items: List[DonationItemResponse] = []
