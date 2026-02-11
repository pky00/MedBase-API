from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class InventoryResponse(BaseModel):
    """Schema for inventory response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: str
    item_id: int
    quantity: int
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
