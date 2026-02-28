from sqlalchemy import Column, String, Integer, Date, Numeric, Text, ForeignKey

from app.model.base import BaseModel


class Treatment(BaseModel):
    """Model for treatment records."""

    __tablename__ = "treatments"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    treatment_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    treatment_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="pending")
    cost = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
