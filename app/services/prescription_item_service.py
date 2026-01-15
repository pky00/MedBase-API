import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prescription_item import PrescriptionItem
from app.schemas.prescription_item import PrescriptionItemCreate, PrescriptionItemUpdate

logger = logging.getLogger(__name__)


class PrescriptionItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, item_id: UUID) -> PrescriptionItem | None:
        result = await self.db.execute(
            select(PrescriptionItem).where(PrescriptionItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_by_prescription(
        self, prescription_id: UUID
    ) -> tuple[list[PrescriptionItem], int]:
        logger.info(f"Listing prescription items for: {prescription_id}")
        query = select(PrescriptionItem).where(
            PrescriptionItem.prescription_id == prescription_id
        )
        count_query = select(func.count(PrescriptionItem.id)).where(
            PrescriptionItem.prescription_id == prescription_id
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def create(self, data: PrescriptionItemCreate, created_by: str) -> PrescriptionItem:
        logger.info(f"Adding item to prescription: {data.prescription_id}")
        item = PrescriptionItem(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(
        self, item: PrescriptionItem, data: PrescriptionItemUpdate, updated_by: str
    ) -> PrescriptionItem:
        logger.info(f"Updating prescription item: {item.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item: PrescriptionItem) -> None:
        logger.info(f"Deleting prescription item: {item.id}")
        await self.db.delete(item)
        await self.db.commit()

