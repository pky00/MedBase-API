import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medicine import Medicine
from app.schemas.medicine import MedicineCreate, MedicineUpdate

logger = logging.getLogger(__name__)


class MedicineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, medicine_id: UUID) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(Medicine.id == medicine_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(Medicine.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).where(Medicine.barcode == barcode)
        )
        return result.scalar_one_or_none()

    async def list_medicines(
        self,
        page: int = 1,
        size: int = 10,
        category_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Medicine], int]:
        logger.info(f"Listing medicines: page={page}, size={size}")
        query = select(Medicine)
        count_query = select(func.count(Medicine.id))

        if category_id:
            query = query.where(Medicine.category_id == category_id)
            count_query = count_query.where(Medicine.category_id == category_id)

        if is_active is not None:
            query = query.where(Medicine.is_active == is_active)
            count_query = count_query.where(Medicine.is_active == is_active)

        if search:
            search_filter = (
                Medicine.name.ilike(f"%{search}%")
                | Medicine.generic_name.ilike(f"%{search}%")
                | Medicine.brand_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Medicine.name)
        result = await self.db.execute(query)
        medicines = list(result.scalars().all())

        return medicines, total

    async def create(self, data: MedicineCreate, created_by: str) -> Medicine:
        logger.info(f"Creating medicine: {data.name}")
        medicine = Medicine(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(medicine)
        await self.db.commit()
        await self.db.refresh(medicine)
        return medicine

    async def update(self, medicine: Medicine, data: MedicineUpdate, updated_by: str) -> Medicine:
        logger.info(f"Updating medicine: {medicine.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(medicine, field, value)
        medicine.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(medicine)
        return medicine

    async def delete(self, medicine: Medicine) -> None:
        logger.info(f"Deleting medicine: {medicine.id}")
        await self.db.delete(medicine)
        await self.db.commit()

