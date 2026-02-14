import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.medicine import Medicine
from app.model.medicine_category import MedicineCategory
from app.model.inventory import Inventory
from app.schema.medicine import MedicineCreate, MedicineUpdate, MedicineDetailResponse
from app.schema.enums import ItemType
from app.service.inventory import InventoryService

logger = logging.getLogger("medbase.service.medicine")


class MedicineService:
    """Service layer for medicine operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, medicine_id: int) -> Optional[Medicine]:
        """Get medicine by ID."""
        result = await self.db.execute(
            select(Medicine).where(
                Medicine.id == medicine_id,
                Medicine.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, medicine_id: int) -> Optional[MedicineDetailResponse]:
        """Get medicine by ID with inventory and category info."""
        result = await self.db.execute(
            select(
                Medicine,
                Inventory.quantity,
                MedicineCategory.name.label("category_name"),
            )
            .outerjoin(
                Inventory,
                (Inventory.item_type == ItemType.MEDICINE)
                & (Inventory.item_id == Medicine.id)
                & (Inventory.is_deleted == False),
            )
            .outerjoin(
                MedicineCategory,
                (MedicineCategory.id == Medicine.category_id)
                & (MedicineCategory.is_deleted == False),
            )
            .where(
                Medicine.id == medicine_id,
                Medicine.is_deleted == False,
            )
        )
        row = result.first()
        if not row:
            return None

        return MedicineDetailResponse.from_row(row)

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Medicine], int]:
        """Get all medicines with pagination, filtering, and sorting."""
        query = select(Medicine).where(Medicine.is_deleted == False)

        # Apply filters
        if category_id is not None:
            query = query.where(Medicine.category_id == category_id)
        if is_active is not None:
            query = query.where(Medicine.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Medicine.name.ilike(search_term),
                    Medicine.description.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Medicine, sort, Medicine.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        medicines = result.scalars().all()

        logger.debug("Queried medicines: total=%d returned=%d", total, len(medicines))

        return list(medicines), total

    async def create(
        self, data: MedicineCreate, created_by: Optional[int] = None
    ) -> Medicine:
        """Create a new medicine and its inventory record."""
        medicine = Medicine(
            name=data.name,
            category_id=data.category_id,
            description=data.description,
            unit=data.unit,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(medicine)
        await self.db.flush()
        await self.db.refresh(medicine)

        # Auto-create inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.create(
            item_type=ItemType.MEDICINE,
            item_id=medicine.id,
            quantity=0,
            created_by=created_by,
        )

        logger.info("Created medicine id=%d name='%s'", medicine.id, medicine.name)
        return medicine

    async def update(
        self,
        medicine_id: int,
        data: MedicineUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[Medicine]:
        """Update a medicine."""
        medicine = await self.get_by_id(medicine_id)
        if not medicine:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(medicine, field, value)

        medicine.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(medicine)
        logger.info("Updated medicine id=%d fields=%s", medicine_id, list(update_data.keys()))
        return medicine

    async def delete(self, medicine_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a medicine and its inventory record."""
        medicine = await self.get_by_id(medicine_id)
        if not medicine:
            return False

        medicine.is_deleted = True
        medicine.updated_by = deleted_by

        # Also soft-delete the inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.delete(ItemType.MEDICINE, medicine_id, deleted_by=deleted_by)

        await self.db.flush()
        logger.info("Soft-deleted medicine id=%d", medicine_id)
        return True

    async def get_inventory_quantity(self, medicine_id: int) -> int:
        """Get inventory quantity for a medicine."""
        inventory_service = InventoryService(self.db)
        inventory = await inventory_service.get_by_item(ItemType.MEDICINE, medicine_id)
        if inventory:
            return inventory.quantity
        return 0
