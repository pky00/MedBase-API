from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey

from app.model.base import BaseModel


class Equipment(BaseModel):
    """Model for equipment inventory items."""

    __tablename__ = "equipment"

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, unique=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    condition = Column(String, nullable=True)  # new, good, fair, poor
    is_active = Column(Boolean, default=True, nullable=False)
