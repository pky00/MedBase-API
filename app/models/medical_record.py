from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, func, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    record_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
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
    visit_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_of_present_illness: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_examination: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    icd_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String(20)), nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedures_performed: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="selectin")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="selectin")
    appointment = relationship("Appointment", back_populates="medical_records")
    prescriptions = relationship("Prescription", back_populates="medical_record")
    documents = relationship("PatientDocument", back_populates="medical_record")

