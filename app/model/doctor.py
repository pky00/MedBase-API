from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.model.base import BaseModel


class Doctor(BaseModel):
    """Model for doctor records."""

    __tablename__ = "doctors"

    third_party_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
    third_party = relationship("ThirdParty", lazy="noload")
    specialization = Column(String, nullable=True)
    type = Column(String, nullable=False)  # internal, external, partner_provided
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
