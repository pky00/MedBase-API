from enum import Enum


class ItemType(str, Enum):
    """Inventory item types."""

    MEDICINE = "medicine"
    EQUIPMENT = "equipment"
    MEDICAL_DEVICE = "medical_device"


class EquipmentCondition(str, Enum):
    """Equipment condition values."""

    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class UserRole(str, Enum):
    """User role values."""

    ADMIN = "admin"
    USER = "user"
