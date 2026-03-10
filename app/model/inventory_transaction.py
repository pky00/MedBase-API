from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey

from app.model.base import BaseModel


class InventoryTransaction(BaseModel):
    """Model for inventory transactions (purchase, donation, prescription, loss, etc.)."""

    __tablename__ = "inventory_transactions"

    transaction_type = Column(String, nullable=False)
    third_party_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    transaction_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
