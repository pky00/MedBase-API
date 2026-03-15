import logging
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.inventory import Inventory
from app.model.item import Item

logger = logging.getLogger("medbase.service.inventory")


class InventoryService:
    """Service layer for inventory operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_raw_by_item(self, item_id: int) -> Optional[Inventory]:
        """Get raw Inventory ORM object by item ID (for internal mutations)."""
        result = await self.db.execute(
            select(Inventory).where(
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, inventory_id: int) -> Optional[dict]:
        """Get inventory record by ID (enriched with item info)."""
        result = await self.db.execute(
            select(Inventory, Item.item_type, Item.name.label("item_name"))
            .outerjoin(Item, Inventory.item_id == Item.id)
            .where(
                Inventory.id == inventory_id,
                Inventory.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None
        return self._row_to_dict(row)

    async def get_by_item(self, item_id: int) -> Optional[dict]:
        """Get inventory record by item ID (enriched with item info)."""
        result = await self.db.execute(
            select(Inventory, Item.item_type, Item.name.label("item_name"))
            .outerjoin(Item, Inventory.item_id == Item.id)
            .where(
                Inventory.item_id == item_id,
                Inventory.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None
        return self._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a (Inventory, item_type, item_name) row to a dict."""
        inv = row[0]
        return {
            "id": inv.id,
            "item_id": inv.item_id,
            "quantity": inv.quantity,
            "is_deleted": inv.is_deleted,
            "created_by": inv.created_by,
            "created_at": inv.created_at,
            "updated_by": inv.updated_by,
            "updated_at": inv.updated_at,
            "item_type": row[1],
            "item_name": row[2],
        }

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        item_type: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get all inventory records with pagination and filtering."""
        query = (
            select(Inventory, Item.item_type, Item.name.label("item_name"))
            .outerjoin(Item, Inventory.item_id == Item.id)
            .where(Inventory.is_deleted == False)
        )

        # Apply filters
        if item_type:
            query = query.where(Item.item_type == item_type)

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
        rows = result.all()

        records = [self._row_to_dict(row) for row in rows]

        logger.debug("Queried inventory: total=%d returned=%d", total, len(records))

        return records, total

    async def create(
        self,
        item_id: int,
        quantity: int = 0,
        created_by: Optional[str] = None,
    ) -> Inventory:
        """Create an inventory record."""
        inventory = Inventory(
            item_id=item_id,
            quantity=quantity,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(inventory)
        await self.db.flush()
        await self.db.refresh(inventory)
        logger.info(
            "Created inventory id=%d item_id=%d quantity=%d",
            inventory.id, item_id, quantity,
        )
        return inventory

    async def delete(self, item_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete an inventory record by item ID."""
        inventory = await self._get_raw_by_item(item_id)
        if not inventory:
            return False

        inventory.is_deleted = True
        inventory.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted inventory id=%d item_id=%d", inventory.id, item_id)
        return True
