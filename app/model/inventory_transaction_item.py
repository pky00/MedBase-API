from sqlalchemy import Column, String, Integer, ForeignKey

from app.model.base import BaseModel


class InventoryTransactionItem(BaseModel):
    """Model for inventory transaction line items."""

    __tablename__ = "inventory_transaction_items"

    transaction_id = Column(Integer, ForeignKey("inventory_transactions.id"), nullable=False)
    item_type = Column(String, nullable=False)  # medicine, equipment, medical_device
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
