from __future__ import annotations
import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Text, DateTime, Date, Time, Integer, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import AppointmentStatus, AppointmentType


class Appointment(Base):
    __tablename__ = "appointments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    appointment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    appointment_type: Mapped[AppointmentType] = mapped_column(
        SQLEnum(AppointmentType, name="appointment_type", create_type=False),
        default=AppointmentType.consultation,
        nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus, name="appointment_status", create_type=False),
        default=AppointmentStatus.scheduled,
        nullable=False
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    previous_appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id"),
        nullable=True
    )
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="selectin")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="selectin")
    previous_appointment = relationship("Appointment", remote_side=[id])
    vital_signs = relationship("VitalSign", back_populates="appointment")
    medical_records = relationship("MedicalRecord", back_populates="appointment")

