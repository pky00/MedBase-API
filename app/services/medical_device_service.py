import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medical_device import MedicalDevice
from app.schemas.medical_device import MedicalDeviceCreate, MedicalDeviceUpdate

logger = logging.getLogger(__name__)


class MedicalDeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, device_id: UUID) -> MedicalDevice | None:
        result = await self.db.execute(
            select(MedicalDevice).where(MedicalDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MedicalDevice | None:
        result = await self.db.execute(
            select(MedicalDevice).where(MedicalDevice.code == code)
        )
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        page: int = 1,
        size: int = 10,
        category_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[MedicalDevice], int]:
        logger.info(f"Listing medical devices: page={page}, size={size}")
        query = select(MedicalDevice)
        count_query = select(func.count(MedicalDevice.id))

        if category_id:
            query = query.where(MedicalDevice.category_id == category_id)
            count_query = count_query.where(MedicalDevice.category_id == category_id)

        if is_active is not None:
            query = query.where(MedicalDevice.is_active == is_active)
            count_query = count_query.where(MedicalDevice.is_active == is_active)

        if search:
            search_filter = MedicalDevice.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(MedicalDevice.name)
        result = await self.db.execute(query)
        devices = list(result.scalars().all())

        return devices, total

    async def create(self, data: MedicalDeviceCreate, created_by: str) -> MedicalDevice:
        logger.info(f"Creating medical device: {data.name}")
        device = MedicalDevice(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def update(
        self, device: MedicalDevice, data: MedicalDeviceUpdate, updated_by: str
    ) -> MedicalDevice:
        logger.info(f"Updating medical device: {device.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        device.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def delete(self, device: MedicalDevice) -> None:
        logger.info(f"Deleting medical device: {device.id}")
        await self.db.delete(device)
        await self.db.commit()

