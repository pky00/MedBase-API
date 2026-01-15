from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import GenderType, BloodType, MaritalStatus


class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    patient_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[GenderType] = mapped_column(
        SQLEnum(GenderType, name="gender_type", create_type=False),
        nullable=False
    )
    blood_type: Mapped[BloodType | None] = mapped_column(
        SQLEnum(BloodType, name="blood_type", create_type=False),
        default=BloodType.unknown,
        nullable=True
    )
    national_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alternative_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), default="Unknown", nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    marital_status: Mapped[MaritalStatus | None] = mapped_column(
        SQLEnum(MaritalStatus, name="marital_status", create_type=False),
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
    allergies = relationship("PatientAllergy", back_populates="patient", cascade="all, delete-orphan")
    medical_history = relationship("PatientMedicalHistory", back_populates="patient", cascade="all, delete-orphan")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

