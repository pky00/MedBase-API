from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, DateTime, Boolean, Numeric, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base
from app.models.enums import DosageForm


class Medicine(Base):
    __tablename__ = "medicines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medicine_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dosage_form: Mapped[DosageForm] = mapped_column(
        SQLEnum(DosageForm, name="dosage_form", create_type=False),
        nullable=False
    )
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    package_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    indications: Mapped[str | None] = mapped_column(Text, nullable=True)
    contraindications: Mapped[str | None] = mapped_column(Text, nullable=True)
    side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_prescription: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_controlled_substance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    category = relationship("MedicineCategory", back_populates="medicines")
    inventory = relationship("MedicineInventory", back_populates="medicine", uselist=False)
    expiry_records = relationship("MedicineExpiry", back_populates="medicine")

