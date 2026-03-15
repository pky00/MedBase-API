from datetime import datetime, date
from enum import StrEnum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class TransactionType(StrEnum):
    PURCHASE = "purchase"
    DONATION = "donation"
    PRESCRIPTION = "prescription"
    LOSS = "loss"
    BREAKAGE = "breakage"
    EXPIRATION = "expiration"
    DESTRUCTION = "destruction"


# --- Transaction Item Schemas ---

class TransactionItemCreate(BaseModel):
    """Schema for creating a transaction item."""

    item_id: int
    quantity: int = Field(..., gt=0)


class TransactionItemUpdate(BaseModel):
    """Schema for updating a transaction item."""

    item_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0)


class TransactionItemResponse(BaseModel):
    """Schema for transaction item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: int
    item_id: int
    quantity: int
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    item_name: Optional[str] = None
    item_type: Optional[str] = None


# --- Transaction Schemas ---

class InventoryTransactionCreate(BaseModel):
    """Schema for creating an inventory transaction."""

    transaction_type: TransactionType
    third_party_id: Optional[int] = None
    appointment_id: Optional[int] = None
    transaction_date: date
    notes: Optional[str] = None
    items: Optional[List[TransactionItemCreate]] = None


class InventoryTransactionUpdate(BaseModel):
    """Schema for updating an inventory transaction."""

    transaction_date: Optional[date] = None
    notes: Optional[str] = None


class InventoryTransactionResponse(BaseModel):
    """Schema for inventory transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    third_party_id: int
    appointment_id: Optional[int] = None
    transaction_date: date
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    third_party_name: Optional[str] = None
    items: Optional[List[TransactionItemResponse]] = None


class TransactionByItemResponse(BaseModel):
    """Schema for transaction response when querying by item ID."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    third_party_id: int
    appointment_id: Optional[int] = None
    transaction_date: date
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    third_party_name: Optional[str] = None
    transaction_item_id: int
    transaction_item_quantity: int

    @classmethod
    def from_row(cls, row) -> "TransactionByItemResponse":
        """Build from a SQLAlchemy row of (InventoryTransaction, third_party_name, transaction_item_id, transaction_item_quantity)."""
        transaction = row[0]
        return cls.model_validate(
            {
                "id": transaction.id,
                "transaction_type": transaction.transaction_type,
                "third_party_id": transaction.third_party_id,
                "appointment_id": transaction.appointment_id,
                "transaction_date": transaction.transaction_date,
                "notes": transaction.notes,
                "is_deleted": transaction.is_deleted,
                "created_by": transaction.created_by,
                "created_at": transaction.created_at,
                "updated_by": transaction.updated_by,
                "updated_at": transaction.updated_at,
                "third_party_name": row[1],
                "transaction_item_id": row[2],
                "transaction_item_quantity": row[3],
            }
        )


class InventoryTransactionListResponse(BaseModel):
    """Schema for inventory transaction in list view (without items)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    third_party_id: int
    appointment_id: Optional[int] = None
    transaction_date: date
    notes: Optional[str] = None
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    third_party_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "InventoryTransactionListResponse":
        """Build from a SQLAlchemy row of (InventoryTransaction, third_party_name)."""
        transaction = row[0]
        return cls.model_validate(
            {
                "id": transaction.id,
                "transaction_type": transaction.transaction_type,
                "third_party_id": transaction.third_party_id,
                "appointment_id": transaction.appointment_id,
                "transaction_date": transaction.transaction_date,
                "notes": transaction.notes,
                "is_deleted": transaction.is_deleted,
                "created_by": transaction.created_by,
                "created_at": transaction.created_at,
                "updated_by": transaction.updated_by,
                "updated_at": transaction.updated_at,
                "third_party_name": row[1],
            }
        )
