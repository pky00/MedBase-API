from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey

from app.model.base import BaseModel


class Appointment(BaseModel):
    """Model for appointment records."""

    __tablename__ = "appointments"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    type = Column(String, nullable=False)
    location = Column(String, nullable=False, default="internal")
    notes = Column(Text, nullable=True)
