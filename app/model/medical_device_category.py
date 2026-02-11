from sqlalchemy import Column, String, Text

from app.model.base import BaseModel


class MedicalDeviceCategory(BaseModel):
    """Model for medical device categories."""

    __tablename__ = "medical_device_categories"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
