from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import EquipmentCondition


class MedicalDeviceInventory(Base):
    __tablename__ = "medical_device_inventory"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_devices.id", ondelete="CASCADE"),
        nullable=False
    )
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition: Mapped[EquipmentCondition] = mapped_column(
        SQLEnum(EquipmentCondition, name="equipment_condition", create_type=False),
        default=EquipmentCondition.good,
        nullable=False
    )
    is_donation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    donor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    device = relationship("MedicalDevice", back_populates="inventory")
    donor = relationship("Donor", foreign_keys=[donor_id])

