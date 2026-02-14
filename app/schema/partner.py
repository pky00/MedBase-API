from datetime import datetime
from enum import StrEnum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class PartnerType(StrEnum):
    DONOR = "donor"
    REFERRAL = "referral"
    BOTH = "both"


class OrganizationType(StrEnum):
    NGO = "NGO"
    ORGANIZATION = "organization"
    INDIVIDUAL = "individual"
    HOSPITAL = "hospital"
    MEDICAL_CENTER = "medical_center"


class PartnerBase(BaseModel):
    """Base schema for partner."""

    name: str = Field(..., min_length=1, max_length=255)
    partner_type: PartnerType
    organization_type: Optional[OrganizationType] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    is_active: bool = True


class PartnerCreate(PartnerBase):
    """Schema for creating a partner."""
    pass


class PartnerUpdate(BaseModel):
    """Schema for updating a partner."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    partner_type: Optional[PartnerType] = None
    organization_type: Optional[OrganizationType] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class PartnerResponse(PartnerBase):
    """Schema for partner response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime


class DonationSummary(BaseModel):
    """Summary of a donation for partner detail view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_date: str
    notes: Optional[str] = None
    item_count: int = 0


class PartnerDetailResponse(PartnerResponse):
    """Schema for partner response with donations and treatments info."""

    donations: List[DonationSummary] = []
