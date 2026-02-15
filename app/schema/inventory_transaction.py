from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schema.inventory import ItemType


class TransactionType(StrEnum):
    PURCHASE = "purchase"
    DONATION = "donation"
    PRESCRIPTION = "prescription"
    LOSS = "loss"
    BREAKAGE = "breakage"
    EXPIRATION = "expiration"
    DESTRUCTION = "destruction"


# Transaction types that increase inventory
INCREASE_TYPES = {TransactionType.PURCHASE, TransactionType.DONATION}
# Transaction types that decrease inventory
DECREASE_TYPES = {
    TransactionType.PRESCRIPTION,
    TransactionType.LOSS,
    TransactionType.BREAKAGE,
    TransactionType.EXPIRATION,
    TransactionType.DESTRUCTION,
}


class InventoryTransactionCreate(BaseModel):
    """Schema for creating an inventory transaction."""

    transaction_type: TransactionType
    item_type: ItemType
    item_id: int
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


class InventoryTransactionResponse(BaseModel):
    """Schema for inventory transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: TransactionType
    item_type: ItemType
    item_id: int
    quantity: int
    notes: Optional[str] = None
    transaction_date: datetime
    is_deleted: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime
