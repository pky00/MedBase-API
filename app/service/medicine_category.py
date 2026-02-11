import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.medicine_category import MedicineCategory
from app.model.medicine import Medicine
from app.schema.medicine_category import MedicineCategoryCreate, MedicineCategoryUpdate

logger = logging.getLogger("medbase.service.medicine_category")


class MedicineCategoryService:
    """Service layer for medicine category operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Optional[MedicineCategory]:
        """Get medicine category by ID."""
        result = await self.db.execute(
            select(MedicineCategory).where(
                MedicineCategory.id == category_id,
                MedicineCategory.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[MedicineCategory], int]:
        """Get all medicine categories with pagination, search, and sorting."""
        query = select(MedicineCategory).where(MedicineCategory.is_deleted == False)

        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    MedicineCategory.name.ilike(search_term),
                    MedicineCategory.description.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(MedicineCategory, sort, MedicineCategory.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        categories = result.scalars().all()

        logger.debug("Queried medicine categories: total=%d returned=%d", total, len(categories))

        return list(categories), total

    async def create(
        self, data: MedicineCategoryCreate, created_by: Optional[int] = None
    ) -> MedicineCategory:
        """Create a new medicine category."""
        category = MedicineCategory(
            name=data.name,
            description=data.description,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        logger.info("Created medicine category id=%d name='%s'", category.id, category.name)
        return category

    async def update(
        self,
        category_id: int,
        data: MedicineCategoryUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[MedicineCategory]:
        """Update a medicine category."""
        category = await self.get_by_id(category_id)
        if not category:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        category.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(category)
        logger.info("Updated medicine category id=%d fields=%s", category_id, list(update_data.keys()))
        return category

    async def delete(self, category_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a medicine category."""
        category = await self.get_by_id(category_id)
        if not category:
            return False

        category.is_deleted = True
        category.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted medicine category id=%d", category_id)
        return True

    async def has_linked_medicines(self, category_id: int) -> bool:
        """Check if a category has linked medicines (non-deleted)."""
        result = await self.db.execute(
            select(func.count()).where(
                Medicine.category_id == category_id,
                Medicine.is_deleted == False,
            )
        )
        count = result.scalar()
        return count > 0
