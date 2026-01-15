import logging
from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prescribed_device import PrescribedDevice
from app.schemas.prescribed_device import PrescribedDeviceCreate, PrescribedDeviceUpdate

logger = logging.getLogger(__name__)


class PrescribedDeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, device_id: UUID) -> PrescribedDevice | None:
        result = await self.db.execute(
            select(PrescribedDevice).where(PrescribedDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def list_prescribed_devices(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: UUID | None = None,
        doctor_id: UUID | None = None,
        device_id: UUID | None = None,
        is_returned: bool | None = None,
    ) -> tuple[list[PrescribedDevice], int]:
        logger.info(f"Listing prescribed devices: page={page}, size={size}")
        query = select(PrescribedDevice)
        count_query = select(func.count(PrescribedDevice.id))

        if patient_id:
            query = query.where(PrescribedDevice.patient_id == patient_id)
            count_query = count_query.where(PrescribedDevice.patient_id == patient_id)

        if doctor_id:
            query = query.where(PrescribedDevice.doctor_id == doctor_id)
            count_query = count_query.where(PrescribedDevice.doctor_id == doctor_id)

        if device_id:
            query = query.where(PrescribedDevice.device_id == device_id)
            count_query = count_query.where(PrescribedDevice.device_id == device_id)

        if is_returned is not None:
            if is_returned:
                query = query.where(PrescribedDevice.return_date.isnot(None))
                count_query = count_query.where(PrescribedDevice.return_date.isnot(None))
            else:
                query = query.where(PrescribedDevice.return_date.is_(None))
                count_query = count_query.where(PrescribedDevice.return_date.is_(None))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            PrescribedDevice.prescription_date.desc()
        )
        result = await self.db.execute(query)
        devices = list(result.scalars().all())

        return devices, total

    async def create(self, data: PrescribedDeviceCreate, created_by: str) -> PrescribedDevice:
        logger.info(f"Prescribing device to patient: {data.patient_id}")
        device = PrescribedDevice(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def update(
        self, device: PrescribedDevice, data: PrescribedDeviceUpdate, updated_by: str
    ) -> PrescribedDevice:
        logger.info(f"Updating prescribed device: {device.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        device.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def delete(self, device: PrescribedDevice) -> None:
        logger.info(f"Deleting prescribed device: {device.id}")
        await self.db.delete(device)
        await self.db.commit()

