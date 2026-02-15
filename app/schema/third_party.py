from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ThirdPartyType(StrEnum):
    USER = "user"
    DOCTOR = "doctor"
    PATIENT = "patient"
    PARTNER = "partner"


class ThirdPartyResponse(BaseModel):
    """Schema for third party response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
