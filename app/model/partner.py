from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey

from app.model.base import BaseModel


class Partner(BaseModel):
    """Model for partner records (donors, referral partners, or both)."""

    __tablename__ = "partners"

    third_party_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    partner_type = Column(String, nullable=False)  # donor, referral, both
    organization_type = Column(String, nullable=True)  # NGO, organization, individual, hospital, medical_center
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
