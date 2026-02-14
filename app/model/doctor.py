from sqlalchemy import Column, String, Integer, Boolean, ForeignKey

from app.model.base import BaseModel


class Doctor(BaseModel):
    """Model for doctor records."""

    __tablename__ = "doctors"

    name = Column(String, unique=True, nullable=False)
    specialization = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    type = Column(String, nullable=False)  # internal, external, partner_provided
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
