from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey

from app.model.base import BaseModel


class MedicalDevice(BaseModel):
    """Model for medical device inventory items."""

    __tablename__ = "medical_devices"

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, unique=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("medical_device_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    serial_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
