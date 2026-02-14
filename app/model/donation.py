from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey

from app.model.base import BaseModel


class Donation(BaseModel):
    """Model for donation records."""

    __tablename__ = "donations"

    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    donation_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)


class DonationItem(BaseModel):
    """Model for donation items."""

    __tablename__ = "donation_items"

    donation_id = Column(Integer, ForeignKey("donations.id"), nullable=False)
    item_type = Column(String, nullable=False)  # medicine, equipment, medical_device
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
