from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Integer, Numeric, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import EquipmentCondition


class DonationEquipmentItem(Base):
    __tablename__ = "donation_equipment_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False
    )
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="SET NULL"),
        nullable=True
    )
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    equipment_condition: Mapped[EquipmentCondition] = mapped_column(
        SQLEnum(EquipmentCondition, name="equipment_condition", create_type=False),
        default=EquipmentCondition.good,
        nullable=False
    )
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    donation = relationship("Donation", back_populates="equipment_items")
    equipment = relationship("Equipment", foreign_keys=[equipment_id])

