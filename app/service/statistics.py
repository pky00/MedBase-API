import logging
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal_column

from app.model.patient import Patient
from app.model.appointment import Appointment
from app.model.inventory import Inventory
from app.model.inventory_transaction import InventoryTransaction
from app.model.inventory_transaction_item import InventoryTransactionItem
from app.model.partner import Partner
from app.model.doctor import Doctor
from app.model.item import Item
from app.model.third_party import ThirdParty
from app.schema.statistics import (
    SummaryStats,
    InventoryStats,
    LowStockItem,
    InventoryByType,
    AppointmentStats,
    AppointmentsByStatus,
    AppointmentsByMonth,
    TransactionStats,
    TransactionsByType,
    RecentTransaction,
)

logger = logging.getLogger("medbase.service.statistics")

LOW_STOCK_THRESHOLD = 10


class StatisticsService:
    """Service layer for dashboard statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> SummaryStats:
        """Get overall summary statistics."""
        total_patients = await self._count(Patient)
        active_patients = await self._count(Patient, Patient.is_active == True)
        total_appointments = await self._count(Appointment)
        total_inventory = await self._count(Inventory)
        total_transactions = await self._count(InventoryTransaction)
        total_partners = await self._count(Partner)
        active_partners = await self._count(Partner, Partner.is_active == True)
        total_doctors = await self._count(Doctor)
        active_doctors = await self._count(Doctor, Doctor.is_active == True)

        return SummaryStats(
            total_patients=total_patients,
            total_appointments=total_appointments,
            total_inventory_items=total_inventory,
            total_transactions=total_transactions,
            total_partners=total_partners,
            total_doctors=total_doctors,
            active_patients=active_patients,
            active_partners=active_partners,
            active_doctors=active_doctors,
        )

    async def get_inventory_stats(self) -> InventoryStats:
        """Get inventory statistics."""
        # Total items and total quantity
        result = await self.db.execute(
            select(
                func.count(Inventory.id),
                func.coalesce(func.sum(Inventory.quantity), 0),
            ).where(Inventory.is_deleted == False)
        )
        row = result.one()
        total_items = row[0]
        total_quantity = row[1]

        # Items by type (join with Item to get item_type)
        result = await self.db.execute(
            select(
                Item.item_type,
                func.count(Inventory.id),
                func.coalesce(func.sum(Inventory.quantity), 0),
            )
            .join(Item, Inventory.item_id == Item.id)
            .where(Inventory.is_deleted == False)
            .group_by(Item.item_type)
        )
        items_by_type = [
            InventoryByType(item_type=r[0], count=r[1], total_quantity=r[2])
            for r in result.all()
        ]

        # Low stock items
        low_stock_query = (
            select(Inventory, Item.name, Item.item_type)
            .join(Item, Inventory.item_id == Item.id)
            .where(
                Inventory.is_deleted == False,
                Inventory.quantity <= LOW_STOCK_THRESHOLD,
            )
            .order_by(Inventory.quantity.asc())
            .limit(20)
        )
        result = await self.db.execute(low_stock_query)
        low_stock_rows = result.all()

        low_stock_items = []
        for row in low_stock_rows:
            inv = row[0]
            low_stock_items.append(
                LowStockItem(
                    item_type=row[2],
                    item_id=inv.item_id,
                    item_name=row[1] or "Unknown",
                    quantity=inv.quantity,
                )
            )

        return InventoryStats(
            total_items=total_items,
            total_quantity=total_quantity,
            low_stock_items=low_stock_items,
            items_by_type=items_by_type,
        )

    async def get_appointment_stats(self) -> AppointmentStats:
        """Get appointment statistics."""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # Today's appointments
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.is_deleted == False,
                Appointment.appointment_date >= today_start,
                Appointment.appointment_date <= today_end,
            )
        )
        today_count = result.scalar()

        # Upcoming appointments (future, excluding today, not cancelled)
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.is_deleted == False,
                Appointment.appointment_date > today_end,
                Appointment.status != "cancelled",
            )
        )
        upcoming_count = result.scalar()

        # By status
        result = await self.db.execute(
            select(
                Appointment.status,
                func.count(Appointment.id),
            )
            .where(Appointment.is_deleted == False)
            .group_by(Appointment.status)
        )
        by_status = [
            AppointmentsByStatus(status=r[0], count=r[1])
            for r in result.all()
        ]

        # By month (last 6 months)
        six_months_ago = today - timedelta(days=180)
        month_expr = func.to_char(Appointment.appointment_date, literal_column("'YYYY-MM'"))
        result = await self.db.execute(
            select(
                month_expr.label("month"),
                func.count(Appointment.id),
            )
            .where(
                Appointment.is_deleted == False,
                Appointment.appointment_date >= six_months_ago,
            )
            .group_by(month_expr)
            .order_by(month_expr)
        )
        by_month = [
            AppointmentsByMonth(month=r[0], count=r[1])
            for r in result.all()
        ]

        # Totals for completed and cancelled
        total_completed = 0
        total_cancelled = 0
        for s in by_status:
            if s.status == "completed":
                total_completed = s.count
            elif s.status == "cancelled":
                total_cancelled = s.count

        return AppointmentStats(
            today_count=today_count,
            upcoming_count=upcoming_count,
            by_status=by_status,
            by_month=by_month,
            total_completed=total_completed,
            total_cancelled=total_cancelled,
        )

    async def get_transaction_stats(self) -> TransactionStats:
        """Get transaction statistics."""
        # Total transactions
        total = await self._count(InventoryTransaction)

        # By type with item counts
        result = await self.db.execute(
            select(
                InventoryTransaction.transaction_type,
                func.count(InventoryTransaction.id),
                func.coalesce(
                    func.sum(
                        select(func.count(InventoryTransactionItem.id))
                        .where(
                            InventoryTransactionItem.transaction_id == InventoryTransaction.id,
                            InventoryTransactionItem.is_deleted == False,
                        )
                        .correlate(InventoryTransaction)
                        .scalar_subquery()
                    ),
                    0,
                ),
            )
            .where(InventoryTransaction.is_deleted == False)
            .group_by(InventoryTransaction.transaction_type)
        )
        by_type = [
            TransactionsByType(transaction_type=r[0], count=r[1], total_items=r[2])
            for r in result.all()
        ]

        # Recent transactions (last 10)
        result = await self.db.execute(
            select(
                InventoryTransaction,
                ThirdParty.name.label("third_party_name"),
            )
            .outerjoin(ThirdParty, InventoryTransaction.third_party_id == ThirdParty.id)
            .where(InventoryTransaction.is_deleted == False)
            .order_by(InventoryTransaction.created_at.desc())
            .limit(10)
        )
        recent_rows = result.all()

        recent_transactions = []
        for row in recent_rows:
            txn = row[0]
            tp_name = row[1]
            # Count items for this transaction
            item_count_result = await self.db.execute(
                select(func.count(InventoryTransactionItem.id)).where(
                    InventoryTransactionItem.transaction_id == txn.id,
                    InventoryTransactionItem.is_deleted == False,
                )
            )
            item_count = item_count_result.scalar()

            recent_transactions.append(
                RecentTransaction(
                    id=txn.id,
                    transaction_type=txn.transaction_type,
                    transaction_date=str(txn.transaction_date),
                    third_party_name=tp_name,
                    item_count=item_count,
                )
            )

        return TransactionStats(
            total_transactions=total,
            by_type=by_type,
            recent_transactions=recent_transactions,
        )

    # --- Helpers ---

    async def _count(self, model, *extra_filters):
        """Count non-deleted records for a model."""
        query = select(func.count(model.id)).where(model.is_deleted == False)
        for f in extra_filters:
            query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar()
