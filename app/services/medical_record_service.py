import logging
from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate

logger = logging.getLogger(__name__)


class MedicalRecordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, record_id: UUID) -> MedicalRecord | None:
        result = await self.db.execute(
            select(MedicalRecord).where(MedicalRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, record_number: str) -> MedicalRecord | None:
        result = await self.db.execute(
            select(MedicalRecord).where(MedicalRecord.record_number == record_number)
        )
        return result.scalar_one_or_none()

    async def _generate_record_number(self) -> str:
        """Generate next record number in format MR-YYYY-NNNNNN"""
        import datetime as dt
        year = dt.datetime.now().year
        prefix = f"MR-{year}-"
        
        result = await self.db.execute(
            select(func.count(MedicalRecord.id)).where(
                MedicalRecord.record_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(6)}"

    async def list_records(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: UUID | None = None,
        doctor_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[MedicalRecord], int]:
        logger.info(f"Listing medical records: page={page}, size={size}")
        query = select(MedicalRecord)
        count_query = select(func.count(MedicalRecord.id))

        if patient_id:
            query = query.where(MedicalRecord.patient_id == patient_id)
            count_query = count_query.where(MedicalRecord.patient_id == patient_id)

        if doctor_id:
            query = query.where(MedicalRecord.doctor_id == doctor_id)
            count_query = count_query.where(MedicalRecord.doctor_id == doctor_id)

        if date_from:
            query = query.where(MedicalRecord.visit_date >= date_from)
            count_query = count_query.where(MedicalRecord.visit_date >= date_from)

        if date_to:
            query = query.where(MedicalRecord.visit_date <= date_to)
            count_query = count_query.where(MedicalRecord.visit_date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(MedicalRecord.visit_date.desc())
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def create(self, data: MedicalRecordCreate, created_by: str) -> MedicalRecord:
        logger.info(f"Creating medical record for patient: {data.patient_id}")
        record_number = await self._generate_record_number()
        record = MedicalRecord(
            **data.model_dump(),
            record_number=record_number,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        logger.info(f"Created medical record: {record_number}")
        return record

    async def update(
        self, record: MedicalRecord, data: MedicalRecordUpdate, updated_by: str
    ) -> MedicalRecord:
        logger.info(f"Updating medical record: {record.record_number}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        record.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def delete(self, record: MedicalRecord) -> None:
        logger.info(f"Deleting medical record: {record.record_number}")
        await self.db.delete(record)
        await self.db.commit()

