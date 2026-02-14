from sqlalchemy import Column, String, Text

from app.model.base import BaseModel


class MedicineCategory(BaseModel):
    """Model for medicine categories."""

    __tablename__ = "medicine_categories"

    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
