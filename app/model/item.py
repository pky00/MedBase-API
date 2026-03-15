from enum import StrEnum

from sqlalchemy import Column, String

from app.model.base import BaseModel


class ItemType(StrEnum):
    MEDICINE = "medicine"
    EQUIPMENT = "equipment"
    MEDICAL_DEVICE = "medical_device"


class Item(BaseModel):
    """Parent model that uniquely identifies each inventory item (medicine, equipment, or medical device)."""

    __tablename__ = "items"

    item_type = Column(String, nullable=False)
    name = Column(String, unique=True, nullable=False)
