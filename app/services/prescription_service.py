import logging
from datetime import date, datetime, timezone
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prescription import Prescription
from app.models.enums import PrescriptionStatus
from app.schemas.prescription import PrescriptionCreate, PrescriptionUpdate

logger = logging.getLogger(__name__)


class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, prescription_id: UUID) -> Prescription | None:
        result = await self.db.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, prescription_number: str) -> Prescription | None:
        result = await self.db.execute(
            select(Prescription).where(
                Prescription.prescription_number == prescription_number
            )
        )
        return result.scalar_one_or_none()

    async def _generate_prescription_number(self) -> str:
        """Generate next prescription number in format RX-YYYY-NNNNNN"""
        import datetime as dt
        year = dt.datetime.now().year
        prefix = f"RX-{year}-"
        
        result = await self.db.execute(
            select(func.count(Prescription.id)).where(
                Prescription.prescription_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(6)}"

    async def list_prescriptions(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: UUID | None = None,
        doctor_id: UUID | None = None,
        status: PrescriptionStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Prescription], int]:
        logger.info(f"Listing prescriptions: page={page}, size={size}")
        query = select(Prescription)
        count_query = select(func.count(Prescription.id))

        if patient_id:
            query = query.where(Prescription.patient_id == patient_id)
            count_query = count_query.where(Prescription.patient_id == patient_id)

        if doctor_id:
            query = query.where(Prescription.doctor_id == doctor_id)
            count_query = count_query.where(Prescription.doctor_id == doctor_id)

        if status:
            query = query.where(Prescription.status == status)
            count_query = count_query.where(Prescription.status == status)

        if date_from:
            query = query.where(Prescription.prescription_date >= date_from)
            count_query = count_query.where(Prescription.prescription_date >= date_from)

        if date_to:
            query = query.where(Prescription.prescription_date <= date_to)
            count_query = count_query.where(Prescription.prescription_date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            Prescription.prescription_date.desc()
        )
        result = await self.db.execute(query)
        prescriptions = list(result.scalars().all())

        return prescriptions, total

    async def create(self, data: PrescriptionCreate, created_by: str) -> Prescription:
        logger.info(f"Creating prescription for patient: {data.patient_id}")
        prescription_number = await self._generate_prescription_number()
        prescription = Prescription(
            **data.model_dump(),
            prescription_number=prescription_number,
            status=PrescriptionStatus.pending,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(prescription)
        await self.db.commit()
        await self.db.refresh(prescription)
        logger.info(f"Created prescription: {prescription_number}")
        return prescription

    async def update(
        self, prescription: Prescription, data: PrescriptionUpdate, updated_by: str
    ) -> Prescription:
        logger.info(f"Updating prescription: {prescription.prescription_number}")
        update_data = data.model_dump(exclude_unset=True)
        
        # If status is being changed to dispensed, set dispensed_at
        if update_data.get("status") == PrescriptionStatus.dispensed:
            prescription.dispensed_at = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(prescription, field, value)
        prescription.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(prescription)
        return prescription

    async def delete(self, prescription: Prescription) -> None:
        logger.info(f"Deleting prescription: {prescription.prescription_number}")
        await self.db.delete(prescription)
        await self.db.commit()

