from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, Integer, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import PrescriptionStatus


class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    prescription_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
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
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True
    )
    medical_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_records.id", ondelete="SET NULL"),
        nullable=True
    )
    prescription_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pharmacy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PrescriptionStatus] = mapped_column(
        SQLEnum(PrescriptionStatus, name="prescription_status", create_type=False),
        default=PrescriptionStatus.pending,
        nullable=False
    )
    dispensed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_refillable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refills_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="selectin")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="selectin")
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

