import secrets

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey

from app.model.base import BaseModel

# Unambiguous characters: no 0/O, 1/I/L
_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_code() -> str:
    """Generate a unique 6-character human-readable code for appointments."""
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(6))


class Appointment(BaseModel):
    """Model for appointment records."""

    __tablename__ = "appointments"

    code = Column(String, unique=True, nullable=False, default=generate_code)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    type = Column(String, nullable=False)
    location = Column(String, nullable=False, default="internal")
    notes = Column(Text, nullable=True)
