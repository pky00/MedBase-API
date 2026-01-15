import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.equipment_category import EquipmentCategory
from app.schemas.equipment_category import EquipmentCategoryCreate, EquipmentCategoryUpdate

logger = logging.getLogger(__name__)


class EquipmentCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: UUID) -> EquipmentCategory | None:
        result = await self.db.execute(
            select(EquipmentCategory).where(EquipmentCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> EquipmentCategory | None:
        result = await self.db.execute(
            select(EquipmentCategory).where(EquipmentCategory.code == code)
        )
        return result.scalar_one_or_none()

    async def list_categories(self, is_active: bool | None = None) -> tuple[list[EquipmentCategory], int]:
        logger.info("Listing equipment categories")
        query = select(EquipmentCategory)
        count_query = select(func.count(EquipmentCategory.id))

        if is_active is not None:
            query = query.where(EquipmentCategory.is_active == is_active)
            count_query = count_query.where(EquipmentCategory.is_active == is_active)

        query = query.order_by(EquipmentCategory.name)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        result = await self.db.execute(query)
        categories = list(result.scalars().all())
        return categories, total

    async def create(self, data: EquipmentCategoryCreate, created_by: str) -> EquipmentCategory:
        logger.info(f"Creating equipment category: {data.name}")
        category = EquipmentCategory(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(
        self, category: EquipmentCategory, data: EquipmentCategoryUpdate, updated_by: str
    ) -> EquipmentCategory:
        logger.info(f"Updating equipment category: {category.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: EquipmentCategory) -> None:
        logger.info(f"Deleting equipment category: {category.id}")
        await self.db.delete(category)
        await self.db.commit()

