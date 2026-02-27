from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ItemType(str, Enum):
    """Inventory item types."""

    MEDICINE = "medicine"
    EQUIPMENT = "equipment"
    MEDICAL_DEVICE = "medical_device"


class InventoryResponse(BaseModel):
    """Schema for inventory response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: ItemType
    item_id: int
    quantity: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
