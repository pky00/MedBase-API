import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medicine_category import MedicineCategory
from app.schemas.medicine_category import MedicineCategoryCreate, MedicineCategoryUpdate

logger = logging.getLogger(__name__)


class MedicineCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: UUID) -> MedicineCategory | None:
        result = await self.db.execute(
            select(MedicineCategory).where(MedicineCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MedicineCategory | None:
        result = await self.db.execute(
            select(MedicineCategory).where(MedicineCategory.code == code)
        )
        return result.scalar_one_or_none()

    async def list_categories(self) -> tuple[list[MedicineCategory], int]:
        logger.info("Listing medicine categories")
        query = select(MedicineCategory).order_by(MedicineCategory.name)
        count_query = select(func.count(MedicineCategory.id))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        result = await self.db.execute(query)
        categories = list(result.scalars().all())
        return categories, total

    async def create(self, data: MedicineCategoryCreate, created_by: str) -> MedicineCategory:
        logger.info(f"Creating medicine category: {data.name}")
        category = MedicineCategory(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(
        self, category: MedicineCategory, data: MedicineCategoryUpdate, updated_by: str
    ) -> MedicineCategory:
        logger.info(f"Updating medicine category: {category.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: MedicineCategory) -> None:
        logger.info(f"Deleting medicine category: {category.id}")
        await self.db.delete(category)
        await self.db.commit()

