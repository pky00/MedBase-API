from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func

from app.model.base import BaseModel


class InventoryTransaction(BaseModel):
    """Model for inventory transactions.

    Tracks all inventory movements: purchases, donations, prescriptions,
    losses, breakage, expiration, destruction.
    This is the only way to modify inventory quantities.
    """

    __tablename__ = "inventory_transactions"

    transaction_type = Column(String, nullable=False)  # purchase, donation, prescription, loss, breakage, expiration, destruction
    item_type = Column(String, nullable=False)  # medicine, equipment, medical_device
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    transaction_date = Column(DateTime, server_default=func.now(), nullable=False)
