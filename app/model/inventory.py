from sqlalchemy import Column, String, Integer

from app.model.base import BaseModel


class Inventory(BaseModel):
    """Model for inventory records.
    
    Tracks quantity of medicines, equipment, and medical devices.
    item_type: 'medicine', 'equipment', 'medical_device'
    """

    __tablename__ = "inventory"

    item_type = Column(String, nullable=False)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
