from sqlalchemy import Column, Integer, Date, Text, ForeignKey

from app.model.base import BaseModel


class MedicalRecord(BaseModel):
    """Model for medical records."""

    __tablename__ = "medical_records"

    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    chief_complaint = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    treatment_notes = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
