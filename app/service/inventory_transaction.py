import logging
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.inventory_transaction import InventoryTransaction
from app.model.inventory_transaction_item import InventoryTransactionItem
from app.model.inventory import Inventory
from app.model.item import Item
from app.model.third_party import ThirdParty
from app.model.partner import Partner
from app.model.doctor import Doctor
from app.schema.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionUpdate,
    InventoryTransactionListResponse,
    InventoryTransactionResponse,
    TransactionItemCreate,
    TransactionItemUpdate,
    TransactionItemResponse,
)

logger = logging.getLogger("medbase.service.inventory_transaction")

# Transaction types that increase inventory
INCREASE_TYPES = {"purchase", "donation"}
# Transaction types that decrease inventory
DECREASE_TYPES = {"prescription", "loss", "breakage", "expiration", "destruction"}


class InventoryTransactionService:
    """Service layer for inventory transaction operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Inventory quantity helpers ----

    async def _adjust_inventory(self, item_id: int, quantity: int, transaction_type: str, updated_by: Optional[str] = None) -> None:
        """Adjust inventory quantity based on transaction type."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        inventory = result.scalar_one_or_none()
        if not inventory:
            raise ValueError(f"Inventory record not found for item_id={item_id}")

        if transaction_type in INCREASE_TYPES:
            inventory.quantity += quantity
        else:
            if inventory.quantity < quantity:
                raise ValueError(
                    f"Insufficient inventory for item_id={item_id}: "
                    f"available={inventory.quantity}, requested={quantity}"
                )
            inventory.quantity -= quantity

        inventory.updated_by = updated_by
        await self.db.flush()
        logger.info(
            "Adjusted inventory item_id=%d by %s%d (new qty=%d)",
            item_id,
            "+" if transaction_type in INCREASE_TYPES else "-",
            quantity, inventory.quantity,
        )

    async def _reverse_inventory(self, item_id: int, quantity: int, transaction_type: str, updated_by: Optional[str] = None) -> None:
        """Reverse an inventory adjustment (for delete/update)."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        inventory = result.scalar_one_or_none()
        if not inventory:
            return

        if transaction_type in INCREASE_TYPES:
            inventory.quantity = max(0, inventory.quantity - quantity)
        else:
            inventory.quantity += quantity

        inventory.updated_by = updated_by
        await self.db.flush()

    # ---- Validation helpers ----

    async def validate_donation_third_party(self, third_party_id: int) -> None:
        """Validate that third_party_id belongs to a donor partner."""
        result = await self.db.execute(
            select(Partner).where(
                Partner.third_party_id == third_party_id,
                Partner.is_deleted == False,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError("third_party_id must belong to a partner for donation transactions")
        if partner.partner_type not in ("donor", "both"):
            raise ValueError("Partner must have partner_type of 'donor' or 'both' for donations")

    async def validate_prescription_third_party(self, third_party_id: int) -> None:
        """Validate that third_party_id belongs to a doctor."""
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.third_party_id == third_party_id,
                Doctor.is_deleted == False,
            )
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            raise ValueError("third_party_id must belong to a doctor for prescription transactions")

    async def validate_inventory_item(self, item_id: int) -> None:
        """Validate that an inventory record exists for the given item."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        inventory = result.scalar_one_or_none()
        if not inventory:
            raise ValueError(f"Inventory record not found for item_id={item_id}")

    async def validate_prescription_item(self, item_id: int) -> None:
        """Validate that the item is not equipment (equipment cannot be prescribed)."""
        result = await self.db.execute(
            select(Item.item_type).where(Item.id == item_id)
        )
        item_type = result.scalar_one_or_none()
        if item_type == "equipment":
            raise ValueError("Equipment cannot be prescribed")

    async def build_item_response(self, item: InventoryTransactionItem) -> TransactionItemResponse:
        """Build a TransactionItemResponse from a model instance."""
        item_name, item_type = await self._get_item_info(item.item_id)
        return TransactionItemResponse(
            id=item.id,
            transaction_id=item.transaction_id,
            item_id=item.item_id,
            quantity=item.quantity,
            is_deleted=item.is_deleted,
            created_by=item.created_by,
            created_at=item.created_at,
            updated_by=item.updated_by,
            updated_at=item.updated_at,
            item_name=item_name,
            item_type=item_type,
        )

    # ---- Transaction CRUD ----

    async def get_by_id(self, transaction_id: int) -> Optional[InventoryTransaction]:
        """Get transaction by ID."""
        result = await self.db.execute(
            select(InventoryTransaction).where(
                InventoryTransaction.id == transaction_id,
                InventoryTransaction.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_items(self, transaction_id: int) -> Optional[InventoryTransactionResponse]:
        """Get transaction by ID with items and third party name."""
        result = await self.db.execute(
            select(
                InventoryTransaction,
                ThirdParty.name.label("third_party_name"),
            )
            .outerjoin(ThirdParty, InventoryTransaction.third_party_id == ThirdParty.id)
            .where(
                InventoryTransaction.id == transaction_id,
                InventoryTransaction.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None

        transaction = row[0]
        third_party_name = row[1]

        # Get items
        items_result = await self.db.execute(
            select(InventoryTransactionItem).where(
                InventoryTransactionItem.transaction_id == transaction_id,
                InventoryTransactionItem.is_deleted == False,
            )
        )
        items = items_result.scalars().all()

        item_responses = []
        for item in items:
            item_name, item_type = await self._get_item_info(item.item_id)
            item_responses.append(
                TransactionItemResponse(
                    id=item.id,
                    transaction_id=item.transaction_id,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    is_deleted=item.is_deleted,
                    created_by=item.created_by,
                    created_at=item.created_at,
                    updated_by=item.updated_by,
                    updated_at=item.updated_at,
                    item_name=item_name,
                    item_type=item_type,
                )
            )

        return InventoryTransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            third_party_id=transaction.third_party_id,
            appointment_id=transaction.appointment_id,
            transaction_date=transaction.transaction_date,
            notes=transaction.notes,
            is_deleted=transaction.is_deleted,
            created_by=transaction.created_by,
            created_at=transaction.created_at,
            updated_by=transaction.updated_by,
            updated_at=transaction.updated_at,
            third_party_name=third_party_name,
            items=item_responses,
        )

    async def _get_item_info(self, item_id: int) -> tuple:
        """Get the name and type of an item by ID."""
        result = await self.db.execute(
            select(Item.name, Item.item_type).where(Item.id == item_id)
        )
        row = result.one_or_none()
        if row:
            return row[0], row[1]
        return None, None

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        transaction_type: Optional[str] = None,
        third_party_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        transaction_date: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get all transactions with pagination and filtering."""
        query = (
            select(
                InventoryTransaction,
                ThirdParty.name.label("third_party_name"),
            )
            .outerjoin(ThirdParty, InventoryTransaction.third_party_id == ThirdParty.id)
            .where(InventoryTransaction.is_deleted == False)
        )

        if transaction_type is not None:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)
        if third_party_id is not None:
            query = query.where(InventoryTransaction.third_party_id == third_party_id)
        if appointment_id is not None:
            query = query.where(InventoryTransaction.appointment_id == appointment_id)
        if transaction_date is not None:
            query = query.where(InventoryTransaction.transaction_date == transaction_date)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(InventoryTransaction, sort, InventoryTransaction.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        transactions = [
            InventoryTransactionListResponse.from_row(row).model_dump()
            for row in rows
        ]

        logger.debug("Queried inventory transactions: total=%d returned=%d", total, len(transactions))
        return transactions, total

    async def get_transactions_by_item(
        self,
        item_id: int,
        page: int = 1,
        size: int = 10,
        transaction_type: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get inventory transactions that include a specific item, with the transaction item details."""
        query = (
            select(
                InventoryTransaction,
                ThirdParty.name.label("third_party_name"),
                InventoryTransactionItem.id.label("transaction_item_id"),
                InventoryTransactionItem.quantity.label("transaction_item_quantity"),
            )
            .join(
                InventoryTransactionItem,
                (InventoryTransactionItem.transaction_id == InventoryTransaction.id)
                & (InventoryTransactionItem.is_deleted == False),
            )
            .outerjoin(ThirdParty, InventoryTransaction.third_party_id == ThirdParty.id)
            .where(
                InventoryTransaction.is_deleted == False,
                InventoryTransactionItem.item_id == item_id,
            )
        )

        if transaction_type is not None:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(InventoryTransaction, sort, InventoryTransaction.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        transactions = []
        for row in rows:
            txn = row[0]
            transactions.append({
                "id": txn.id,
                "transaction_type": txn.transaction_type,
                "third_party_id": txn.third_party_id,
                "appointment_id": txn.appointment_id,
                "transaction_date": txn.transaction_date,
                "notes": txn.notes,
                "is_deleted": txn.is_deleted,
                "created_by": txn.created_by,
                "created_at": txn.created_at,
                "updated_by": txn.updated_by,
                "updated_at": txn.updated_at,
                "third_party_name": row[1],
                "transaction_item_id": row[2],
                "transaction_item_quantity": row[3],
            })

        logger.debug("Queried transactions for item_id=%d: total=%d returned=%d", item_id, total, len(transactions))
        return transactions, total

    async def create(
        self,
        data: InventoryTransactionCreate,
        third_party_id: int,
        created_by: Optional[str] = None,
    ) -> InventoryTransaction:
        """Create a new inventory transaction with optional items."""
        transaction = InventoryTransaction(
            transaction_type=data.transaction_type,
            third_party_id=third_party_id,
            appointment_id=data.appointment_id,
            transaction_date=data.transaction_date,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        logger.info(
            "Created inventory transaction id=%d type=%s third_party_id=%d",
            transaction.id, data.transaction_type, third_party_id,
        )

        # Create items if provided
        if data.items:
            for item_data in data.items:
                await self.create_item(
                    transaction.id,
                    item_data,
                    data.transaction_type,
                    created_by=created_by,
                )

        return transaction

    async def update(
        self,
        transaction_id: int,
        data: InventoryTransactionUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[InventoryTransaction]:
        """Update a transaction (only date and notes)."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)

        transaction.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(transaction)

        logger.info("Updated inventory transaction id=%d fields=%s", transaction_id, list(update_data.keys()))
        return transaction

    async def delete(self, transaction_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a transaction and reverse inventory changes for its items."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False

        # Get all active items and reverse their inventory impact
        items_result = await self.db.execute(
            select(InventoryTransactionItem).where(
                InventoryTransactionItem.transaction_id == transaction_id,
                InventoryTransactionItem.is_deleted == False,
            )
        )
        items = items_result.scalars().all()

        for item in items:
            await self._reverse_inventory(
                item.item_id, item.quantity,
                transaction.transaction_type, updated_by=deleted_by,
            )
            item.is_deleted = True
            item.updated_by = deleted_by

        transaction.is_deleted = True
        transaction.updated_by = deleted_by
        await self.db.flush()

        logger.info("Soft-deleted inventory transaction id=%d (reversed %d items)", transaction_id, len(items))
        return True

    # ---- Transaction Item CRUD ----

    async def get_item_by_id(self, item_id: int) -> Optional[InventoryTransactionItem]:
        """Get a transaction item by ID."""
        result = await self.db.execute(
            select(InventoryTransactionItem).where(
                InventoryTransactionItem.id == item_id,
                InventoryTransactionItem.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_items_for_transaction(self, transaction_id: int) -> List[TransactionItemResponse]:
        """Get all items for a transaction."""
        result = await self.db.execute(
            select(InventoryTransactionItem).where(
                InventoryTransactionItem.transaction_id == transaction_id,
                InventoryTransactionItem.is_deleted == False,
            )
        )
        items = result.scalars().all()

        item_responses = []
        for item in items:
            item_name, item_type = await self._get_item_info(item.item_id)
            item_responses.append(
                TransactionItemResponse(
                    id=item.id,
                    transaction_id=item.transaction_id,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    is_deleted=item.is_deleted,
                    created_by=item.created_by,
                    created_at=item.created_at,
                    updated_by=item.updated_by,
                    updated_at=item.updated_at,
                    item_name=item_name,
                    item_type=item_type,
                )
            )
        return item_responses

    async def create_item(
        self,
        transaction_id: int,
        data: TransactionItemCreate,
        transaction_type: str,
        created_by: Optional[str] = None,
    ) -> InventoryTransactionItem:
        """Create a transaction item and adjust inventory."""
        item = InventoryTransactionItem(
            transaction_id=transaction_id,
            item_id=data.item_id,
            quantity=data.quantity,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        # Adjust inventory
        await self._adjust_inventory(
            data.item_id, data.quantity,
            transaction_type, updated_by=created_by,
        )

        logger.info(
            "Created transaction item id=%d transaction_id=%d item_id=%d qty=%d",
            item.id, transaction_id, data.item_id, data.quantity,
        )
        return item

    async def update_item(
        self,
        item_id: int,
        data: TransactionItemUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[InventoryTransactionItem]:
        """Update a transaction item and adjust inventory accordingly."""
        item = await self.get_item_by_id(item_id)
        if not item:
            return None

        # Get the parent transaction to know the type
        transaction = await self.get_by_id(item.transaction_id)
        if not transaction:
            return None

        # Reverse old inventory impact
        await self._reverse_inventory(
            item.item_id, item.quantity,
            transaction.transaction_type, updated_by=updated_by,
        )

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(item)

        # Apply new inventory impact
        await self._adjust_inventory(
            item.item_id, item.quantity,
            transaction.transaction_type, updated_by=updated_by,
        )

        logger.info("Updated transaction item id=%d fields=%s", item_id, list(update_data.keys()))
        return item

    async def delete_item(self, item_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a transaction item and reverse its inventory impact."""
        item = await self.get_item_by_id(item_id)
        if not item:
            return False

        transaction = await self.get_by_id(item.transaction_id)
        if not transaction:
            return False

        # Reverse inventory
        await self._reverse_inventory(
            item.item_id, item.quantity,
            transaction.transaction_type, updated_by=deleted_by,
        )

        item.is_deleted = True
        item.updated_by = deleted_by
        await self.db.flush()

        logger.info("Soft-deleted transaction item id=%d", item_id)
        return True
