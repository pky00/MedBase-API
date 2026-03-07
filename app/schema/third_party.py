from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ThirdPartyUpdate(BaseModel):
    """Schema for updating a third party record."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class ThirdPartyResponse(BaseModel):
    """Schema for third party response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
