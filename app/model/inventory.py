from sqlalchemy import Column, Integer, ForeignKey

from app.model.base import BaseModel


class Inventory(BaseModel):
    """Model for inventory records.

    Tracks quantity of items (medicines, equipment, medical devices).
    Each inventory record is linked to an item via item_id.
    """

    __tablename__ = "inventory"

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False, default=0)
