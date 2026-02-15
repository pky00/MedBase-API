import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.inventory_transaction import InventoryTransaction
from app.model.inventory import Inventory
from app.model.medicine import Medicine
from app.model.equipment import Equipment
from app.model.medical_device import MedicalDevice
from app.schema.inventory_transaction import (
    InventoryTransactionCreate,
    TransactionType,
    INCREASE_TYPES,
    DECREASE_TYPES,
)
from app.schema.inventory import ItemType

logger = logging.getLogger("medbase.service.inventory_transaction")


class InventoryTransactionService:
    """Service layer for inventory transaction operations.

    Inventory transactions are the only way to modify inventory quantities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, transaction_id: int) -> Optional[InventoryTransaction]:
        """Get transaction by ID."""
        result = await self.db.execute(
            select(InventoryTransaction).where(
                InventoryTransaction.id == transaction_id,
                InventoryTransaction.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        transaction_type: Optional[str] = None,
        item_type: Optional[str] = None,
        item_id: Optional[int] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[InventoryTransaction], int]:
        """Get all transactions with pagination and filtering."""
        query = select(InventoryTransaction).where(
            InventoryTransaction.is_deleted == False
        )

        # Apply filters
        if transaction_type is not None:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)
        if item_type is not None:
            query = query.where(InventoryTransaction.item_type == item_type)
        if item_id is not None:
            query = query.where(InventoryTransaction.item_id == item_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(InventoryTransaction, sort, InventoryTransaction.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        transactions = result.scalars().all()

        logger.debug("Queried inventory transactions: total=%d returned=%d", total, len(transactions))

        return list(transactions), total

    async def create(
        self,
        data: InventoryTransactionCreate,
        created_by: Optional[int] = None,
    ) -> InventoryTransaction:
        """Create a transaction and update inventory quantity.

        + for purchase/donation, - for others.
        """
        transaction = InventoryTransaction(
            transaction_type=data.transaction_type,
            item_type=data.item_type,
            item_id=data.item_id,
            quantity=data.quantity,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        if data.transaction_date:
            transaction.transaction_date = data.transaction_date

        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        # Update inventory quantity
        await self._apply_inventory_change(
            item_type=data.item_type,
            item_id=data.item_id,
            quantity=data.quantity,
            transaction_type=data.transaction_type,
            updated_by=created_by,
        )

        logger.info(
            "Created inventory transaction id=%d type='%s' item_type='%s' item_id=%d qty=%d",
            transaction.id, data.transaction_type, data.item_type, data.item_id, data.quantity,
        )
        return transaction

    async def delete(self, transaction_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a transaction and reverse the inventory change."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False

        # Reverse the inventory change
        await self._reverse_inventory_change(
            item_type=transaction.item_type,
            item_id=transaction.item_id,
            quantity=transaction.quantity,
            transaction_type=transaction.transaction_type,
            updated_by=deleted_by,
        )

        transaction.is_deleted = True
        transaction.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted inventory transaction id=%d", transaction_id)
        return True

    async def _apply_inventory_change(
        self,
        item_type: str,
        item_id: int,
        quantity: int,
        transaction_type: str,
        updated_by: Optional[int] = None,
    ):
        """Apply inventory change based on transaction type.

        + for purchase/donation, - for others.
        """
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_type == item_type,
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        inventory = result.scalar_one_or_none()
        if not inventory:
            return

        if transaction_type in INCREASE_TYPES:
            inventory.quantity += quantity
        else:
            inventory.quantity = max(0, inventory.quantity - quantity)

        inventory.updated_by = updated_by
        await self.db.flush()
        logger.debug(
            "Applied inventory change: item_type='%s' item_id=%d type='%s' qty=%d new_qty=%d",
            item_type, item_id, transaction_type, quantity, inventory.quantity,
        )

    async def _reverse_inventory_change(
        self,
        item_type: str,
        item_id: int,
        quantity: int,
        transaction_type: str,
        updated_by: Optional[int] = None,
    ):
        """Reverse an inventory change (for transaction deletion)."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_type == item_type,
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        inventory = result.scalar_one_or_none()
        if not inventory:
            return

        # Reverse: if it was an increase, decrease; if decrease, increase
        if transaction_type in INCREASE_TYPES:
            inventory.quantity = max(0, inventory.quantity - quantity)
        else:
            inventory.quantity += quantity

        inventory.updated_by = updated_by
        await self.db.flush()
        logger.debug(
            "Reversed inventory change: item_type='%s' item_id=%d type='%s' qty=%d new_qty=%d",
            item_type, item_id, transaction_type, quantity, inventory.quantity,
        )

    async def validate_item_exists(self, item_type: str, item_id: int) -> bool:
        """Validate that the referenced inventory item exists."""
        if item_type == ItemType.MEDICINE:
            result = await self.db.execute(
                select(Medicine.id).where(Medicine.id == item_id, Medicine.is_deleted == False)
            )
        elif item_type == ItemType.EQUIPMENT:
            result = await self.db.execute(
                select(Equipment.id).where(Equipment.id == item_id, Equipment.is_deleted == False)
            )
        elif item_type == ItemType.MEDICAL_DEVICE:
            result = await self.db.execute(
                select(MedicalDevice.id).where(MedicalDevice.id == item_id, MedicalDevice.is_deleted == False)
            )
        else:
            return False
        return result.scalar_one_or_none() is not None
