import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory_transaction import InventoryTransaction
from app.schemas.inventory_transaction import InventoryTransactionCreate
from app.models.enums import InventoryTransactionType, ReferenceType
from app.utils.sort import apply_sorting

logger = logging.getLogger(__name__)

# Fields that can be sorted on
INVENTORY_TRANSACTION_SORTABLE_FIELDS = [
    'transaction_type',
    'quantity',
    'transaction_date',
    'reference_type',
    'created_at',
]


class InventoryTransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, transaction_id: UUID) -> InventoryTransaction | None:
        result = await self.db.execute(
            select(InventoryTransaction).where(InventoryTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        page: int = 1,
        size: int = 10,
        transaction_type: InventoryTransactionType | None = None,
        reference_type: ReferenceType | None = None,
        medicine_inventory_id: UUID | None = None,
        medical_device_inventory_id: UUID | None = None,
        equipment_id: UUID | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[InventoryTransaction], int]:
        logger.info(f"Listing inventory transactions: page={page}, size={size}")
        query = select(InventoryTransaction)
        count_query = select(func.count(InventoryTransaction.id))

        if transaction_type:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)
            count_query = count_query.where(InventoryTransaction.transaction_type == transaction_type)

        if reference_type:
            query = query.where(InventoryTransaction.reference_type == reference_type)
            count_query = count_query.where(InventoryTransaction.reference_type == reference_type)

        if medicine_inventory_id:
            query = query.where(InventoryTransaction.medicine_inventory_id == medicine_inventory_id)
            count_query = count_query.where(InventoryTransaction.medicine_inventory_id == medicine_inventory_id)

        if medical_device_inventory_id:
            query = query.where(InventoryTransaction.medical_device_inventory_id == medical_device_inventory_id)
            count_query = count_query.where(InventoryTransaction.medical_device_inventory_id == medical_device_inventory_id)

        if equipment_id:
            query = query.where(InventoryTransaction.equipment_id == equipment_id)
            count_query = count_query.where(InventoryTransaction.equipment_id == equipment_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting using the utility
        query = apply_sorting(
            query=query,
            model=InventoryTransaction,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_fields=INVENTORY_TRANSACTION_SORTABLE_FIELDS,
            default_field='transaction_date',
            default_order='desc'
        )

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        result = await self.db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total

    async def create(self, data: InventoryTransactionCreate, created_by: str) -> InventoryTransaction:
        logger.info(f"Creating inventory transaction: {data.transaction_type}")
        transaction = InventoryTransaction(
            **data.model_dump(exclude_none=True),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        logger.info(f"Created inventory transaction with ID: {transaction.id}")
        return transaction

    async def delete(self, transaction: InventoryTransaction) -> None:
        logger.info(f"Deleting inventory transaction: {transaction.id}")
        await self.db.delete(transaction)
        await self.db.commit()

