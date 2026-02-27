from sqlalchemy import Column, Integer, Numeric, Text, ForeignKey

from app.model.base import BaseModel


class VitalSign(BaseModel):
    """Model for vital signs records."""

    __tablename__ = "vital_signs"

    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature = Column(Numeric(5, 2), nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    weight = Column(Numeric(6, 2), nullable=True)
    height = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
