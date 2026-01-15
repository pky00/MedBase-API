from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Integer, Numeric, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class VitalSign(Base):
    __tablename__ = "vital_signs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    temperature_celsius: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pulse_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oxygen_saturation: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    blood_glucose: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    __table_args__ = (
        CheckConstraint('pain_level >= 0 AND pain_level <= 10', name='check_pain_level'),
    )
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="selectin")
    appointment = relationship("Appointment", back_populates="vital_signs")

