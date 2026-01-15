from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import InventoryTransactionType, ReferenceType


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    medicine_inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medicine_inventory.id", ondelete="CASCADE"),
        nullable=True
    )
    medical_device_inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medical_device_inventory.id", ondelete="CASCADE"),
        nullable=True
    )
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=True
    )
    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        SQLEnum(InventoryTransactionType, name="inventory_transaction_type", create_type=False),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[ReferenceType | None] = mapped_column(
        SQLEnum(ReferenceType, name="reference_type", create_type=False),
        nullable=True
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    medicine_inventory = relationship("MedicineInventory", foreign_keys=[medicine_inventory_id])
    medical_device_inventory = relationship("MedicalDeviceInventory", foreign_keys=[medical_device_inventory_id])
    equipment = relationship("Equipment", foreign_keys=[equipment_id])

