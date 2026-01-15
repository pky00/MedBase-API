from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import Severity


class PatientMedicalHistory(Base):
    __tablename__ = "patient_medical_history"
    
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
    condition_name: Mapped[str] = mapped_column(String(200), nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    diagnosis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolution_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    severity: Mapped[Severity | None] = mapped_column(
        SQLEnum(Severity, name="severity", create_type=False),
        nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_history", lazy="selectin")

