import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.equipment import Equipment
from app.model.equipment_category import EquipmentCategory
from app.model.inventory import Inventory
from app.schema.equipment import EquipmentCreate, EquipmentUpdate, EquipmentDetailResponse
from app.schema.enums import ItemType
from app.service.inventory import InventoryService

logger = logging.getLogger("medbase.service.equipment")


class EquipmentService:
    """Service layer for equipment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, equipment_id: int) -> Optional[Equipment]:
        """Get equipment by ID."""
        result = await self.db.execute(
            select(Equipment).where(
                Equipment.id == equipment_id,
                Equipment.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, equipment_id: int) -> Optional[EquipmentDetailResponse]:
        """Get equipment by ID with inventory and category info."""
        result = await self.db.execute(
            select(
                Equipment,
                Inventory.quantity,
                EquipmentCategory.name.label("category_name"),
            )
            .outerjoin(
                Inventory,
                (Inventory.item_type == ItemType.EQUIPMENT)
                & (Inventory.item_id == Equipment.id)
                & (Inventory.is_deleted == False),
            )
            .outerjoin(
                EquipmentCategory,
                (EquipmentCategory.id == Equipment.category_id)
                & (EquipmentCategory.is_deleted == False),
            )
            .where(
                Equipment.id == equipment_id,
                Equipment.is_deleted == False,
            )
        )
        row = result.first()
        if not row:
            return None

        return EquipmentDetailResponse.from_row(row)

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        condition: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Equipment], int]:
        """Get all equipment with pagination, filtering, and sorting."""
        query = select(Equipment).where(Equipment.is_deleted == False)

        # Apply filters
        if category_id is not None:
            query = query.where(Equipment.category_id == category_id)
        if is_active is not None:
            query = query.where(Equipment.is_active == is_active)
        if condition:
            query = query.where(Equipment.condition == condition)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Equipment.name.ilike(search_term),
                    Equipment.description.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Equipment, sort, Equipment.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        logger.debug("Queried equipment: total=%d returned=%d", total, len(items))

        return list(items), total

    async def create(
        self, data: EquipmentCreate, created_by: Optional[int] = None
    ) -> Equipment:
        """Create new equipment and its inventory record."""
        equipment = Equipment(
            name=data.name,
            category_id=data.category_id,
            description=data.description,
            condition=data.condition,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(equipment)
        await self.db.flush()
        await self.db.refresh(equipment)

        # Auto-create inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.create(
            item_type=ItemType.EQUIPMENT,
            item_id=equipment.id,
            quantity=0,
            created_by=created_by,
        )

        logger.info("Created equipment id=%d name='%s'", equipment.id, equipment.name)
        return equipment

    async def update(
        self,
        equipment_id: int,
        data: EquipmentUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[Equipment]:
        """Update equipment."""
        equipment = await self.get_by_id(equipment_id)
        if not equipment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)

        equipment.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(equipment)
        logger.info("Updated equipment id=%d fields=%s", equipment_id, list(update_data.keys()))
        return equipment

    async def delete(self, equipment_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete equipment and its inventory record."""
        equipment = await self.get_by_id(equipment_id)
        if not equipment:
            return False

        equipment.is_deleted = True
        equipment.updated_by = deleted_by

        # Also soft-delete the inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.delete(ItemType.EQUIPMENT, equipment_id, deleted_by=deleted_by)

        await self.db.flush()
        logger.info("Soft-deleted equipment id=%d", equipment_id)
        return True

    async def get_inventory_quantity(self, equipment_id: int) -> int:
        """Get inventory quantity for equipment."""
        inventory_service = InventoryService(self.db)
        inventory = await inventory_service.get_by_item(ItemType.EQUIPMENT, equipment_id)
        if inventory:
            return inventory.quantity
        return 0
