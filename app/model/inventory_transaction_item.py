from sqlalchemy import Column, Integer, ForeignKey

from app.model.base import BaseModel


class InventoryTransactionItem(BaseModel):
    """Model for inventory transaction line items."""

    __tablename__ = "inventory_transaction_items"

    transaction_id = Column(Integer, ForeignKey("inventory_transactions.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
