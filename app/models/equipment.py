from __future__ import annotations
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Date, Boolean, Numeric, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import EquipmentCondition


class Equipment(Base):
    __tablename__ = "equipment"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    asset_code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_donation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    donor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True
    )
    donation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donations.id", ondelete="SET NULL"),
        nullable=True
    )
    equipment_condition: Mapped[EquipmentCondition] = mapped_column(
        SQLEnum(EquipmentCondition, name="equipment_condition", create_type=False),
        default=EquipmentCondition.good,
        nullable=False
    )
    is_portable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    category = relationship("EquipmentCategory", back_populates="equipment")
    donor = relationship("Donor", foreign_keys=[donor_id])
    donation = relationship("Donation", foreign_keys=[donation_id])

