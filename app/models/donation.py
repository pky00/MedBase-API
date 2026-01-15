from __future__ import annotations
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Date, Integer, Numeric, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import DonationType


class Donation(Base):
    __tablename__ = "donations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    donation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False
    )
    donation_type: Mapped[DonationType] = mapped_column(
        SQLEnum(DonationType, name="donation_type", create_type=False),
        nullable=False
    )
    donation_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_items_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    donor = relationship("Donor", back_populates="donations")
    medicine_items = relationship("DonationMedicineItem", back_populates="donation", cascade="all, delete-orphan")
    equipment_items = relationship("DonationEquipmentItem", back_populates="donation", cascade="all, delete-orphan")
    medical_device_items = relationship("DonationMedicalDeviceItem", back_populates="donation", cascade="all, delete-orphan")

