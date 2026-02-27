import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.inventory import Inventory

logger = logging.getLogger("medbase.service.inventory")


class InventoryService:
    """Service layer for inventory operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Get inventory record by ID."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.id == inventory_id,
                Inventory.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_item(self, item_type: str, item_id: int) -> Optional[Inventory]:
        """Get inventory record by item type and item ID."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_type == item_type,
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        item_type: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Inventory], int]:
        """Get all inventory records with pagination and filtering."""
        query = select(Inventory).where(Inventory.is_deleted == False)

        # Apply filters
        if item_type:
            query = query.where(Inventory.item_type == item_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Inventory, sort, Inventory.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        records = result.scalars().all()

        logger.debug("Queried inventory: total=%d returned=%d", total, len(records))

        return list(records), total

    async def create(
        self,
        item_type: str,
        item_id: int,
        quantity: int = 0,
        created_by: Optional[str] = None,
    ) -> Inventory:
        """Create an inventory record."""
        inventory = Inventory(
            item_type=item_type,
            item_id=item_id,
            quantity=quantity,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(inventory)
        await self.db.flush()
        await self.db.refresh(inventory)
        logger.info(
            "Created inventory id=%d item_type='%s' item_id=%d quantity=%d",
            inventory.id, item_type, item_id, quantity,
        )
        return inventory

    async def delete(self, item_type: str, item_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete an inventory record by item type and item ID."""
        inventory = await self.get_by_item(item_type, item_id)
        if not inventory:
            return False

        inventory.is_deleted = True
        inventory.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted inventory id=%d item_type='%s' item_id=%d", inventory.id, item_type, item_id)
        return True
