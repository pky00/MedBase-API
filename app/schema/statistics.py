from typing import Optional, List
from pydantic import BaseModel


# --- Summary Stats ---

class SummaryStats(BaseModel):
    """Overall summary statistics for the dashboard."""

    total_patients: int
    total_appointments: int
    total_inventory_items: int
    total_transactions: int
    total_partners: int
    total_doctors: int
    active_patients: int
    active_partners: int
    active_doctors: int


# --- Inventory Stats ---

class LowStockItem(BaseModel):
    """An inventory item with low stock."""

    item_type: str
    item_id: int
    item_name: str
    quantity: int


class InventoryByType(BaseModel):
    """Inventory count grouped by item type."""

    item_type: str
    count: int
    total_quantity: int


class InventoryStats(BaseModel):
    """Inventory statistics for the dashboard."""

    total_items: int
    total_quantity: int
    low_stock_items: List[LowStockItem]
    items_by_type: List[InventoryByType]


# --- Appointment Stats ---

class AppointmentsByStatus(BaseModel):
    """Appointment count grouped by status."""

    status: str
    count: int


class AppointmentsByMonth(BaseModel):
    """Appointment count grouped by month."""

    month: str  # e.g. "2026-03"
    count: int


class AppointmentStats(BaseModel):
    """Appointment statistics for the dashboard."""

    today_count: int
    upcoming_count: int
    by_status: List[AppointmentsByStatus]
    by_month: List[AppointmentsByMonth]
    total_completed: int
    total_cancelled: int


# --- Transaction Stats ---

class TransactionsByType(BaseModel):
    """Transaction counts grouped by type."""

    transaction_type: str
    count: int
    total_items: int


class RecentTransaction(BaseModel):
    """A recent transaction summary."""

    id: int
    transaction_type: str
    transaction_date: str
    third_party_name: Optional[str] = None
    item_count: int


class TransactionStats(BaseModel):
    """Transaction statistics for the dashboard."""

    total_transactions: int
    by_type: List[TransactionsByType]
    recent_transactions: List[RecentTransaction]
