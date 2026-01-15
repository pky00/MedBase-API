import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate

logger = logging.getLogger(__name__)


class EquipmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None:
        result = await self.db.execute(
            select(Equipment).where(Equipment.id == equipment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_asset_code(self, asset_code: str) -> Equipment | None:
        result = await self.db.execute(
            select(Equipment).where(Equipment.asset_code == asset_code)
        )
        return result.scalar_one_or_none()

    async def get_by_serial_number(self, serial_number: str) -> Equipment | None:
        result = await self.db.execute(
            select(Equipment).where(Equipment.serial_number == serial_number)
        )
        return result.scalar_one_or_none()

    async def list_equipment(
        self,
        page: int = 1,
        size: int = 10,
        category_id: UUID | None = None,
        is_active: bool | None = None,
        is_donation: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Equipment], int]:
        logger.info(f"Listing equipment: page={page}, size={size}")
        query = select(Equipment)
        count_query = select(func.count(Equipment.id))

        if category_id:
            query = query.where(Equipment.category_id == category_id)
            count_query = count_query.where(Equipment.category_id == category_id)

        if is_active is not None:
            query = query.where(Equipment.is_active == is_active)
            count_query = count_query.where(Equipment.is_active == is_active)

        if is_donation is not None:
            query = query.where(Equipment.is_donation == is_donation)
            count_query = count_query.where(Equipment.is_donation == is_donation)

        if search:
            search_filter = Equipment.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Equipment.name)
        result = await self.db.execute(query)
        equipment = list(result.scalars().all())

        return equipment, total

    async def create(self, data: EquipmentCreate, created_by: str) -> Equipment:
        logger.info(f"Creating equipment: {data.name}")
        equipment = Equipment(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(equipment)
        await self.db.commit()
        await self.db.refresh(equipment)
        return equipment

    async def update(self, equipment: Equipment, data: EquipmentUpdate, updated_by: str) -> Equipment:
        logger.info(f"Updating equipment: {equipment.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)
        equipment.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(equipment)
        return equipment

    async def delete(self, equipment: Equipment) -> None:
        logger.info(f"Deleting equipment: {equipment.id}")
        await self.db.delete(equipment)
        await self.db.commit()

