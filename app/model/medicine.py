from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey

from app.model.base import BaseModel


class Medicine(BaseModel):
    """Model for medicine inventory items."""

    __tablename__ = "medicines"

    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("medicine_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    unit = Column(String, nullable=True)  # tablets, ml, mg, etc.
    is_active = Column(Boolean, default=True, nullable=False)
