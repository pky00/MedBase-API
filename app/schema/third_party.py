from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


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
