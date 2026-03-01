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
    """Get summary statistics for the dashboard."""
    logger.info("Fetching dashboard summary by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_summary()


@router.get("/inventory", response_model=InventoryStats)
async def get_inventory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inventory statistics (low stock alerts, items by type)."""
    logger.info("Fetching inventory stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_inventory_stats()


@router.get("/appointments", response_model=AppointmentStats)
async def get_appointment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get appointment statistics (today, upcoming, by status, by month)."""
    logger.info("Fetching appointment stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_appointment_stats()


@router.get("/transactions", response_model=TransactionStats)
async def get_transaction_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transaction statistics (by type, recent transactions)."""
    logger.info("Fetching transaction stats by user_id=%d", current_user.id)
    service = StatisticsService(db)
    return await service.get_transaction_stats()
