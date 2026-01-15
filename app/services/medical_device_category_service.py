import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medical_device_category import MedicalDeviceCategory
from app.schemas.medical_device_category import (
    MedicalDeviceCategoryCreate,
    MedicalDeviceCategoryUpdate,
)

logger = logging.getLogger(__name__)


class MedicalDeviceCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: UUID) -> MedicalDeviceCategory | None:
        result = await self.db.execute(
            select(MedicalDeviceCategory).where(MedicalDeviceCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MedicalDeviceCategory | None:
        result = await self.db.execute(
            select(MedicalDeviceCategory).where(MedicalDeviceCategory.code == code)
        )
        return result.scalar_one_or_none()

    async def list_categories(self) -> tuple[list[MedicalDeviceCategory], int]:
        logger.info("Listing medical device categories")
        query = select(MedicalDeviceCategory).order_by(MedicalDeviceCategory.name)
        count_query = select(func.count(MedicalDeviceCategory.id))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        result = await self.db.execute(query)
        categories = list(result.scalars().all())
        return categories, total

    async def create(
        self, data: MedicalDeviceCategoryCreate, created_by: str
    ) -> MedicalDeviceCategory:
        logger.info(f"Creating medical device category: {data.name}")
        category = MedicalDeviceCategory(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(
        self,
        category: MedicalDeviceCategory,
        data: MedicalDeviceCategoryUpdate,
        updated_by: str,
    ) -> MedicalDeviceCategory:
        logger.info(f"Updating medical device category: {category.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: MedicalDeviceCategory) -> None:
        logger.info(f"Deleting medical device category: {category.id}")
        await self.db.delete(category)
        await self.db.commit()

