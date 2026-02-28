import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.model.vital_sign import VitalSign
from app.model.appointment import Appointment
from app.schema.vital_sign import VitalSignCreate, VitalSignUpdate

logger = logging.getLogger("medbase.service.vital_sign")


class VitalSignService:
    """Service layer for vital sign operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, vital_sign_id: int) -> Optional[VitalSign]:
        """Get vital sign by ID."""
        result = await self.db.execute(
            select(VitalSign).where(
                VitalSign.id == vital_sign_id,
                VitalSign.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_appointment_id(self, appointment_id: int) -> Optional[VitalSign]:
        """Get vital signs for an appointment."""
        result = await self.db.execute(
            select(VitalSign).where(
                VitalSign.appointment_id == appointment_id,
                VitalSign.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, appointment_id: int, data: VitalSignCreate, created_by: Optional[str] = None) -> VitalSign:
        """Create vital signs for an appointment."""
        vital_sign = VitalSign(
            appointment_id=appointment_id,
            blood_pressure_systolic=data.blood_pressure_systolic,
            blood_pressure_diastolic=data.blood_pressure_diastolic,
            heart_rate=data.heart_rate,
            temperature=data.temperature,
            respiratory_rate=data.respiratory_rate,
            weight=data.weight,
            height=data.height,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(vital_sign)
        await self.db.flush()
        await self.db.refresh(vital_sign)

        logger.info("Created vital signs id=%d appointment_id=%d", vital_sign.id, appointment_id)
        return vital_sign

    async def update(self, vital_sign_id: int, data: VitalSignUpdate, updated_by: Optional[str] = None) -> Optional[VitalSign]:
        """Update vital signs."""
        vital_sign = await self.get_by_id(vital_sign_id)
        if not vital_sign:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vital_sign, field, value)

        vital_sign.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(vital_sign)

        logger.info("Updated vital signs id=%d fields=%s", vital_sign_id, list(update_data.keys()))
        return vital_sign

    async def delete(self, vital_sign_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete vital signs."""
        vital_sign = await self.get_by_id(vital_sign_id)
        if not vital_sign:
            return False
        vital_sign.is_deleted = True
        vital_sign.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted vital signs id=%d", vital_sign_id)
        return True
