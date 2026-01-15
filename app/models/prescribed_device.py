from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import EquipmentCondition


class PrescribedDevice(Base):
    __tablename__ = "prescribed_devices"
    
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
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_devices.id", ondelete="CASCADE"),
        nullable=False
    )
    prescription_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    condition_on_issue: Mapped[EquipmentCondition | None] = mapped_column(
        SQLEnum(EquipmentCondition, name="equipment_condition", create_type=False),
        nullable=True
    )
    condition_on_return: Mapped[EquipmentCondition | None] = mapped_column(
        SQLEnum(EquipmentCondition, name="equipment_condition", create_type=False),
        nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="selectin")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="selectin")
    device = relationship("MedicalDevice", foreign_keys=[device_id], lazy="selectin")

