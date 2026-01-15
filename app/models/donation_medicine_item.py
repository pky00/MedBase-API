from __future__ import annotations
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Date, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class DonationMedicineItem(Base):
    __tablename__ = "donation_medicine_items"
    
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
    medicine_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medicines.id", ondelete="SET NULL"),
        nullable=True
    )
    medicine_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_unit_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    donation = relationship("Donation", back_populates="medicine_items")
    medicine = relationship("Medicine", foreign_keys=[medicine_id])

