from sqlalchemy import Column, String, Text

from app.model.base import BaseModel


class EquipmentCategory(BaseModel):
    """Model for equipment categories."""

    __tablename__ = "equipment_categories"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
