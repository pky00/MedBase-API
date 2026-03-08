from sqlalchemy import Column, String, Integer, Date, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.model.base import BaseModel


class Patient(BaseModel):
    """Model for patient records."""

    __tablename__ = "patients"

    third_party_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
    third_party = relationship("ThirdParty", lazy="noload")
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
