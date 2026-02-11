from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey

from app.model.base import BaseModel


class Equipment(BaseModel):
    """Model for equipment inventory items."""

    __tablename__ = "equipment"

    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    condition = Column(String, nullable=True)  # new, good, fair, poor
    is_active = Column(Boolean, default=True, nullable=False)
