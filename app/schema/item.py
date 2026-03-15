from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemType(StrEnum):
    """Item types."""

    MEDICINE = "medicine"
    EQUIPMENT = "equipment"
    MEDICAL_DEVICE = "medical_device"


class ItemResponse(BaseModel):
    """Schema for item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: str
    name: str
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
