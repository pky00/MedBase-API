import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.statistics import StatisticsService
from app.schema.statistics import (
    SummaryStats,
    InventoryStats,
    AppointmentStats,
    TransactionStats,
)
from app.model.user import User

logger = logging.getLogger("medbase.router.statistics")

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/summary", response_model=SummaryStats)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary statistics for the dashboard.

    Returns total counts for: patients, appointments, inventory items, transactions,
    partners, doctors, plus active counts for patients, partners, and doctors.
    """
    logger.info("Fetching dashboard summary by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_summary()


@router.get("/inventory", response_model=InventoryStats)
async def get_inventory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get inventory statistics.

    Returns total items count, total quantity across all items, low stock alerts
    (items with quantity below threshold), and item counts grouped by type
    (medicine, equipment, medical device).
    """
    logger.info("Fetching inventory stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_inventory_stats()


@router.get("/appointments", response_model=AppointmentStats)
async def get_appointment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get appointment statistics.

    Returns: today's appointment count, upcoming appointments count, appointments
    grouped by status, appointments grouped by month, and total completed/cancelled counts.
    """
    logger.info("Fetching appointment stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_appointment_stats()


@router.get("/transactions", response_model=TransactionStats)
async def get_transaction_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get inventory transaction statistics.

    Returns: total transaction count, transactions grouped by type with item totals,
    and a list of recent transactions with third party names and item counts.
    """
    logger.info("Fetching transaction stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_transaction_stats()
