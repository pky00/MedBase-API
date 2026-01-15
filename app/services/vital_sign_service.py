import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vital_sign import VitalSign
from app.schemas.vital_sign import VitalSignCreate, VitalSignUpdate

logger = logging.getLogger(__name__)


class VitalSignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, vital_sign_id: UUID) -> VitalSign | None:
        result = await self.db.execute(
            select(VitalSign).where(VitalSign.id == vital_sign_id)
        )
        return result.scalar_one_or_none()

    async def list_by_patient(
        self, patient_id: UUID
    ) -> tuple[list[VitalSign], int]:
        logger.info(f"Listing vital signs for patient: {patient_id}")
        query = select(VitalSign).where(VitalSign.patient_id == patient_id)
        count_query = select(func.count(VitalSign.id)).where(
            VitalSign.patient_id == patient_id
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(VitalSign.recorded_at.desc())
        result = await self.db.execute(query)
        vital_signs = list(result.scalars().all())
        return vital_signs, total

    async def create(self, data: VitalSignCreate, created_by: str) -> VitalSign:
        logger.info(f"Recording vital signs for patient: {data.patient_id}")
        vital_sign = VitalSign(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(vital_sign)
        await self.db.commit()
        await self.db.refresh(vital_sign)
        return vital_sign

    async def update(
        self, vital_sign: VitalSign, data: VitalSignUpdate, updated_by: str
    ) -> VitalSign:
        logger.info(f"Updating vital signs: {vital_sign.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vital_sign, field, value)
        vital_sign.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(vital_sign)
        return vital_sign

    async def delete(self, vital_sign: VitalSign) -> None:
        logger.info(f"Deleting vital signs: {vital_sign.id}")
        await self.db.delete(vital_sign)
        await self.db.commit()

